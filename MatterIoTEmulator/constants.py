# Copyright (c) 2024 LG Electronics, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


CONFIG_FILE = 'res/config/config.json'
CHIP_FACTORY_FILE = "chip_factory.ini"
TEMP_PATH = "/temp/"

LOG_PATH = "/log/"
NETWORK_INFO_FILENAME = "network_info.json"
IP_VERSION4 = "inet"
IP_VERSION4_PREFIXLEN = 24
IP_VERSION4_SCOPE = "global"
IP_VERSION6 = "inet6"
IP_VERSION6_PREFIXLEN = 64
IP_VERSION6_SCOPE = "link"
NUMBER_OF_FOLDER_LOG = 2

# Connect status's color
RED = "red"
YELLOW = "orange"
GREEN = "green"
BLACK = "black"

MAX_SERIAL_NUMBER = 9223372036854775807
MAX_VID = 65535
MAX_PID = 65535
MAX_PINCODE = 99999999
MAX_DISCRIMINATOR = 4095

# Input constraints
INVALID_PASSCODES = [
    00000000,
    11111111,
    22222222,
    33333333,
    44444444,
    55555555,
    66666666,
    77777777,
    88888888,
    99999999,
    12345678,
    87654321]
# Connect status
STT_DISCONNECTED = 0
STT_CREATE_IP = 10
STT_DEVICE_STARTING = 1
STT_DEVICE_STARTED = 2
STT_CONNECTING = 3
STT_CONNECTED = 4
STT_DEVICE_UNSUPPORTED = 5
STT_COMMISSIONING_FAIL = 6
STT_DAC_GENERATE_STARTING = 7
STT_DAC_GENERATE_FAIL = 8
STT_DAC_GENERATED = 9
STT_IP_GENERATE_STARTING = 10
STT_IP_GENERATED = 11
STT_IP_GENERATE_FAIL = 12
STT_DEVICE_DUPLICATE = 13
STT_COMMISSIONING_FAIL_BLUETOOTH = 14
STT_BIND_IP_FAIL_BACKEND = 15
STT_WAITING_RUNING_DEVICE = 16
STT_RPC_INIT_FAIL = 17
STT_RECOVER_FAIL = 18
# Connect flag
FLAG_DISCONNECTED = ""
FLAG_COMMISSIONING_FAIL = "Commissioning failed"
FLAG_DEVICE_STARTED = "CHIP:SVR: SetupQRCode:"
FLAG_CONNECTING = "Device completed Rendezvous process"
FLAG_CONNECTED = "GeneralCommissioning: Received CommissioningComplete"
FLAG_BLUETOOTH_FAIL = "Bluez notify CHIPoBluez connection disconnected"
FLAG_BIND_IP_FAIL = "VerifyOrDie failure"
FLAG_DEVICE_CONFIGURATION = "Device Configuration"
FLAG_RPC_INIT_DONE = "Starting pw_rpc server"

TEST_MODE = 1
NUMBER_STORAGE_FILE = 4
