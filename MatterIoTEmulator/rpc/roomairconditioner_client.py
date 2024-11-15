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
from roomairconditioner_service import roomairconditioner_service_pb2
import time
import logging


class RoomAirConditionerClient(DeviceClient):
    """
    Room Air Conditioner client class for creating a device.
    """

    def __init__(self, socket_addr=None):
        """
        Initialize a Room Air Conditioner client instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        """
        super().__init__(socket_addr)

    def GetTempValue(self):
        """
        Return Measured value.
        """
        result = self.rpcs.chip.rpc.RoomAirConditioner.GetTempValue()
        reply = json_format.MessageToDict(
            result[1], roomairconditioner_service_pb2.TemperatureSensorRoomAir())
        return {'status': result[0].name, 'reply': reply}

    def SetTempValue(self, data):
        """
        Set Measured state and return the result.

        Arguments:
            data {str} -- the Measured state
        """
        arg = roomairconditioner_service_pb2.TemperatureSensorRoomAir()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.RoomAirConditioner.SetTempValue(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetHumiditySensorValue(self):
        """
        Return Humidity sensor state.
        """
        result = self.rpcs.chip.rpc.RoomAirConditioner.GetHumiditySensorValue()
        reply = json_format.MessageToDict(
            result[1], roomairconditioner_service_pb2.HumiditySensorRoomAir())
        return {'status': result[0].name, 'reply': reply}

    def SetHumiditySensorValue(self, data):
        """
        Set Humidity sensor value and return the result.

        Arguments:
            data {str} -- the Humidity sensor value
        """
        arg = roomairconditioner_service_pb2.HumiditySensorRoomAir()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.RoomAirConditioner.SetHumiditySensorValue(
            arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetRoomAirConditionerSensor(self):
        """
        Return Room Air Conditioner sensor state.
        """
        result = self.rpcs.chip.rpc.RoomAirConditioner.GetRoomAirConditionerSensor()
        reply = json_format.MessageToDict(
            result[1], roomairconditioner_service_pb2.RoomAirConditionerState())
        return {'status': result[0].name, 'reply': reply}

    def SetRoomAirConditionerSensor(self, data):
        """
        Set Room Air Conditioner state and return the result.

        Arguments:
            data {str} -- the Room Air Conditioner sensor state
        """
        arg = roomairconditioner_service_pb2.RoomAirConditionerState()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.RoomAirConditioner.SetRoomAirConditionerSensor(
            arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}


if __name__ == '__main__':
    # This is the sample only
    client = RoomAirConditionerClient()
    time.sleep()
