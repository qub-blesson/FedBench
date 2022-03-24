import sys

# Communication config
COMM = 'TCP'

# Network configration
SERVER_ADDR = '192.168.101.120'
SERVER_PORT = 1883

K = 4  # Number of devices

# Unique clients order
HOST2IP = {'mars116XU': '192.168.101.116', 'mars117XU': '192.168.101.217', 'mars118XU': '192.168.101.218',
           'mars119XU': '192.168.101.219'}
CLIENTS_CONFIG = {'192.168.101.116': 0, '192.168.101.217': 1, '192.168.101.218': 2, '192.168.101.219': 3}
CLIENTS_LIST = ['192.168.101.116', '192.168.101.217', '192.168.101.218', '192.168.101.219']

# Dataset configration
dataset_name = 'CIFAR10'
home = sys.path[0].split('FedAdapt')[0] + 'FedAdapt'
dataset_path = "../datasets/CIFAR10/"
N = 50000  # data length

# train communication time
comm_time = 0.0

model_cfg = {
    # (Type, in_channels, out_channels, kernel_size, out_size(c_out*h*w), flops(c_out*h*w*k*k*c_in))
    'VGG5': [('C', 3, 32, 3, 32 * 32 * 32, 32 * 32 * 32 * 3 * 3 * 3), ('M', 32, 32, 2, 32 * 16 * 16, 0),
             ('C', 32, 64, 3, 64 * 16 * 16, 64 * 16 * 16 * 3 * 3 * 32), ('M', 64, 64, 2, 64 * 8 * 8, 0),
             ('C', 64, 64, 3, 64 * 8 * 8, 64 * 8 * 8 * 3 * 3 * 64),
             ('D', 8 * 8 * 64, 128, 1, 64, 128 * 8 * 8 * 64),
             ('D', 128, 10, 1, 10, 128 * 10)],
    'VGG8': [('C', 3, 32, 3, 32 * 32 * 32, 32 * 32 * 32 * 3 * 3 * 3),
             ('C', 32, 32, 3, 32 * 32 * 32, 32 * 32 * 32 * 3 * 3 * 32),
             ('M', 32, 32, 2, 32 * 16 * 16, 0),
             ('C', 32, 64, 3, 64 * 16 * 16, 64 * 16 * 16 * 3 * 3 * 32),
             ('C', 64, 64, 3, 64 * 16 * 16, 64 * 16 * 16 * 3 * 3 * 64),
             ('M', 64, 64, 2, 64 * 8 * 8, 0),
             ('C', 64, 128, 3, 128 * 8 * 8, 128 * 8 * 8 * 3 * 3 * 64),
             ('C', 128, 128, 3, 128 * 8 * 8, 128 * 8 * 8 * 3 * 3 * 128),
             ('D', 8 * 8 * 128, 128, 1, 128, 128 * 8 * 8 * 128),
             ('D', 128, 10, 1, 10, 128 * 10)]
}
model_name = 'VGG8'
split_layer = [9, 9, 9, 9]  # Initial split layers
model_len = 10

# FL training configuration
R = 5  # FL rounds
LR = 0.01  # Learning rate
B = 100  # Batch size

random = True
random_seed = 0
