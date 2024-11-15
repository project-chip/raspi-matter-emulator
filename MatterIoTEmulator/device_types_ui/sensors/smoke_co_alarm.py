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
import logging
import threading
import random
import os
import time

from rpc.smokecoalarm_client import SmokeCoAlarmClient
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/sensors/")

NORMAL = 0
WARNING = 1
CRITICAL = 2

EXP_NORMAL = 0
EXP_SMOKE_ALARM = 1
EXP_CO_ALARM = 2
EXP_BATTERY_ALERT = 3
EXP_TESTING = 4
EXP_HARDWARE_FAULT = 5
EXP_END_OF_SERVICE = 6
EXP_INTER_CONNECT_SMOKE = 7
EXP_INTER_CONNECT_CO = 8

NOT_MUTED = 0
MUTED = 1

HIGH = 0
STANDARD = 1
LOW = 2

SMOKE_FEATURE = 0
CO_FEATURE = 1
ALL_FEATURE = 2


class SmokeCoAlarm(BaseDeviceUI):
    """
    SmokeCoAlarm device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `SmokeCoAlarm` UI.
        :param parent: An UI object load SmokeCoAlarm device UI controller.
        """
        super().__init__(parent)
        self.humidity = 8000
        self.temperature = 2000
        self.battary = 150
        self.co = 35
        self.smoke_state = NORMAL
        self.co_state = NORMAL
        self.express_state = NORMAL
        self.smoke_sense_level = STANDARD
        self.battery_status = NORMAL
        self.cr_feature_type = SMOKE_FEATURE
        self.enable_update = True
        self.time_repeat = 0
        self.time_sleep = 0
        self.remaining_time_interval = 0
        self.is_stop_clicked = False
        self.contact_value = True
        self.is_edit_hum = True
        self.is_edit_bat = True
        self.is_edit_temp = True
        self.is_edit_co_done = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'smoke-co-alarm.png')
        self.lbl_main_icon.setFixedSize(70, 70)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # add feature map
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_feature = QLabel()
        self.lbl_feature.setText('Alarm Feature')
        self.parent.ui.lo_controller.addWidget(self.lbl_feature)

        smokeco_feature_list = ["SmokeAlarm", "COAlarm", "All Feature"]
        self.smokeco_feature_box = QComboBox()
        self.smokeco_feature_box.addItems(smokeco_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.smokeco_feature_box.currentIndexChanged.connect(
            self.smokeco_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.smokeco_feature_box)

        # add SmokeSensitivityLevel
        self.lbl_feature = QLabel()
        self.lbl_feature.setText('Smoke Sensitivity Level')
        self.parent.ui.lo_controller.addWidget(self.lbl_feature)

        smoke_sense_level_feature_list = ["High", "Standard", "Low"]
        self.smoke_sense_level_box = QComboBox()
        self.smoke_sense_level_box.addItems(smoke_sense_level_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.smoke_sense_level_box.currentIndexChanged.connect(
            self.smoke_sense_level_box_changed)
        self.parent.ui.lo_controller.addWidget(self.smoke_sense_level_box)

        # Battery alert
        self.lbl_feature = QLabel()
        self.lbl_feature.setText('Battery alert')
        self.parent.ui.lo_controller.addWidget(self.lbl_feature)

        battery_status_list = ["Ok", "Warning", "Critical"]
        self.battery_status_box = QComboBox()
        self.battery_status_box.addItems(battery_status_list)
        # Connect the currentIndexChanged signal to a slot
        self.battery_status_box.currentIndexChanged.connect(
            self.battery_status_changed)
        self.parent.ui.lo_controller.addWidget(self.battery_status_box)

        # Express state
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_express_state = QLabel()
        self.lbl_express_state.setText('Express state:')
        self.lbl_express_state.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_express_state)

        # Smoke Alarm
        self.lbl_main_status_smoke_alarm = QLabel()
        self.lbl_main_status_smoke_alarm.setText('Smoke Alarm:')
        self.lbl_main_status_smoke_alarm.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(
            self.lbl_main_status_smoke_alarm)

        self.btn_smoke = QPushButton()
        self.btn_smoke.setMaximumSize(QSize(100, 20))
        self.btn_smoke.setEnabled(False)

        self.grid_layout = QHBoxLayout()
        self.grid_layout.addWidget(
            self.lbl_main_status_smoke_alarm,
            alignment=Qt.AlignRight)
        self.grid_layout.addWidget(self.btn_smoke, alignment=Qt.AlignLeft)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        # CO Alarm
        self.lbl_main_status_co_alarm = QLabel()
        self.lbl_main_status_co_alarm.setText('CO Alarm:')
        self.lbl_main_status_co_alarm.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_co_alarm)

        self.btn_co = QPushButton()
        self.btn_co.setMaximumSize(QSize(100, 20))
        self.btn_co.setEnabled(False)

        self.grid_layout = QHBoxLayout()
        self.grid_layout.addWidget(
            self.lbl_main_status_co_alarm,
            alignment=Qt.AlignRight)
        self.grid_layout.addWidget(self.btn_co, alignment=Qt.AlignLeft)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        # Item Battery
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_main_status_battery = QLabel()
        self.lbl_main_status_battery.setText('Battery: ')
        self.lbl_main_status_battery.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_battery)

        self.line_edit_bat = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_bat.setValidator(self.validator)
        self.line_edit_bat.setValidator(self.double_validator)
        self.line_edit_bat.setMaximumSize(QSize(65, 20))
        self.lbl_measure_bat = QLabel()
        self.lbl_measure_bat.setText('%')
        self.grid_layout_bat = QHBoxLayout()
        self.grid_layout_bat.setAlignment(Qt.AlignCenter)
        self.grid_layout_bat.addWidget(
            self.lbl_main_status_battery,
            alignment=Qt.AlignRight)
        self.grid_layout_bat.addWidget(
            self.line_edit_bat, alignment=Qt.AlignRight)
        self.grid_layout_bat.addWidget(
            self.lbl_measure_bat, alignment=Qt.AlignRight)

        self.line_edit_bat.textEdited.connect(self.on_text_edited_bat)
        self.line_edit_bat.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_bat)

        # Item Humidity
        self.lbl_main_status_humidity = QLabel()
        self.lbl_main_status_humidity.setText('Relative Humidity: ')
        self.lbl_main_status_humidity.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_humidity)

        self.line_edit_hum = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_hum.setValidator(self.validator)
        self.line_edit_hum.setValidator(self.double_validator)
        self.line_edit_hum.setMaximumSize(QSize(65, 20))
        self.lbl_measure_hum = QLabel()
        self.lbl_measure_hum.setText('%')
        self.grid_layout_hum = QHBoxLayout()
        self.grid_layout_hum.setAlignment(Qt.AlignCenter)
        self.grid_layout_hum.addWidget(
            self.lbl_main_status_humidity,
            alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.line_edit_hum, alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.lbl_measure_hum, alignment=Qt.AlignRight)

        self.line_edit_hum.textEdited.connect(self.on_text_edited_hum)
        self.line_edit_hum.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_hum)

        # Item Temperature
        self.lbl_main_status_temp = QLabel()
        self.lbl_main_status_temp.setText('Temperature Measurement: ')
        self.lbl_main_status_temp.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_temp)

        self.line_edit_temp = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_temp.setValidator(self.validator)
        self.line_edit_temp.setValidator(self.double_validator)
        self.line_edit_temp.setMaximumSize(QSize(65, 20))
        self.lbl_measure_temp = QLabel()
        self.lbl_measure_temp.setText('°C')
        self.grid_layout_temp = QHBoxLayout()
        self.grid_layout_temp.setAlignment(Qt.AlignCenter)
        self.grid_layout_temp.addWidget(
            self.lbl_main_status_temp,
            alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.line_edit_temp, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.lbl_measure_temp, alignment=Qt.AlignRight)

        self.line_edit_temp.textEdited.connect(self.on_text_edited_temp)
        self.line_edit_temp.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_temp)

        # Item CO measurement
        self.lbl_main_status_co = QLabel()
        self.lbl_main_status_co.setText('Carbon monoxide Concentration:')
        self.lbl_main_status_co.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_co)

        self.line_edit_co = QLineEdit()
        self.line_edit_co.setValidator(self.validator)
        self.line_edit_co.setValidator(self.double_validator)
        self.line_edit_co.setMaximumSize(QSize(65, 20))
        self.lbl_measure_co = QLabel()
        self.lbl_measure_co.setText('PPM')
        self.grid_layout_co = QHBoxLayout()
        self.grid_layout_co.setAlignment(Qt.AlignCenter)
        self.grid_layout_co.addWidget(
            self.lbl_main_status_co,
            alignment=Qt.AlignRight)
        self.grid_layout_co.addWidget(
            self.line_edit_co, alignment=Qt.AlignRight)
        self.grid_layout_co.addWidget(
            self.lbl_measure_co, alignment=Qt.AlignRight)

        self.line_edit_co.textEdited.connect(self.on_text_edited_co)
        self.line_edit_co.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_co)

        # Init rpc
        self.client = SmokeCoAlarmClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

        logging.debug("Init contact sensor done")

    def smokeco_feature_changed(self, feature_type):
        """
        Handle set smoke feature map to matter device (backend)
        through rpc service
        :param feature_type: current index of smoke feature map combo box
        """
        self.mutex.acquire(timeout=1)
        self.client.set({'featureMap': {'featureMap': feature_type}})
        self.mutex.release()

    def smoke_sense_level_box_changed(self, smoke_sense_level):
        """
        Handle set smoke sense level to matter device (backend)
        through rpc service
        :param smoke_sense_level: current index of smoke sense combo box
        """
        self.mutex.acquire(timeout=1)
        self.client.set(
            {
                'smokeCOAlarmCluster': {
                    'expressedState': self.express_state,
                    'smokeState': self.smoke_state,
                    'batteryAlert': self.battery_status,
                    'coState': self.co_state,
                    'smokeSensitivityLevel': smoke_sense_level}})
        self.mutex.release()

    def enable_update_mode(self):
        """Enable 'enable_update' attribute to enable update value for combo box"""
        self.enable_update = True

    def battery_status_changed(self, battery_index):
        """
        Handle set battery alert value to matter device(backend)
        through rpc service
        :param battery_index: current index of battery alert combo box
        """
        logging.info("RPC set battery: " + str(battery_index))
        self.enable_update = False
        QTimer.singleShot(1.2, self.enable_update_mode)
        self.mutex.acquire(timeout=1)
        self.client.set(
            {
                'smokeCOAlarmCluster': {
                    'expressedState': self.express_state,
                    'smokeState': self.smoke_state,
                    'batteryAlert': battery_index,
                    'coState': self.co_state,
                    'smokeSensitivityLevel': self.smoke_sense_level}})
        self.mutex.release()

    def on_text_edited_bat(self):
        """Enable 'is_edit_bat' attribute
        when line edit battery percent is editting"""
        self.is_edit_bat = False

    def on_text_edited_hum(self):
        """Enable 'is_edit_hum' attribute
        when line edit humidity is editting"""
        self.is_edit_hum = False

    def on_text_edited_temp(self):
        """Enable 'is_edit_temp' attribute
        when line edit temperature is editting"""
        self.is_edit_temp = False

    def on_text_edited_co(self):
        """Enable 'is_edit_co' attribute
        when line edit co is editting"""
        self.is_edit_co_done = False

    def on_return_pressed(self):
        """
        Handle update all smoke-co alarm and power source attributes
        to matter device(backend) through rpc service
        after enter value to line edit done
        """
        try:
            value_temp = round(float(self.line_edit_temp.text()) * 100)
            value_hum = round(float(self.line_edit_hum.text()) * 100)
            value_co = round(float(self.line_edit_co.text()), 2)
            value_bat = round(int(self.line_edit_bat.text()) * 2)
            if 0 <= value_hum <= 10000:
                data = {
                    'relativeHumidityMeasurement': {
                        'measuredValue': value_hum}}
                self.client.set(data)
                self.is_edit_hum = True
            else:
                self.message_box(ER_HUM)
                self.line_edit_hum.setText(str(self.humidity))

            if 0 <= value_bat <= 200:
                data = {'powerSource': {'batPercentRemaining': value_bat}}
                self.client.set(data)
                self.is_edit_bat = True
            else:
                self.message_box(ER_BAT)
                self.line_edit_bat.setText(str(self.battary))

            if 0 <= value_temp <= 10000:
                data = {
                    'temperatureMeasurement': {
                        'measuredValue': value_temp}}
                self.client.set(data)
                self.is_edit_temp = True
            else:
                self.message_box(ER_TEMP)
                self.line_edit_temp.setText(str(self.temperature))

            if 0 <= value_co <= 150:
                data = {
                    'carbonMonoxideConcentrationMeasurement': {
                        'measuredValue': value_co}}
                self.client.set(data)
                self.is_edit_co_done = True
            else:
                self.message_box(ER_CO)
                self.line_edit_co.setText(str(self.co))
        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Smoke Co Alarm")
        msgBox.setText("Value out of range")
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'smokeCOAlarmCluster': {
                    'expressedState': EXP_NORMAL,
                    'smokeState': NORMAL,
                    'batteryAlert': NORMAL,
                    'coState': NORMAL,
                    'smokeSensitivityLevel': HIGH},
                'featureMap': {
                    'featureMap': ALL_FEATURE},
                'relativeHumidityMeasurement': {
                    'measuredValue': self.humidity},
                'temperatureMeasurement': {
                    'measuredValue': self.temperature},
                'carbonMonoxideConcentrationMeasurement': {
                    'measuredValue': self.co},
                'powerSource': {
                    'batPercentRemaining': self.battary},
            }
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def check_co(self):
        """
        Check value of co measurement to set express state attribute,
        smoke state and coState attribute
        """
        if 0 < self.co <= 30:
            data = {
                'smokeCOAlarmCluster': {
                    'expressedState': EXP_NORMAL,
                    'smokeState': NORMAL,
                    'coState': NORMAL,
                    'smokeSensitivityLevel': self.smoke_sense_level,
                    'batteryAlert': self.battery_status}}
            self.client.set(data)
        elif 30 < self.co <= 70:
            data = {
                'smokeCOAlarmCluster': {
                    'expressedState': EXP_NORMAL,
                    'smokeState': WARNING,
                    'coState': WARNING,
                    'smokeSensitivityLevel': self.smoke_sense_level,
                    'batteryAlert': self.battery_status}}
            self.client.set(data)
        else:
            data = {
                'smokeCOAlarmCluster': {
                    'expressedState': EXP_SMOKE_ALARM,
                    'smokeState': CRITICAL,
                    'coState': CRITICAL,
                    'smokeSensitivityLevel': self.smoke_sense_level,
                    'batteryAlert': self.battery_status}}
            self.client.set(data)

    def set_express_state_status(self):
        """
        Check value of express state attribute to set express state label
        """
        if self.express_state == EXP_NORMAL:
            self.lbl_express_state.setText('Express state: Normal')
        elif self.express_state == EXP_SMOKE_ALARM:
            self.lbl_express_state.setText('Express state: Smoke Alarm')
        elif self.express_state == EXP_CO_ALARM:
            self.lbl_express_state.setText('Express state: CO Alarm')
        elif self.express_state == EXP_BATTERY_ALERT:
            self.lbl_express_state.setText('Express state: Battery alert')
        elif self.express_state == EXP_TESTING:
            self.lbl_express_state.setText('Express state: Testing')
        elif self.express_state == EXP_HARDWARE_FAULT:
            self.lbl_express_state.setText('Express state: Hardware Fault')
        elif self.express_state == EXP_END_OF_SERVICE:
            self.lbl_express_state.setText('Express state: End Of Service')
        elif self.express_state == EXP_INTER_CONNECT_SMOKE:
            self.lbl_express_state.setText(
                'Express state: Inter Connect Smoke')
        elif self.express_state == EXP_INTER_CONNECT_CO:
            self.lbl_express_state.setText('Express state: Inter Connect CO')

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
                # Update feature map
                if (self.cr_feature_type !=
                        device_status['reply']['featureMap']['featureMap']):
                    self.cr_feature_type = device_status['reply']['featureMap']['featureMap']
                    self.smokeco_feature_box.setCurrentIndex(
                        self.cr_feature_type)

                # Update smoke sense level
                if (self.smoke_sense_level !=
                        device_status['reply']["smokeCOAlarmCluster"]["smokeSensitivityLevel"]):
                    self.smoke_sense_level = device_status['reply']["smokeCOAlarmCluster"]["smokeSensitivityLevel"]
                    self.smoke_sense_level_box.setCurrentIndex(
                        self.smoke_sense_level)

                # Update battery status
                if self.enable_update:
                    self.battery_status = device_status['reply']["smokeCOAlarmCluster"]["batteryAlert"]
                    self.battery_status_box.setCurrentIndex(
                        self.battery_status)

                # Update humidity
                self.humidity = round(
                    float(
                        device_status['reply']['relativeHumidityMeasurement']['measuredValue']) / 100, 2)
                if self.is_edit_hum:
                    self.line_edit_hum.setText(str(self.humidity))

                # Update temperature
                self.temperature = round(
                    float(
                        device_status['reply']['temperatureMeasurement']['measuredValue']) / 100, 2)
                if self.is_edit_temp:
                    self.line_edit_temp.setText(str(self.temperature))

                # Update battary
                self.battary = round(
                    int(device_status['reply']['powerSource']['batPercentRemaining']) / 2)
                if self.is_edit_bat:
                    self.line_edit_bat.setText(str(self.battary))

                # Update express state
                self.express_state = (
                    device_status['reply']["smokeCOAlarmCluster"]["expressedState"])
                self.set_express_state_status()

                # Update CO measurement
                self.co = round(
                    float(
                        device_status['reply']["carbonMonoxideConcentrationMeasurement"]["measuredValue"]), 2)
                if self.is_edit_co_done:
                    self.line_edit_co.setText(str(self.co))
                    self.check_co()

                # Update smoke state
                self.smoke_state = (
                    device_status['reply']["smokeCOAlarmCluster"]["smokeState"])
                if self.smoke_state == NORMAL:
                    self.btn_smoke.setText('Normal')
                    self.btn_smoke.setStyleSheet(
                        "background-color: #66FF00; color: black")
                elif self.smoke_state == WARNING:
                    self.btn_smoke.setText('Warning')
                    self.btn_smoke.setStyleSheet(
                        "background-color: #FFCC00; color: black")
                elif self.smoke_state == CRITICAL:
                    self.btn_smoke.setText('Critical')
                    self.btn_smoke.setStyleSheet(
                        "background-color: #FF0000; color: black")
                self.btn_smoke.adjustSize()

                # Update co state
                self.co_state = (
                    device_status['reply']["smokeCOAlarmCluster"]["coState"])
                if self.co_state == NORMAL:
                    self.btn_co.setText('Normal')
                    self.btn_co.setStyleSheet(
                        "background-color: #66FF00; color: black")
                elif self.co_state == WARNING:
                    self.btn_co.setText('Warning')
                    self.btn_co.setStyleSheet(
                        "background-color: #FFCC00; color: black")
                elif self.co_state == CRITICAL:
                    self.btn_co.setText('Critical')
                    self.btn_co.setStyleSheet(
                        "background-color: #FF0000; color: black")
                self.btn_co.adjustSize()

                # self.lbl_remain_repeat_time.setText('Remaining count: ' + str(self.time_repeat))
                # self.lbl_remaining_time_interval.setText('Remaining time of interval: ' + str(self.remaining_time_interval) + " sec")
        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
