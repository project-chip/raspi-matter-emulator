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
from refrigerator_service import refrigerator_service_pb2
import time


class RefrigeratorClient(DeviceClient):
    """
    Refrigerator client class for creating a device.
    """

    def __init__(self, socket_addr=None):
        """
        Initialize a Refrigerator client instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        """
        super().__init__(socket_addr)

    def GetRefrigerator(self):
        """
        Return Refrigerator state.
        """
        result = self.rpcs.chip.rpc.Refrigerator.GetRefrigerator()
        reply = json_format.MessageToDict(
            result[1], refrigerator_service_pb2.RefrigeratorState())
        return {'status': result[0].name, 'reply': reply}

    def SetRefrigerator(self, data):
        """
        Set Refrigerator state and return the result.

        Arguments:
            data {str} -- the Refrigerator state
        """
        arg = refrigerator_service_pb2.RefrigeratorState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Refrigerator.SetRefrigerator(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetColdCabinet(self):
        """
        Return cold cabinet value.
        """
        result = self.rpcs.chip.rpc.Refrigerator.GetColdCabinet()
        reply = json_format.MessageToDict(
            result[1], refrigerator_service_pb2.ColdCabinetState())
        return {'status': result[0].name, 'reply': reply}

    def SetColdCabinet(self, data):
        """
        Set Cold cabinet state and return the result.

        Arguments:
            data {str} -- the Cold cabinet value
        """
        arg = refrigerator_service_pb2.ColdCabinetState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Refrigerator.SetColdCabinet(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetFreezeCabinet(self):
        """
        Return Freeze cabinet value.
        """
        result = self.rpcs.chip.rpc.Refrigerator.GetFreezeCabinet()
        reply = json_format.MessageToDict(
            result[1], refrigerator_service_pb2.FreezeCabinetState())
        return {'status': result[0].name, 'reply': reply}

    def SetFreezeCabinet(self, data):
        """
        Set Freeze cabinet state and return the result.

        Arguments:
            data {str} -- the Freeze cabinet value
        """
        arg = refrigerator_service_pb2.FreezeCabinetState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.Refrigerator.SetFreezeCabinet(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}


if __name__ == '__main__':
    # This is the sample only
    client = RefrigeratorClient()
    print(client.GetFreezeCabinet())
    time.sleep()
