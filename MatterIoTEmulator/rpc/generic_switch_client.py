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
from generic_switch_service import generic_switch_service_pb2
import time


class GenericSwitchClient(DeviceClient):
    """
    GenericSwitch client class for creating a device.
    """

    def __init__(self, socket_addr=None):
        """
        Initialize a GenericSwitch client instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        """
        super().__init__(socket_addr)

    def get(self):
        """
        Return GenericSwitch state.
        """
        result = self.rpcs.chip.rpc.GenericSwitchService.Get()
        reply = json_format.MessageToDict(
            result[1], generic_switch_service_pb2.GenericSwitchState())
        return {'status': result[0].name, 'reply': reply}

    def set(self, data):
        """
        Set GenericSwitch state and return the result.

        Arguments:
            data {str} -- the GenericSwitch state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.Set(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnSwitchLatch(self, data):
        """
        Set GenericSwitch latch and return the result.

        Arguments:
            data {str} -- the GenericSwitch latch state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnSwitchLatch(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnInitialPress(self, data):
        """
        Set GenericSwitch initial press and return the result.

        Arguments:
            data {str} -- the GenericSwitch initial press state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnInitialPress(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnLongPress(self, data):
        """
        Set GenericSwitch long state and return the result.

        Arguments:
            data {str} -- the GenericSwitch long press state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnLongPress(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnShortRelease(self, data):
        """
        Set GenericSwitch short release state and return the result.

        Arguments:
            data {str} -- the GenericSwitch short release state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnShortRelease(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnLongRelease(self, data):
        """
        Set GenericSwitch long release state and return the result.

        Arguments:
            data {str} -- the GenericSwitch long release state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnLongRelease(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnMultiPressOngoing(self, data):
        """
        Set GenericSwitch multi press ongoing state and return the result.

        Arguments:
            data {str} -- the GenericSwitch multi press ongoing state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnMultiPressOngoing(
            arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def OnMultiPressComplete(self, data):
        """
        Set GenericSwitch multi press complete state and return the result.

        Arguments:
            data {str} -- the GenericSwitch multi press complete state
        """
        arg = generic_switch_service_pb2.GenericSwitchState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.GenericSwitchService.OnMultiPressComplete(
            arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}


if __name__ == '__main__':
    # This is the sample only
    client = GenericSwitchClient()
    print(client.get())
    time.sleep(1)
