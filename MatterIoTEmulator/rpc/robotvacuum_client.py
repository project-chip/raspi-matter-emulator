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


from rpc.device_client import DeviceClient
from google.protobuf import json_format
from rvc_service import rvc_service_pb2
import time


class RobotVacuumClient(DeviceClient):
    """
    RobotVacuum client class for creating a device.
    """

    def __init__(self, socket_addr=None):
        """
        Initialize a RobotVacuum client instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        """
        super().__init__(socket_addr)

    def get(self):
        """
        Return RobotVacuum state.
        """
        result = self.rpcs.chip.rpc.RVCService.Get()
        reply = json_format.MessageToDict(
            result[1], rvc_service_pb2.RVCState())
        return {'status': result[0].name, 'reply': reply}

    def set(self, data):
        """
        Set RobotVacuum state and return the result.

        Arguments:
            data {str} -- the RobotVacuum state
        """
        arg = rvc_service_pb2.RVCState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.RVCService.Set(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def HandleClearErrorMessage(self):
        """
        Handle Clear Error message.
        """
        self.rpcs.chip.rpc.RVCService.HandleClearErrorMessage()

    def HandleChargedMessage(self):
        """
        Handle Charged message.
        """
        self.rpcs.chip.rpc.RVCService.HandleChargedMessage()

    def HandleChargingMessage(self):
        """
        Handle Charging message.
        """
        self.rpcs.chip.rpc.RVCService.HandleChargingMessage()

    def HandleDockedMessage(self):
        """
        Handle Docked message.
        """
        self.rpcs.chip.rpc.RVCService.HandleDockedMessage()

    def HandleChargerFoundMessage(self):
        """
        Handle Charger message.
        """
        self.rpcs.chip.rpc.RVCService.HandleChargerFoundMessage()

    def HandleLowChargeMessage(self):
        """
        Handle Low Charge message.
        """
        self.rpcs.chip.rpc.RVCService.HandleLowChargeMessage()

    def HandleActivityCompleteEvent(self):
        """
        Handle Activity Complete event.
        """
        self.rpcs.chip.rpc.RVCService.HandleActivityCompleteEvent()


if __name__ == '__main__':
    # This is the sample only
    client = RobotVacuumClient()
    time.sleep(1)
    print(client.get())
    time.sleep(1)
    print(client.get())
