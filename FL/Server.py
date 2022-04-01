import time

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import threading
import tqdm
import numpy as np

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import sys

sys.path.append('../')
from Communicator import *
import Utils
import Config

np.random.seed(0)
torch.manual_seed(0)


class Server(Communicator):
    def __init__(self, index, ip_address, server_port):
        """

        :param index:
        :param ip_address:
        :param server_port:
        """
        super(Server, self).__init__(index, ip_address, ip_address, server_port, pub_topic="fedserver",
                                     sub_topic='fedbench', client_num=Config.K)
        self.criterion = None
        self.optimizers = None
        self.nets = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.port = server_port

        logger.info("Waiting For Incoming Connections.")
        if Config.COMM == 'TCP':
            self.sock.bind((self.ip, self.port))
            self.client_socks = {}

            while len(self.client_socks) < Config.K:
                self.sock.listen(5)
                (client_sock, (ip, port)) = self.sock.accept()
                logger.info('Got connection from ' + str(ip))
                self.client_socks[str(ip)] = client_sock
        elif Config.COMM == 'MQTT' or Config.COMM == 'AMQP':
            connections = 0
            while connections < Config.K:
                connections += int(self.q.get())

            logger.info("Clients have connected")

        self.uninet = Utils.get_model('Unit', Config.model_name, Config.model_len - 1, self.device, Config.model_cfg)

        self.transform_test = transforms.Compose(
            [transforms.ToTensor(), transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
             ])
        self.testset = torchvision.datasets.CIFAR10(root=Config.dataset_path, train=False, download=False,
                                                    transform=self.transform_test)
        self.testloader = torch.utils.data.DataLoader(self.testset, batch_size=100, shuffle=False, num_workers=4)

    def initialize(self, first):
        """

        :param first:
        """
        if first:
            self.nets = {}
            self.optimizers = {}
            for i in range(len(Config.split_layer)):
                client_ip = Config.CLIENTS_LIST[i]
                self.nets[client_ip] = Utils.get_model('Server', Config.model_name, Config.split_layer[i], self.device,
                                                       Config.model_cfg)
            self.criterion = nn.CrossEntropyLoss()

        msg = ['MSG_INITIAL_GLOBAL_WEIGHTS_SERVER_TO_CLIENT', self.uninet.state_dict()]
        if Config.COMM == 'TCP':
            for i in self.client_socks:
                self.snd_msg_tcp(self.client_socks[i], msg)
        else:
            self.send_msg(msg)

    def train(self):
        """

        :return:
        """
        # Training start

        ttpi = {}  # Training time per iteration
        if Config.COMM == 'TCP':
            for s in self.client_socks:
                msg = self.recv_msg(self.client_socks[s], 'MSG_TRAINING_TIME_PER_ITERATION')
                ttpi[msg[1]] = msg[2]
        else:
            connections = 0
            while connections != Config.K:
                msg = self.q.get()
                while msg[0] != 'MSG_TRAINING_TIME_PER_ITERATION':
                    self.q.put(msg)
                    msg = self.q.get()
                connections += 1
                ttpi[msg[1]] = msg[2]
        return ttpi

    def aggregate(self, client_ips):
        """

        :param client_ips:
        """
        w_local_list = []
        for i in range(len(client_ips)):
            msg = None
            if Config.COMM == 'TCP':
                msg = self.recv_msg(self.client_socks[client_ips[i]], 'MSG_LOCAL_WEIGHTS_CLIENT_TO_SERVER')
            else:
                while msg is None:
                    msg = self.q.get()
            w_local = (msg[1], Config.N / Config.K)
            w_local_list.append(w_local)
        zero_model = Utils.zero_init(self.uninet).state_dict()
        aggregated_model = Utils.fed_avg(zero_model, w_local_list, Config.N)

        self.uninet.load_state_dict(aggregated_model)

    def test(self):
        """

        :return:
        """
        self.uninet.eval()
        test_loss = 0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_idx, (inputs, targets) in enumerate(tqdm.tqdm(self.testloader)):
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.uninet(inputs)
                loss = self.criterion(outputs, targets)

                test_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        acc = 100. * correct / total
        logger.info('Test Accuracy: {}'.format(acc))

        # Save checkpoint.
        torch.save(self.uninet.state_dict(), './' + Config.model_name + '.pth')

        return acc

    def reinitialize(self, first):
        """

        :param first:
        """
        self.initialize(first)

    def finish(self, client_ips):
        """

        :param client_ips:
        :return:
        """
        msg = []
        if Config.COMM == 'TCP':
            for i in range(len(client_ips)):
                msg.append(self.recv_msg(self.client_socks[client_ips[i]], 'MSG_COMMUNICATION_TIME')[1])
        else:
            connections = 0
            while connections != Config.K:
                msg.append(self.q.get()[1])
                connections += 1
            self.send_msg(['DONE'])
        return max(msg)