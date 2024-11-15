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
from rpc.fan_client import FanClient
from ..stoppablethread import UpdateStatusThread
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

ROCK_LEFT_RIGHT = 1
ROCK_UP_DOWN = 2
ROCK_ROUND = 4

SLEEP_WIND = 1
NATURAL_WIND = 2

FORWARD = 0
REVERSE = 1

MULTI_SPEED = 0
AUTO = 1
ROCKING = 2
WIND = 3
STEP = 4
AIR_FLOW_DIRECTION = 5
ALL_FEATURE = 6


class Fan(BaseDeviceUI):
    """
    Fan device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `Fan` UI.
        :param parent: An UI object load Fan device UI controller.
        """
        super().__init__(parent)
        self.fan_mode = 0
        self.fan_sequence_mode = 2
        self.rock_mode = 0
        self.wind_mode = 0
        self.air_flow = 0
        self.enable_update = True
        self.cr_feature_type = MULTI_SPEED

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'fan.png')
        self.lbl_main_icon.setFixedSize(80, 80)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('Fan Mode: Off')
        self.lbl_main_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        # Fan feature map
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
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Show fan mode
        self.sl_title = QLabel()
        self.sl_title.setText('Fan Mode')
        self.parent.ui.lo_controller.addWidget(self.sl_title)

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
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Rock fan mode
        self.lb_rock_title = QLabel()
        self.lb_rock_title.setText('Rock Setting')
        self.parent.ui.lo_controller.addWidget(self.lb_rock_title)
        # Create rock fan mode
        rock_mode_list = ["RockLeftRight", "RockUpDown", "RockRound"]
        self.rock_control_box = QComboBox()
        self.rock_control_box.addItems(rock_mode_list)
        # Connect the currentIndexChanged signal to a slot
        self.rock_control_box.currentIndexChanged.connect(
            self.handle_rock_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.rock_control_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Wind fan mode
        self.lb_wind_title = QLabel()
        self.lb_wind_title.setText('Wind Setting')
        self.parent.ui.lo_controller.addWidget(self.lb_wind_title)
        wind_mode_list = ["SleepWind", "NaturalWind"]
        self.wind_control_box = QComboBox()
        self.wind_control_box.addItems(wind_mode_list)
        # Connect the currentIndexChanged signal to a slot
        self.wind_control_box.currentIndexChanged.connect(
            self.handle_wind_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.wind_control_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Air flow direction mode
        self.lb_airflow_title = QLabel()
        self.lb_airflow_title.setText('AirFlow')
        self.parent.ui.lo_controller.addWidget(self.lb_airflow_title)
        airflow_mode_list = ["Forward", "Reverse"]
        self.airflow_control_box = QComboBox()
        self.airflow_control_box.addItems(airflow_mode_list)
        # Connect the currentIndexChanged signal to a slot
        self.airflow_control_box.currentIndexChanged.connect(
            self.handle_airflow_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.airflow_control_box)

        # Init rpc
        self.client = FanClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

        logging.debug("Init Fan done")

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'fanMode': MEDIUM_MODE,
                'fanModeSequence': self.fan_sequence_mode,
                'fanWind': {'windSetting': SLEEP_WIND, 'windSupport': True}, 
                'fanSpeed': {'speedSetting': 30},
                'fanPercent': {'percentSetting': 100},
                'fanRock': {'rockSetting': ROCK_LEFT_RIGHT,'rockSupport': True},
                'fanAirFlowDirection': {'airFlowDirection': FORWARD},
                'featureMap': {'featureMap': ALL_FEATURE}}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def handle_rock_mode_changed(self, index):
        """
        Handle rock mode change
        :param index {int}: A index of rock combo box
        """
        logging.info("RPC SET Rock Mode at index: " + str(index))
        if (0 == index):
            self.rock_mode = ROCK_LEFT_RIGHT
        elif (1 == index):
            self.rock_mode = ROCK_UP_DOWN
        elif (2 == index):
            self.rock_mode = ROCK_ROUND
        self.mutex.acquire(timeout=1)
        self.client.set(
            {'fanRock': {'rockSetting': self.rock_mode, 'rockSupport': True}})
        self.mutex.release()

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
        self.client.set({'fanMode': mode})
        self.fan_mode = mode
        self.mutex.release()

    def handle_wind_mode_changed(self, index):
        """
        Handle wind mode change
        :param index {int}: A index of wind combo box
        """
        logging.info("RPC SET Wind Mode: " + str(index + 1))
        self.mutex.acquire(timeout=1)
        self.client.set(
            {'fanWind': {'windSetting': (index + 1), 'windSupport': True}})
        self.mutex.release()

    def handle_airflow_mode_changed(self, mode):
        """
        Handle air flow mode change
        :param index {int}: A index of air flow combo box
        """
        logging.info("RPC SET Air flow direction Mode: " + str(mode))
        self.mutex.acquire(timeout=1)
        self.client.set({'fanAirFlowDirection': {'airFlowDirection': mode}})
        self.mutex.release()

    def fan_feature_changed(self, feature_type):
        """
        Handle display UI when fan control feature map change
        :param feature_type: Value feature map of fan control cluster
        """
        logging.info("RPC SET Fan feature Mode: " + str(feature_type))
        self.mutex.acquire(timeout=1)
        self.client.set({'featureMap': {'featureMap': feature_type}})
        self.mutex.release()

    def check_enable_fan_feature(self, feature_type):
        """
        Check fan feature map change
        then enable or disable UI corressponding to each fan feature map value
        :param feature_type {int}: A feature map value of fan feature map
        """
        self.fan_control_box.setEnabled(False)
        self.rock_control_box.setEnabled(False)
        self.wind_control_box.setEnabled(False)
        self.airflow_control_box.setEnabled(False)
        self.fan_control_box.model().item(AUTO_MODE).setEnabled(False)
        if ((feature_type == MULTI_SPEED) or (
                feature_type == AUTO) or (feature_type == STEP)):
            self.fan_control_box.setEnabled(True)
            if (feature_type == AUTO):
                self.fan_control_box.model().item(AUTO_MODE).setEnabled(True)
        elif (feature_type == ROCKING):
            self.rock_control_box.setEnabled(True)
        elif (feature_type == WIND):
            self.wind_control_box.setEnabled(True)
        elif (feature_type == AIR_FLOW_DIRECTION):
            self.airflow_control_box.setEnabled(True)
        elif (feature_type == ALL_FEATURE):
            self.fan_control_box.setEnabled(True)
            self.rock_control_box.setEnabled(True)
            self.wind_control_box.setEnabled(True)
            self.airflow_control_box.setEnabled(True)
            self.fan_control_box.model().item(AUTO_MODE).setEnabled(True)

    def on_device_status_changed(self, result):
        """
        Interval update all attributes value
        to UI through rpc service
        :param result {dict}: Data get all attributes value
        from matter device(backend) from rpc service
        """
        # logging.info(f'on_device_status_changed {result}, RPC Port: {str(self.parent.rpcPort)}')
        try:
            device_status = result['device_status']
            device_state = result['device_state']
            self.parent.update_device_state(device_state)
            if device_status['status'] == 'OK':
                if self.enable_update:
                    self.fan_mode = (device_status['reply'].get('fanMode'))
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
                    self.fan_control_box.setCurrentIndex(self.fan_mode)

                if (self.rock_mode != (
                        device_status['reply']['fanRock']['rockSetting'])):
                    self.rock_mode = (
                        device_status['reply']['fanRock']['rockSetting'])
                    index = 0
                    if (ROCK_LEFT_RIGHT == self.rock_mode):
                        index = 0
                    elif (ROCK_UP_DOWN == self.rock_mode):
                        index = 1
                    elif (ROCK_ROUND == self.rock_mode):
                        index = 2
                    self.rock_control_box.setCurrentIndex(index)

                if (self.wind_mode != (
                        device_status['reply']['fanWind']['windSetting'])):
                    self.wind_mode = (
                        device_status['reply']['fanWind']['windSetting'])
                    index = 0
                    if (self.wind_mode > 0):
                        index = self.wind_mode - 1
                    self.wind_control_box.setCurrentIndex(index)

                if (self.air_flow != (
                        device_status['reply']['fanAirFlowDirection']['airFlowDirection'])):
                    self.air_flow = (
                        device_status['reply']['fanAirFlowDirection']['airFlowDirection'])
                    self.airflow_control_box.setCurrentIndex(self.air_flow)

                if (self.cr_feature_type !=
                        device_status['reply']['featureMap']['featureMap']):
                    self.cr_feature_type = device_status['reply']['featureMap']['featureMap']
                    self.fan_feature_box.setCurrentIndex(self.cr_feature_type)
                    self.check_enable_fan_feature(self.cr_feature_type)

                # speed = (device_status['reply']['fanSpeed']['speedSetting'])
                # self.sl_speed_level.setValue(int(speed))

        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
