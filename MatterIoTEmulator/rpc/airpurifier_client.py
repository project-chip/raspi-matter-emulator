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
from airpurifier_service import airpurifier_service_pb2
import time
import logging


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"
)


class AirPurifierClient(DeviceClient):
    """
    AirPurifier Client class for creating a device.
    """

    def __init__(self, socket_addr=None):
        """
        Initialize a AirPurifier client instance.

        Arguments:
            socket_addr {str} -- configuration about ip address and port
        """
        super().__init__(socket_addr)

    def GetAirPurifierSensor(self):
        """
        Return Air Purifier state.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetAirPurifierSensor()
        # logging.info(result)
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.AirPurifierState())
        return {'status': result[0].name, 'reply': reply}

    def SetAirPurifierSensor(self, data):
        """
        Set AirPurifier state and return the result.

        Arguments:
            data {str} -- the AirPurifier state
        """
        arg = airpurifier_service_pb2.AirPurifierState()
        json_format.ParseDict(data, arg)
        # logging.info(arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetAirPurifierSensor(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetTempValue(self):
        """
        Return measured value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetTempValue()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.TemperatureMeasurementAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetTempValue(self, data):
        """
        Set measured value and return the result.

        Arguments:
            data {str} -- the measured value
        """
        arg = airpurifier_service_pb2.TemperatureMeasurementAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetTempValue(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetHumidityValue(self):
        """
        Return humidity value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetHumidityValue()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.RelativeHumidityMeasurementAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetHumidityValue(self, data):
        """
        Set humidity value and return the result.

        Arguments:
            data {str} -- the humidity value
        """
        arg = airpurifier_service_pb2.RelativeHumidityMeasurementAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetHumidityValue(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetAirQuality(self):
        """
        Return AirQuality value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetAirQuality()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.AirQualityAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetAirQuality(self, data):
        """
        Set AirQuality value and return the result.

        Arguments:
            data {str} -- the AirQuality value
        """
        arg = airpurifier_service_pb2.AirQualityAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetAirQuality(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    def GetCondition(self):
        """
        Return AirCondition value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetCondition()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.HEPAFilterMonitoringAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetCondition(self, data):
        """
        Set AirCondition value and return the result.

        Arguments:
            data {str} -- the AirCondition value
        """
        arg = airpurifier_service_pb2.HEPAFilterMonitoringAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetCondition(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}

    # PM25
    def GetPM25(self):
        """
        Return PM25 value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetPM25()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.PM25ConcentrationMeasurementAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetPM25(self, data):
        """
        Set PM25 value and return the result.

        Arguments:
            data {str} -- the PM25 value
        """
        arg = airpurifier_service_pb2.PM25ConcentrationMeasurementAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetPM25(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}
    
    # Thermostat
    def GetThermostat(self):
        """
        Return Thermostat value.
        """
        result = self.rpcs.chip.rpc.AirPurifier.GetThermostat()
        reply = json_format.MessageToDict(
            result[1], airpurifier_service_pb2.ThermostatAirPurifier())
        return {'status': result[0].name, 'reply': reply}

    def SetThermostat(self, data):
        """
        Set Thermostat value and return the result.

        Arguments:
            data {str} -- the Thermostat value
        """
        arg = airpurifier_service_pb2.ThermostatAirPurifier()
        json_format.ParseDict(data, arg)
        result = self.rpcs.chip.rpc.AirPurifier.SetThermostat(arg)
        reply = json_format.MessageToDict(result[1])
        return {'status': result[0].name, 'reply': reply}


if __name__ == '__main__':
    # This is the sample only
    client = AirPurifierClient()
    time.sleep()
