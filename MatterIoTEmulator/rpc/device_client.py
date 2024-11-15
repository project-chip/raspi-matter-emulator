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


import logging
import re
import socket
import sys
from typing import Any, BinaryIO, Collection

from pw_hdlc.rpc import HdlcRpcClient, default_channels
from pw_rpc import callback_client

from pw_tokenizer.detokenize import Detokenizer
from pw_tokenizer import tokens
from ui.ui_matter import Ui_Matter
# Protos
from attributes_service import attributes_service_pb2
from button_service import button_service_pb2
from descriptor_service import descriptor_service_pb2
from device_service import device_service_pb2
from echo_service import echo_pb2
from lighting_service import lighting_service_pb2
from locking_service import locking_service_pb2
from ot_cli_service import ot_cli_service_pb2
from thread_service import thread_service_pb2
from wifi_service import wifi_service_pb2
from pump_service import pump_service_pb2
from plug_service import plug_service_pb2
from sensor_service import sensor_service_pb2
from google.protobuf import json_format
from window_service import window_service_pb2
from lock_service import lock_service_pb2
from fan_service import fan_service_pb2
from hvac_service import hvac_service_pb2
from thermostat_service import thermostat_service_pb2
from airpurifier_service import airpurifier_service_pb2
from airqualitysensor_service import airqualitysensor_service_pb2
from dishwasher_service import dishwasher_service_pb2
from laundrywasher_service import laundrywasher_service_pb2
from roomairconditioner_service import roomairconditioner_service_pb2
from refrigerator_service import refrigerator_service_pb2
from smokecoalarm_service import smokecoalarm_service_pb2
from rvc_service import rvc_service_pb2
from generic_switch_service import generic_switch_service_pb2

_LOG = logging.getLogger(__name__)
_DEVICE_LOG = logging.getLogger('rpc_device')

PW_RPC_MAX_PACKET_SIZE = 256
SOCKET_SERVER = 'localhost'
SOCKET_PORT = 33000

PROTOS = [attributes_service_pb2,
          button_service_pb2,
          descriptor_service_pb2,
          device_service_pb2,
          echo_pb2,
          lighting_service_pb2,
          pump_service_pb2,
          locking_service_pb2,
          ot_cli_service_pb2,
          thread_service_pb2,
          plug_service_pb2,
          sensor_service_pb2,
          window_service_pb2,
          wifi_service_pb2,
          lock_service_pb2,
          fan_service_pb2,
          hvac_service_pb2,
          thermostat_service_pb2,
          airpurifier_service_pb2,
          airqualitysensor_service_pb2,
          dishwasher_service_pb2,
          laundrywasher_service_pb2,
          roomairconditioner_service_pb2,
          refrigerator_service_pb2,
          smokecoalarm_service_pb2,
          rvc_service_pb2,
          generic_switch_service_pb2]


class SocketClientImpl:
    """
    SocketClientImpl class for creating common socket.
    """

    def __init__(self, config: str):
        """
        Initialize a SocketClientImpl instance.

        Arguments:
            config {str} -- configuration about ip address and port
        Raises:
            Exception: if socket creation has an error
        """
        try:
            # self.ui = Ui_Matter()
            # SOCKET_PORT = self.ui.txt_productid.text()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_server = ''
            socket_port = 0

            if config == 'default':
                socket_server = SOCKET_SERVER
                socket_port = SOCKET_PORT
            else:
                socket_server, socket_port_str = config.split(':')
                socket_port = int(socket_port_str)
            self.socket.connect((socket_server, socket_port))
        except Exception as e:
            logging.error("Failed to initial RPC: " + str(e))

    def write(self, data: bytes):
        """
        Send data to network via a socket connection.

        Arguments:
            data {[byte]} -- the number of bytes need to write
        """
        self.socket.sendall(data)

    def read(self, num_bytes: int = PW_RPC_MAX_PACKET_SIZE):
        """
        Return the numbers of bytes read from network via a socket connection.

        Arguments:
            num_bytes {int} -- the number of bytes to be read (default 256)
        """
        return self.socket.recv(num_bytes)


