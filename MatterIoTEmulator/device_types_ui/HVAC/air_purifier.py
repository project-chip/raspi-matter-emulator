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


from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from qtwidgets import Toggle
import logging
import threading
import os
import time
import random

from rpc.airpurifier_client import AirPurifierClient
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/HVAC/")


OFF_MODE = 0
LOW_MODE = 1
MEDIUM_MODE = 2
HIGH_MODE = 3
ON_MODE = 4
AUTO_MODE = 5
SMART_MODE = 6


AIR_UNKNOWN = 0
AIR_GOOD = 1
AIR_FAIR = 2
AIR_MODERATE = 3
AIR_POOR = 4
AIR_VERYPOOR = 5
AIR_EXTREMELY = 6


MULTI_SPEED = 0
AUTO = 1
ROCKING = 2
WIND = 3
STEP = 4
AIR_FLOW_DIRECTION = 5
ALL_FEATURE = 6

ROCK_LEFT_RIGHT = 1
ROCK_UP_DOWN = 2
ROCK_ROUND = 4

SLEEP_WIND = 1
NATURAL_WIND = 2

FORWARD = 0
REVERSE = 1


class AirPurifier(BaseDeviceUI):
    """
    AirPurifier device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `AirPurifier` UI.
        :param parent: An UI object load AirPurifier device UI controller.
        """
        super().__init__(parent)

        self.fan_mode = 0
        self.fan_mode_sequence = 2
        self.support_rock_mode = True
        self.rock_mode = 0
        self.support_wind_mode = True
        self.wind_mode = 0
        self.air_flow = 0  
        self.percent_setting = 100
        self.speed_setting = 80  
        self.cr_feature_type = ALL_FEATURE
        self.cr_value_carbon = 99

        self.air_quality = 0
        self.temperature = 0
        self.humidity = 0
        self.condition_filter = 0
        self.pm25 = 0
        self.enable_update = True
        self.is_edit_temp = True
        self.is_edit_hum = True
        self.is_edit_pm25 = True
        self.is_edit_con = True
        self.is_edit_carbon = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'air-purifier.png')
        self.lbl_main_icon.setFixedSize(80, 80)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # Air quality status
        self.lbl_air_status = QLabel()
        self.lbl_air_status.setText("Air Quality:")
        self.lbl_air_status.setAlignment(Qt.AlignCenter)

        self.bt_air = QPushButton()
        self.bt_air.setMaximumSize(QSize(120, 20))
        self.bt_air.setEnabled(False)

        self.grid_layout = QHBoxLayout()
        self.grid_layout.addWidget(
            self.lbl_air_status,
            alignment=Qt.AlignRight)
        self.grid_layout.addWidget(self.bt_air, alignment=Qt.AlignLeft)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        # Local Temperature
        self.lbl_tem_status = QLabel()
        self.lbl_tem_status.setText('Local Temperature:')
        self.lbl_tem_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_tem_status)

        self.line_edit_temp = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_temp.setValidator(self.validator)
        self.line_edit_temp.setValidator(self.double_validator)
        self.line_edit_temp.setMaximumSize(QSize(65, 20))
        self.lbl_measure = QLabel()
        self.lbl_measure.setText('°C')
        self.grid_layout_temp = QHBoxLayout()
        self.grid_layout_temp.setAlignment(Qt.AlignCenter)
        self.grid_layout_temp.addWidget(
            self.lbl_tem_status, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.line_edit_temp, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_temp.textEdited.connect(self.on_text_edited_temp)
        self.line_edit_temp.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_temp)

        # Local Humidity
        self.lbl_hum_status = QLabel()
        self.lbl_hum_status.setText('Local Humidity:')
        self.lbl_hum_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_hum_status)

        self.line_edit_hum = QLineEdit()
        self.line_edit_hum.setValidator(self.validator)
        self.line_edit_hum.setValidator(self.double_validator)
        self.line_edit_hum.setMaximumSize(QSize(65, 20))
        self.lbl_measure_hum = QLabel()
        self.lbl_measure_hum.setText('%')
        self.grid_layout_hum = QHBoxLayout()
        self.grid_layout_hum.setAlignment(Qt.AlignCenter)
        self.grid_layout_hum.addWidget(
            self.lbl_hum_status, alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.line_edit_hum, alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.lbl_measure_hum, alignment=Qt.AlignRight)

        self.line_edit_hum.textEdited.connect(self.on_text_edited_hum)
        self.line_edit_hum.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_hum)

        # PM2.5 Concentration
        self.lbl_concentration_status = QLabel()
        self.lbl_concentration_status.setText('PM2.5 Concentration :')
        self.lbl_concentration_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_concentration_status)

        self.line_edit_pm25 = QLineEdit()
        self.line_edit_pm25.setValidator(self.validator)
        self.line_edit_pm25.setValidator(self.double_validator)
        self.line_edit_pm25.setMaximumSize(QSize(65, 20))
        self.lbl_measure_pm25 = QLabel()
        self.lbl_measure_pm25.setText('PPM')
        self.grid_layout_pm25 = QHBoxLayout()
        self.grid_layout_pm25.setAlignment(Qt.AlignCenter)
        self.grid_layout_pm25.addWidget(
            self.lbl_concentration_status,
            alignment=Qt.AlignRight)
        self.grid_layout_pm25.addWidget(
            self.line_edit_pm25, alignment=Qt.AlignRight)
        self.grid_layout_pm25.addWidget(
            self.lbl_measure_pm25, alignment=Qt.AlignRight)

        self.line_edit_pm25.textEdited.connect(self.on_text_edited_pm25)
        self.line_edit_pm25.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_pm25)

        # Filter Condition Status
        self.lbl_core_status = QLabel()
        self.lbl_core_status.setText('Filter Condition Status:')
        self.lbl_core_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_core_status)

        self.line_edit_con = QLineEdit()
        self.line_edit_con.setValidator(self.validator)
        self.line_edit_con.setValidator(self.double_validator)
        self.line_edit_con.setMaximumSize(QSize(65, 20))
        self.lbl_measure_con = QLabel()
        self.lbl_measure_con.setText('%')
        self.grid_layout_con = QHBoxLayout()
        self.grid_layout_con.setAlignment(Qt.AlignCenter)
        self.grid_layout_con.addWidget(
            self.lbl_core_status, alignment=Qt.AlignRight)
        self.grid_layout_con.addWidget(
            self.line_edit_con, alignment=Qt.AlignRight)
        self.grid_layout_con.addWidget(
            self.lbl_measure_con, alignment=Qt.AlignRight)

        self.line_edit_con.textEdited.connect(
            self.on_text_edited_hepa_filter_condition)
        self.line_edit_con.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_con)

        # Activated CarbonFilter Monitoring
        self.lbl_carbon_status = QLabel()
        self.lbl_carbon_status.setText('Filter Activated Carbon:')
        self.lbl_carbon_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_carbon_status)

        self.line_edit_carbon = QLineEdit()
        self.line_edit_carbon.setValidator(self.validator)
        self.line_edit_carbon.setValidator(self.double_validator)
        self.line_edit_carbon.setMaximumSize(QSize(65, 20))
        self.lbl_measure_carbon = QLabel()
        self.lbl_measure_carbon.setText('%')
        self.grid_layout_carbon = QHBoxLayout()
        self.grid_layout_carbon.setAlignment(Qt.AlignCenter)
        self.grid_layout_carbon.addWidget(
            self.lbl_carbon_status, alignment=Qt.AlignRight)
        self.grid_layout_carbon.addWidget(
            self.line_edit_carbon, alignment=Qt.AlignRight)
        self.grid_layout_carbon.addWidget(
            self.lbl_measure_carbon, alignment=Qt.AlignRight)

        self.line_edit_carbon.textEdited.connect(
            self.on_text_edited_cacbon_filter_condition)
        self.line_edit_carbon.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_carbon)

        # Fan feature mode
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_feature = QLabel()
        self.lbl_feature.setText('Fan Feature')
        self.parent.ui.lo_controller.addWidget(self.lbl_feature)

        fan_feature_list = [
            "MultiSpeed",
            "Auto",
            "Rocking",
            "Wind",
            "Step",
            "AirflowDirection",
            "AllFeature"]
        self.fan_feature_box = QComboBox()
        self.fan_feature_box.addItems(fan_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.fan_feature_box.currentIndexChanged.connect(
            self.fan_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.fan_feature_box)

        # Show fan mode
        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('Fan Mode : ')
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        # Create a fan control mode
        fan_mode_list = ["OFF", "LOW", "MEDIUM", "HIGH", "ON", "AUTO", "SMART"]
        self.fan_control_box = QComboBox()
        self.fan_control_box.addItems(fan_mode_list)
        self.fan_control_box.model().item(ON_MODE).setEnabled(False)
        self.fan_control_box.model().item(SMART_MODE).setEnabled(False)

        # Connect the currentIndexChanged signal to a slot
        self.fan_control_box.currentIndexChanged.connect(
            self.handle_fan_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.fan_control_box)

        # Init rpc
        self.client = AirPurifierClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()
        logging.debug("Init Fan done")

    def on_text_edited_temp(self):
        """Enable 'is_edit_temp' attribute when line edit temperature is editting"""
        self.is_edit_temp = False

    def on_text_edited_hum(self):
        """Enable 'is_edit_hum' attribute when line edit humidity is editting"""
        self.is_edit_hum = False

    def on_text_edited_pm25(self):
        """Enable 'is_edit_pm25' attribute when line edit pm25 is editting"""
        self.is_edit_pm25 = False

    def on_text_edited_hepa_filter_condition(self):
        """Enable 'is_edit_con' attribute when line edit hepa filter is editting"""
        self.is_edit_con = False

    def on_text_edited_cacbon_filter_condition(self):
        """Enable 'is_edit_carbon' attribute when line edit cacbon filter is editting"""
        self.is_edit_carbon = False

    def get_air_purifier_data(self, fan_feature_type = None, fan_data = None):
        data = {'featureMapFanControl': {'featureMap': fan_feature_type if fan_feature_type is not None else self.cr_feature_type},
                'activatedCarbonFilterMonitoring': {'condition': self.cr_value_carbon}
                }
        if fan_data is not None:
            data.update(fan_data)
        return data

    def on_return_pressed(self):
        """
        Handle set temperature measurement or
        humidity measurement or
        pm25 measurement or
        hepa filter condition or
        active cacbon filter condition or
        when set from line edit
        """
        try:
            value_temp = round(float(self.line_edit_temp.text()) * 100)
            value_hum = round(float(self.line_edit_hum.text()) * 100)
            value_pm25 = round(float(self.line_edit_pm25.text()), 2)
            hepa_filter_condition = round(float(self.line_edit_con.text()))
            cacbon_filter_condition = round(
                float(self.line_edit_carbon.text()))

            if 0 <= value_temp <= 10000:
                data_tem = {'measuredValue': value_temp}
                self.client.SetTempValue(data_tem)
                self.is_edit_temp = True
            else:
                self.message_box(ER_TEMP)
                self.line_edit_temp.setText(str(self.temperature))

            if 0 <= value_hum <= 10000:
                data_humidity = {'measuredValue': value_hum}
                self.client.SetHumidityValue(data_humidity)
                self.is_edit_hum = True
            else:
                self.message_box(ER_HUM)
                self.line_edit_hum.setText(str(self.humidity))

            if 0 <= hepa_filter_condition <= 100:
                data_condition = {'condition': hepa_filter_condition}
                self.client.SetCondition(data_condition)
                self.is_edit_con = True
            else:
                self.message_box(ER_CON)
                self.line_edit_con.setText(str(self.condition_filter))

            if 0 <= cacbon_filter_condition <= 100:
                self.cr_value_carbon = cacbon_filter_condition                
                self.client.SetAirPurifierSensor(self.get_air_purifier_data())
                self.is_edit_carbon = True
            else:
                self.message_box(ER_CARBON)
                self.line_edit_carbon.setText(str(self.cr_value_carbon))

            if 0 <= value_pm25 <= 300:
                data_PM25 = {'measuredValue': value_pm25}
                self.client.SetPM25(data_PM25)
                self.is_edit_pm25 = True
            else:
                self.message_box(ER_PM25)
                self.line_edit_pm25.setText(str(self.pm25))

        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Air Purifier")
        msgBox.setText("Value out of range")
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def check_enable_fan_feature(self, feature_type):
        """
        Check fan feature map change
        then enable or disable UI corressponding to each fan feature map value
        :param feature_type {int}: A feature map value of fan feature map
        """
        self.fan_control_box.setEnabled(False)
        self.fan_control_box.model().item(AUTO_MODE).setEnabled(False)
        if ((feature_type == MULTI_SPEED) or (
                feature_type == AUTO) or (feature_type == STEP)):
            self.fan_control_box.setEnabled(True)
            if (feature_type == AUTO):
                self.fan_control_box.model().item(AUTO_MODE).setEnabled(True)
        elif (feature_type == ALL_FEATURE):
            self.fan_control_box.setEnabled(True)
            self.fan_control_box.model().item(AUTO_MODE).setEnabled(True)

    def fan_feature_changed(self, feature_type):
        """
        Handle display UI when fan control feature map change
        :param feature_type: Value feature map of fan control cluster
        """
        logging.info("RPC SET fan feature: " + str(feature_type))
        self.mutex.acquire(timeout=1)     
        self.client.SetAirPurifierSensor(self.get_air_purifier_data(fan_feature_type = feature_type))
        self.mutex.release()
 
    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            fan_data ={
                'fanControl':{
                    'fanMode': OFF_MODE,
                    'fanModeSequence': 2,
                    'fanWind': {'windSetting': SLEEP_WIND, 'windSupport': True}, 
                    'fanSpeed': {'speedSetting': 0},
                    'fanPercent': {'percentSetting': 100},
                    'fanRock': {'rockSetting': ROCK_LEFT_RIGHT,'rockSupport': True},
                    'fanAirFlowDirection': {'airFlowDirection': FORWARD}
                }
            }          
            self.client.SetAirPurifierSensor(self.get_air_purifier_data(fan_data = fan_data))
            self.fan_feature_box.setCurrentIndex(ALL_FEATURE)

            data_tem = {'measuredValue': 2821}
            self.client.SetTempValue(data_tem)

            data_hepa_condition = {'condition': 98}
            self.client.SetCondition(data_hepa_condition)

            data_air = {'airQuality': AIR_GOOD}
            self.client.SetAirQuality(data_air)

            data_humidity = {'measuredValue': 5011}
            self.client.SetHumidityValue(data_humidity)

            data_PM25 = {'measuredValue': 20}
            self.client.SetPM25(data_PM25)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def enable_update_mode(self):
        """Enable 'enable_update' attribute for enable update value of combo box"""
        self.enable_update = True

    def handle_fan_mode_changed(self, mode):
        """
        Handle fan mode change
        :param mode {int}: A new mode of fan mode
        """
        logging.info("RPC SET Fan Mode: " + str(mode))
        self.enable_update = False
        QTimer.singleShot(1, self.enable_update_mode)
        self.mutex.acquire(timeout=1)
        fan_data ={
            'fanControl': {
                'fanMode': mode,
                'fanModeSequence': self.fan_mode_sequence
            }
        } 
        self.client.SetAirPurifierSensor(self.get_air_purifier_data(fan_data = fan_data))
        self.mutex.release()      

    def check_pm25(self, pm25):
        """Check pm25 value to set air quality value respectively"""
        if 0 < self.pm25 <= 50:
            data_air = {'airQuality': AIR_GOOD}
            self.client.SetAirQuality(data_air)
        elif 50 < self.pm25 <= 100:
            data_air = {'airQuality': AIR_FAIR}
            self.client.SetAirQuality(data_air)
        elif 100 < self.pm25 <= 150:
            data_air = {'airQuality': AIR_MODERATE}
            self.client.SetAirQuality(data_air)
        elif 150 < self.pm25 <= 200:
            data_air = {'airQuality': AIR_POOR}
            self.client.SetAirQuality(data_air)
        elif 200 < self.pm25 <= 250:
            data_air = {'airQuality': AIR_VERYPOOR}
            self.client.SetAirQuality(data_air)
        elif 250 < self.pm25 <= 300:
            data_air = {'airQuality': AIR_EXTREMELY}
            self.client.SetAirQuality(data_air)
        else:
            data_air = {'airQuality': AIR_UNKNOWN}
            self.client.SetAirQuality(data_air)

    def on_device_status_changed(self, result):
        """
        Interval update all attributes value
        to UI through rpc service
        :param result {dict}: Data get all attributes value
        from matter device(backend) from rpc service
        """
        # logging.info(f'on_device_status_changed {result}, RPC Port: {str(self.parent.rpcPort)}')
        try:
            air_purifier_status = result['air_purifier_status']
            ep2_temp_measure_status = result['ep2_temp_measure_status']
            hepa_filter_status = result['hepa_filter_status']
            ep3_humidity_measure_status = result['ep3_humidity_measure_status']
            device_airquality_status = result['device_air_status']
            device_concentration_status = result['device_concentration_status']
            device_state = result['device_state']
            self.parent.update_device_state(device_state)
            if air_purifier_status['status'] == 'OK':
                if self.enable_update:
                    self.fan_mode = (
                        air_purifier_status['reply']['fanControl']['fanMode'])
                    if self.fan_mode == OFF_MODE:
                        self.lbl_main_status.setText('Fan Mode: Off')
                    elif self.fan_mode == LOW_MODE:
                        self.lbl_main_status.setText('Fan Mode: Low')
                    elif self.fan_mode == MEDIUM_MODE:
                        self.lbl_main_status.setText('Fan Mode: Medium')
                    elif self.fan_mode == HIGH_MODE:
                        self.lbl_main_status.setText('Fan Mode: High')
                    elif self.fan_mode == AUTO_MODE:
                        self.lbl_main_status.setText('Fan Mode: Auto')
                    elif self.fan_mode == ON_MODE:
                        self.lbl_main_status.setText('Fan Mode: On')
                    elif self.fan_mode == SMART_MODE:
                        self.lbl_main_status.setText('Fan Mode: Smart')
                    self.fan_control_box.setCurrentIndex((self.fan_mode))

                self.fan_mode_sequence = air_purifier_status['reply']['fanControl']['fanModeSequence']
                self.wind_mode = air_purifier_status['reply']['fanControl']['fanWind']['windSetting']
                self.speed_setting = air_purifier_status['reply']['fanControl']['fanSpeed']['speedSetting']
                self.percent_setting = air_purifier_status['reply']['fanControl']['fanPercent']['percentSetting']
                self.rock_mode = air_purifier_status['reply']['fanControl']['fanRock']['rockSetting']  
                self.air_flow = air_purifier_status['reply']['fanControl']['fanAirFlowDirection']['airFlowDirection']          

            if (self.cr_feature_type !=
                    air_purifier_status['reply']['featureMapFanControl']['featureMap']):
                self.cr_feature_type = air_purifier_status['reply']['featureMapFanControl']['featureMap']
                self.fan_feature_box.setCurrentIndex((self.cr_feature_type))
                self.check_enable_fan_feature(self.cr_feature_type)

            if ep2_temp_measure_status['status'] == 'OK':
                self.temperature = round(
                    (ep2_temp_measure_status['reply']['measuredValue'] / 100.0), 2)
                if self.is_edit_temp:
                    self.line_edit_temp.setText(str(self.temperature))

            if hepa_filter_status['status'] == 'OK':
                self.condition_filter = round(
                    hepa_filter_status['reply']['condition'])
                if self.is_edit_con:
                    self.line_edit_con.setText(str(self.condition_filter))

            if air_purifier_status['status'] == 'OK':
                self.cr_value_carbon = round(
                    air_purifier_status['reply']['activatedCarbonFilterMonitoring']['condition'])
                if self.is_edit_carbon:
                    self.line_edit_carbon.setText(str(self.cr_value_carbon))

            if ep3_humidity_measure_status['status'] == 'OK':
                self.humidity = round(
                    (ep3_humidity_measure_status['reply']['measuredValue'] / 100.0), 2)
                if self.is_edit_hum:
                    self.line_edit_hum.setText(str(self.humidity))

            if device_concentration_status['status'] == 'OK':
                self.pm25 = (
                    device_concentration_status['reply']['measuredValue'])
                if self.is_edit_pm25:
                    self.line_edit_pm25.setText(str(self.pm25))
                self.check_pm25(self.pm25)

            if device_airquality_status['status'] == 'OK':
                self.air_quality = (
                    device_airquality_status['reply']['airQuality'])
                if self.air_quality == AIR_UNKNOWN:
                    self.bt_air.setText('Unknown')
                    self.bt_air.setStyleSheet("background-color: green")
                elif self.air_quality == AIR_GOOD:
                    self.bt_air.setText('Good')
                    self.bt_air.setStyleSheet(
                        "background-color: #66FF00; color: black")
                elif self.air_quality == AIR_FAIR:
                    self.bt_air.setText('Fair')
                    self.bt_air.setStyleSheet(
                        "background-color: #FFFF33; color: black")
                elif self.air_quality == AIR_MODERATE:
                    self.bt_air.setText('Moderate')
                    self.bt_air.setStyleSheet(
                        "background-color: #FF9900; color: black")
                elif self.air_quality == AIR_POOR:
                    self.bt_air.setText('Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #FF6699; color: black")
                elif self.air_quality == AIR_VERYPOOR:
                    self.bt_air.setText('Very Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #CC66CC; color: black")
                elif self.air_quality == AIR_EXTREMELY:
                    self.bt_air.setText('Extremely Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #996699; color: black")
                self.bt_air.adjustSize()

        except Exception as e:
            logging.error("Error: " + str(e))

    def update_device_status(self):
        """
        Update value for all attributes on UI
        when set timer for change random attribute value
        """
        try:
            while self.check_condition_update_status(
                    self.update_device_status_thread):
                try:
                    self.mutex.acquire(timeout=1)
                    air_purifier_status = self.client.GetAirPurifierSensor()
                    ep2_temp_measure_status = self.client.GetTempValue()
                    hepa_filter_status = self.client.GetCondition()
                    ep3_humidity_measure_status = self.client.GetHumidityValue()
                    device_airquality_status = self.client.GetAirQuality()
                    device_concentration_status = self.client.GetPM25()
                    device_state = self.client.get_device_state()
                    self.mutex.release()
                    self.sig_device_status_changed.emit(
                        {
                            'device_air_status': device_airquality_status,
                            'air_purifier_status': air_purifier_status,
                            'ep3_humidity_measure_status': ep3_humidity_measure_status,
                            'hepa_filter_status': hepa_filter_status,
                            'ep2_temp_measure_status': ep2_temp_measure_status,
                            'device_concentration_status': device_concentration_status,
                            'device_state': device_state})
                    time.sleep(0.5)
                except Exception as e:
                    logging.error(
                        f'{str(e)} , RPC Port: {str(self.parent.rpcPort)}')
        except Exception as e:
            logging.error(str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