def write_to_output(data: bytes,
                    unused_output: BinaryIO = sys.stdout.buffer,
                    detokenizer=None):
    """
    Write data to buffer.

    Arguments:
        num_bytes {int} -- the number of bytes to be send
        unused_output {BinaryIO} -- sending buffer (default sys.stdout.buffer)
        detokenizer {Detokenizer} -- decodes and detokenizes binary messages
    """
    pass


class DeviceClient():
    """
    DeviceClient class for creating a device.
    """

    def __init__(self, socket_addr=None) -> None:
        """
        Initialize a DeviceClient instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        Raises:
            Exception: if socket creation has an error
        """
        try:
            if not socket_addr:
                socket_addr = 'default'
            output = sys.stdout.buffer
            try:
                self.socket_device = SocketClientImpl(socket_addr)
                read = self.socket_device.read
                write = self.socket_device.write
            except ValueError:
                _LOG.exception(
                    'Failed to initialize socket at %s',
                    socket_addr)
                return 1
            token_databases = None
            detokenizer = Detokenizer(
                tokens.Database.merged(
                    *token_databases),
                show_errors=False) if token_databases else None

            callback_client_impl = callback_client.Impl(
                default_unary_timeout_s=10.0,
                default_stream_timeout_s=None,
            )
            self._client = HdlcRpcClient(read, PROTOS, default_channels(write),
                                         lambda data: write_to_output(
                                             data, output, detokenizer),
                                         client_impl=callback_client_impl)
            self._rpcs = self._client.client.channel(1).rpcs
        except Exception as e:
            logging.error("Failed to initial RPC: " + str(e))

    @property
    def rpcs(self):
        """
        Return a reference to a rpc socket.
        """
        return self._rpcs

    def stop(self):
        """
        Close a rpc client socket.
        """
        if (self._client is not None):
            self._client.close()
            del self._client
            self.socket_device.socket.close()

    def factory_reset(self):
        """
        Factory reset device and return the result.
        """
        result = self._rpcs.chip.rpc.Device.FactoryReset()
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def reboot(self):
        """
        Reboot device and return the result.
        """
        result = self._rpcs.chip.rpc.Device.Reboot()
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def trigger_ota(self):
        """
        Return current device information.
        """
        result = self._rpcs.chip.rpc.Device.TriggerOta()
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def set_ota_metadata_for_provider(self, data):
        """
        Set OTA metadata information and return the result.
        """
        arg = device_service_pb2.MetadataForProvider()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Device.SetOtaMetadataForProvider(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def get_device_info(self):
        """
        Return current device information.
        """
        result = self._rpcs.chip.rpc.Device.GetDeviceInfo()
        reply = json_format.MessageToDict(
            result[1], device_service_pb2.DeviceInfo())
        return {'status': result[0].name, 'reply': reply}

    def get_device_state(self):
        """
        Return current device state.
        """
        result = self._rpcs.chip.rpc.Device.GetDeviceState()
        reply = json_format.MessageToDict(
            result[1], device_service_pb2.DeviceState())
        return {'status': result[0].name, 'reply': reply}

    def set_pairing_state(self, data):
        """
        Set pairing state of a device and return the result.

        Arguments:
            data {str} -- pairing state
        """
        arg = device_service_pb2.PairingState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Device.SetPairingState(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def get_pairing_state(self):
        """
        Return current pairing state of a device.
        """
        result = self._rpcs.chip.rpc.Device.GetPairingState()
        reply = json_format.MessageToDict(
            result[1], device_service_pb2.PairingState())
        return {'status': result[0].name, 'reply': reply}

    def set_pairing_info(self, data):
        """
        Set pairing infomation and return the result.

        Arguments:
            data {str} -- pairing information
        """
        arg = device_service_pb2.PairingInfo()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Device.SetPairingInfo(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def get_spake_info(self):
        """
        Return spake infomation.
        """
        result = self._rpcs.chip.rpc.Device.GetSpakeInfo()
        reply = json_format.MessageToDict(
            result[1], device_service_pb2.SpakeInfo())
        return {'status': result[0].name, 'reply': reply}

    def set_spake_info(self, data):
        """
        Set spake infomation and return the result.

        Arguments:
            data {str} -- spake information
        """
        arg = device_service_pb2.SpakeInfo()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Device.SetSpakeInfo(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}
