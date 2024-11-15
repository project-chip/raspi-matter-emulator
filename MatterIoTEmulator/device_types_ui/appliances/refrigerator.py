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
from rpc.refrigerator_client import RefrigeratorClient
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/Appliances/")

TEMP_NUMBER_FEATURE = 0
TEMP_LEVEL_FEATURE = 1
TEMP_STEP_FEATURE = 2


class Refrigerator(BaseDeviceUI):
    """
    Refrigerator device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `Refrigerator` UI.
        :param parent: An UI object load Refrigerator device UI controller.
        """
        super().__init__(parent)
        self.system_mode = 0

        self.temp_freeze = 0
        self.temp_freeze_sensor = 0
        self.temp_cold = 0
        self.temp_cold_sensor = 0

        self.alarm_feature = 0
        self.alarm_state = 0

        self.cold_temp_feature = 0
        self.free_temp_feature = 0

        self.step_cold = 100
        self.step_freeze = 100

        self.temp_level_cold = 0
        self.temp_level_freeze = 0

        self.is_edit_clod = True
        self.is_edit_freezer = True

        self.is_edit_step_cold = True
        self.is_edit_step_freeze = True

        self.step_on_cold = False
        self.step_on_freeze = False

        self.select_temp_level_cold = False
        self.select_temp_level_freeze = False

        self.number_temp_cold = True
        self.number_temp_freeze = True

        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'fridge.png')
        self.lbl_main_icon.setFixedSize(70, 70)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Temperature refrigerator (cold cabinet)
        self.lbl_cold_status = QLabel()
        self.lbl_cold_status.setText('Temperature cold:')
        self.lbl_cold_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_cold_status)

        self.line_edit_cold = QLineEdit()
        self.line_edit_cold.setValidator(self.validator)
        self.line_edit_cold.setValidator(self.double_validator)
        self.line_edit_cold.setMaximumSize(QSize(65, 20))
        self.lbl_measure_cold = QLabel()
        self.lbl_measure_cold.setText('°C')
        self.grid_layout_cold = QHBoxLayout()
        self.grid_layout_cold.setAlignment(Qt.AlignCenter)
        self.grid_layout_cold.addWidget(
            self.lbl_cold_status, alignment=Qt.AlignRight)
        self.grid_layout_cold.addWidget(
            self.line_edit_cold, alignment=Qt.AlignRight)
        self.grid_layout_cold.addWidget(
            self.lbl_measure_cold, alignment=Qt.AlignRight)

        self.line_edit_cold.textEdited.connect(self.on_text_edited_cold)
        self.line_edit_cold.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_cold)

        # Temp Feature Control Refrigerator
        self.lbl_cold_tem_feature = QLabel()
        self.lbl_cold_tem_feature.setText(
            'Refrigerator Temperature Control Feature:')
        self.parent.ui.lo_controller.addWidget(self.lbl_cold_tem_feature)
        # Create a temp control mode
        cold_tem_control_list = [
            "Temperature Number",
            "Temperature Level",
            "Temperature Step"]
        self.cold_tem_control_box = QComboBox()
        self.cold_tem_control_box.addItems(cold_tem_control_list)
        # Connect the currentIndexChanged signal to a slot
        self.cold_tem_control_box.currentIndexChanged.connect(
            self.handle_cold_temp_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.cold_tem_control_box)

        # Add temp feature cold layout
        self.grid_layout_feature_tem_cold = QGridLayout()
        self.grid_layout_feature_tem_cold.addWidget(
            self.lbl_cold_tem_feature, 0, 0)
        self.grid_layout_feature_tem_cold.addWidget(
            self.cold_tem_control_box, 0, 1)
        self.parent.ui.lo_controller.addLayout(
            self.grid_layout_feature_tem_cold)

        # Show dimmable slider temperature  cold cabinet
        self.lb_cold_title = QLabel()
        self.lb_cold_title.setText('Temperature cold')
        self.parent.ui.lo_controller.addWidget(self.lb_cold_title)
        self.lb_cold_value = QLabel()
        self.lb_cold_value.setFixedSize(50, 30)
        self.lb_cold_value.setText('°C')
        self.lb_cold_value.setAlignment(Qt.AlignCenter)

        self.sl_cold_level = QSlider()
        self.sl_cold_level.setRange(0, 700)
        self.sl_cold_level.setOrientation(Qt.Horizontal)
        self.sl_cold_level.valueChanged.connect(self.update_lb_cold)
        self.sl_cold_level.sliderPressed.connect(self.on_pressed_event)
        self.sl_cold_level.sliderReleased.connect(self.dimming_cold)

        self.grid_layout_cold = QGridLayout()
        self.grid_layout_cold.addWidget(self.lb_cold_title, 1, 0)
        self.grid_layout_cold.addWidget(self.lb_cold_value, 1, 1)
        self.grid_layout_cold.addWidget(self.sl_cold_level)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_cold)

        # Temperature freeze cabinet
        self.lbl_freezer_status = QLabel()
        self.lbl_freezer_status.setText('Temperature freezer:')
        self.lbl_freezer_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_freezer_status)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        self.line_edit_freezer = QLineEdit()
        self.line_edit_freezer.setValidator(self.validator)
        self.line_edit_freezer.setValidator(self.double_validator)
        self.line_edit_freezer.setMaximumSize(QSize(65, 20))
        self.lbl_measure_freezer = QLabel()
        self.lbl_measure_freezer.setText('°C')
        self.grid_layout_freezer = QHBoxLayout()
        self.grid_layout_freezer.setAlignment(Qt.AlignCenter)
        self.grid_layout_freezer.addWidget(
            self.lbl_freezer_status, alignment=Qt.AlignRight)
        self.grid_layout_freezer.addWidget(
            self.line_edit_freezer, alignment=Qt.AlignRight)
        self.grid_layout_freezer.addWidget(
            self.lbl_measure_freezer, alignment=Qt.AlignRight)

        self.line_edit_freezer.textEdited.connect(self.on_text_edited_freeze)
        self.line_edit_freezer.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_freezer)

        self.parent.ui.lo_controller.addWidget(QLabel(""))
        # Temp Feature Control Refrigerator
        self.lbl_freeze_tem_feature = QLabel()
        self.lbl_freeze_tem_feature.setText(
            'Freeze Temperature Control Feature:')
        self.parent.ui.lo_controller.addWidget(self.lbl_freeze_tem_feature)
        # Create a temp control mode
        freeze_tem_control_list = [
            "Temperature Number",
            "Temperature Level",
            "Temperature Step"]
        self.freeze_tem_control_box = QComboBox()
        self.freeze_tem_control_box.addItems(freeze_tem_control_list)
        # Connect the currentIndexChanged signal to a slot
        self.freeze_tem_control_box.currentIndexChanged.connect(
            self.handle_freeze_temp_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.freeze_tem_control_box)
        # add layout
        self.grid_layout_feature_tem_freeze = QGridLayout()
        self.grid_layout_feature_tem_freeze.addWidget(
            self.lbl_freeze_tem_feature, 0, 0)
        self.grid_layout_feature_tem_freeze.addWidget(
            self.freeze_tem_control_box, 0, 1)
        self.parent.ui.lo_controller.addLayout(
            self.grid_layout_feature_tem_freeze)

        # Show dimmable slider freeze
        self.lb_freezer_title = QLabel()
        self.lb_freezer_title.setText('Temperature freezer:')
        self.parent.ui.lo_controller.addWidget(self.lb_freezer_title)
        self.lb_freezer_value = QLabel()
        self.lb_freezer_value.setText('°C')
        self.lb_freezer_value.setFixedSize(50, 30)
        self.lb_freezer_value.setAlignment(Qt.AlignCenter)

        self.sl_freezer_level = QSlider()
        self.sl_freezer_level.setRange(-1700, 0)
        self.sl_freezer_level.setOrientation(Qt.Horizontal)
        self.sl_freezer_level.valueChanged.connect(self.update_lb_freezer)
        self.sl_freezer_level.sliderPressed.connect(self.on_pressed_event)
        self.sl_freezer_level.sliderReleased.connect(self.dimming_freezer)

        self.grid_layout_freeze = QGridLayout()
        self.grid_layout_freeze.addWidget(self.lb_freezer_title, 0, 0)
        self.grid_layout_freeze.addWidget(self.lb_freezer_value, 0, 1)
        self.grid_layout_freeze.addWidget(self.sl_freezer_level)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_freeze)

        # Refrigerator Cabinet Mode
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_mod = QLabel()
        self.lbl_mod.setText('Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_mod)
        # Create a refrigerator mode
        mod_list = ["Normal", "RapidCool", "RapidFreeze"]
        self.mod_box = QComboBox()
        self.mod_box.addItems(mod_list)
        # Connect the currentIndexChanged signal to a slot
        self.mod_box.currentIndexChanged.connect(self.handle_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.mod_box)

        """
        #Alarm feature
        self.lbl_alarm_feature_= QLabel()
        self.lbl_alarm_feature_.setText('Refrigerator alarm feature:')
        self.parent.ui.lo_controller.addWidget(self.lbl_alarm_feature_)
        # Create a alarm feature list
        alarm_feature_list = ["No Support", "Reset"]
        self.alarm_feature_box = QComboBox()
        self.alarm_feature_box.addItems(alarm_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.alarm_feature_box.currentIndexChanged.connect(self.handle_alarm_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.alarm_feature_box)
        """

        # Alarm state
        self.lbl_alarm_state = QLabel()
        self.lbl_alarm_state.setText('Refrigerator alarm state:')
        self.parent.ui.lo_controller.addWidget(self.lbl_alarm_state)

        # Create alarm state list
        alarm_state_list = ["No Alarm", "Door Open"]
        self.alarm_state_box = QComboBox()
        self.alarm_state_box.addItems(alarm_state_list)
        self.alarm_state_box.setCurrentIndex(self.alarm_state)

        # Connect the currentIndexChanged signal to a slot
        self.alarm_state_box.currentIndexChanged.connect(
            self.handle_alarm_state_changed)
        self.parent.ui.lo_controller.addWidget(self.alarm_state_box)

        # Init rpc
        self.client = RefrigeratorClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()
        logging.debug("Init Lighting done")

    def handle_alarm_feature_changed(self, feature):
        """
        Handle set alarm feature when alarm feature map change
        :param feature: Alarm feature map value
        """
        logging.info("RPC SET alarm feature: " + str(feature))
        self.mutex.acquire(timeout=1)
        self.client.SetRefrigerator(
            {"refrigeratorAlarmFeature": {"featureMap": feature}})
        self.mutex.release()

    def handle_alarm_state_changed(self, alarm):
        """
        Handle set alarm state when alarm state change
        :param alarm: Alarm state value
        """
        logging.info("RPC SET alarm state: " + str(bool(alarm)))
        self.mutex.acquire(timeout=1)
        self.client.SetRefrigerator(
            {"refrigeratorAlarm": {"alarm": bool(alarm)}})
        self.mutex.release()

    def handle_cold_temp_feature_changed(self, cold_feature):
        """
        Handle display UI when temperature control feature map of cold cabinet change
        :param cold_feature: Value feature map of temperature control cluster
        """
        logging.info("RPC SET cold temp feature: " + str(cold_feature))
        self.number_temp_cold = False
        self.select_temp_level_cold = False
        self.step_on_cold = False
        self.clear_layout_cold()
        self.mutex.acquire(timeout=1)
        self.client.SetColdCabinet(
            {"coldTempControlFeature": {"featureMap": cold_feature}})
        self.mutex.release()
        if cold_feature == TEMP_NUMBER_FEATURE:
            self.number_temp_cold = True
            self.lb_cold_title = QLabel()
            self.lb_cold_title.setText('Temperature cold')
            self.lb_cold_value = QLabel()
            self.lb_cold_value.setFixedSize(50, 30)
            self.lb_cold_value.setText('°C')

            self.sl_cold_level = QSlider()
            self.sl_cold_level.setRange(0, 700)
            self.sl_cold_level.setOrientation(Qt.Horizontal)
            self.sl_cold_level.valueChanged.connect(self.update_lb_cold)
            self.sl_cold_level.sliderPressed.connect(self.on_pressed_event)
            self.sl_cold_level.sliderReleased.connect(self.dimming_cold)

            self.grid_layout_cold.addWidget(self.lb_cold_title, 0, 0)
            self.grid_layout_cold.addWidget(
                self.lb_cold_value, 0, 1, 1, 1, alignment=Qt.AlignRight)
            self.grid_layout_cold.addWidget(self.sl_cold_level, 1, 0, 1, 2)

        elif cold_feature == TEMP_LEVEL_FEATURE:
            self.select_temp_level_cold = True
            self.lbl_level_mod_cold = QLabel()
            self.lbl_level_mod_cold.setText('Temperature level')

            level_list_cold = ["Normal", "Warm", "Hot", "Cold"]
            self.level_box_cold = QComboBox()
            self.level_box_cold.addItems(level_list_cold)
            # Connect the currentIndexChanged signal to a slot
            self.level_box_cold.currentIndexChanged.connect(
                self.handle_level_box_changed_cold)
            self.grid_layout_cold.addWidget(self.lbl_level_mod_cold, 0, 0)
            self.grid_layout_cold.addWidget(self.level_box_cold, 0, 1)

        elif cold_feature == TEMP_STEP_FEATURE:
            self.step_on_cold = True
            self.number_temp_cold = True
            self.lb_cold_title = QLabel()
            self.lb_cold_title.setText('Temperature refrigerator')
            self.lb_cold_value = QLabel()
            self.lb_cold_value.setText('°C')

            self.sl_cold_level = QSlider()
            self.sl_cold_level.setRange(0, 700)
            self.sl_cold_level.setOrientation(Qt.Horizontal)
            self.sl_cold_level.valueChanged.connect(self.update_lb_cold)
            self.sl_cold_level.sliderPressed.connect(self.on_pressed_event)
            self.sl_cold_level.sliderReleased.connect(self.dimming_cold)

            self.lbl_step_mod_cold = QLabel()
            self.lbl_step_mod_cold.setText('Temperature step:')

            self.line_edit_step_cold = QLineEdit()
            self.line_edit_step_cold.setValidator(self.validator)
            self.line_edit_step_cold.setValidator(self.double_validator)
            self.line_edit_step_cold.textEdited.connect(
                self.on_text_step_cold_edited)
            self.line_edit_step_cold.returnPressed.connect(
                self.on_return_pressed_step_cold)
            self.line_edit_step_cold.setMaximumSize(QSize(65, 20))

            self.grid_layout_cold.addWidget(self.lb_cold_title, 0, 0)
            self.grid_layout_cold.addWidget(
                self.lb_cold_value, 0, 1, alignment=Qt.AlignRight)
            self.grid_layout_cold.addWidget(self.sl_cold_level, 1, 0, 1, 2)

            self.grid_layout_cold.addWidget(self.lbl_step_mod_cold, 2, 0)
            self.grid_layout_cold.addWidget(
                self.line_edit_step_cold, 2, 1, 1, 1, alignment=Qt.AlignLeft)

    def handle_freeze_temp_feature_changed(self, freeze_feature):
        """
        Handle display UI when temperature control feature map of freeze cabinet change
        :param freeze_feature: Value feature map of temperature control cluster
        """
        self.number_temp_freeze = False
        self.select_temp_level_freeze = False
        self.step_on_freeze = False
        self.clear_layout_freeze()
        self.mutex.acquire(timeout=1)
        self.client.SetFreezeCabinet(
            {"freezeTempControlFeature": {"featureMap": freeze_feature}})
        self.mutex.release()
        if freeze_feature == TEMP_NUMBER_FEATURE:
            self.number_temp_freeze = True
            self.lb_freezer_title = QLabel()
            self.lb_freezer_title.setText('Temperature freezer:')
            self.lb_freezer_value = QLabel()
            self.lb_freezer_value.setText('°C')

            self.sl_freezer_level = QSlider()
            self.sl_freezer_level.setRange(-1700, 0)
            self.sl_freezer_level.setOrientation(Qt.Horizontal)
            self.sl_freezer_level.valueChanged.connect(self.update_lb_freezer)
            self.sl_freezer_level.sliderPressed.connect(self.on_pressed_event)
            self.sl_freezer_level.sliderReleased.connect(self.dimming_freezer)

            self.grid_layout_freeze.addWidget(self.lb_freezer_title, 0, 0)
            self.grid_layout_freeze.addWidget(
                self.lb_freezer_value, 0, 1, alignment=Qt.AlignRight)
            self.grid_layout_freeze.addWidget(
                self.sl_freezer_level, 1, 0, 1, 2)

        elif freeze_feature == TEMP_LEVEL_FEATURE:
            self.select_temp_level_freeze = True
            self.lbl_level_mod_freeze = QLabel()
            self.lbl_level_mod_freeze.setText('Temperature level')

            level_list_freeze = ["Normal", "Warm", "Hot", "Cold"]
            self.level_box_freeze = QComboBox()
            self.level_box_freeze.addItems(level_list_freeze)
            # Connect the currentIndexChanged signal to a slot
            self.level_box_freeze.currentIndexChanged.connect(
                self.handle_level_box_changed_freeze)
            self.grid_layout_freeze.addWidget(self.lbl_level_mod_freeze, 0, 0)
            self.grid_layout_freeze.addWidget(self.level_box_freeze, 0, 1)

        elif freeze_feature == TEMP_STEP_FEATURE:
            self.step_on_freeze = True
            self.number_temp_freeze = True
            self.lb_freezer_title = QLabel()
            self.lb_freezer_title.setText('Temperature freezer:')
            self.lb_freezer_value = QLabel()
            self.lb_freezer_value.setText('°C')

            self.sl_freezer_level = QSlider()
            self.sl_freezer_level.setRange(-1700, 0)
            self.sl_freezer_level.setOrientation(Qt.Horizontal)
            self.sl_freezer_level.valueChanged.connect(self.update_lb_freezer)
            self.sl_freezer_level.sliderPressed.connect(self.on_pressed_event)
            self.sl_freezer_level.sliderReleased.connect(self.dimming_freezer)

            self.lbl_step_mod_freeze = QLabel()
            self.lbl_step_mod_freeze.setText('Temperature step:')

            self.line_edit_step_freeze = QLineEdit()
            self.line_edit_step_freeze.setValidator(self.validator)
            self.line_edit_step_freeze.setValidator(self.double_validator)
            self.line_edit_step_freeze.textEdited.connect(
                self.on_text_step_freeze_edited)
            self.line_edit_step_freeze.returnPressed.connect(
                self.on_return_pressed_step_freeze)
            self.line_edit_step_freeze.setMaximumSize(QSize(65, 20))

            self.grid_layout_freeze.addWidget(self.lb_freezer_title, 0, 0)
            self.grid_layout_freeze.addWidget(
                self.lb_freezer_value, 0, 1, 1, 1, alignment=Qt.AlignRight)
            self.grid_layout_freeze.addWidget(
                self.sl_freezer_level, 1, 0, 1, 2)

            self.grid_layout_freeze.addWidget(self.lbl_step_mod_freeze, 2, 0)
            self.grid_layout_freeze.addWidget(
                self.line_edit_step_freeze, 2, 1, alignment=Qt.AlignLeft)

    def on_text_step_cold_edited(self, txt):
        """Enable 'is_edit_step_cold' attribute when step cold line edit is editting"""
        self.is_edit_step_cold = False

    def on_text_step_freeze_edited(self, txt):
        """Enable 'is_edit_step_freeze' attribute when step freeze line edit is editting"""
        self.is_edit_step_freeze = False

    def handle_level_box_changed_cold(self, level_mode):
        """
        Handle set temperature level of cold cabinet when temperature combo box change
        :param level_mode: Temperature level corressponding to index of combo box
        """
        logging.info("RPC SET level temp cold: " + str(level_mode))
        self.mutex.acquire(timeout=1)
        self.client.SetColdCabinet(
            {
                'refTemperatureControl': {
                    'temperatureControl': self.temp_cold,
                    'step': self.step_cold,
                    'selectedTemperatureLevel': level_mode}})
        self.mutex.release()

    def handle_level_box_changed_freeze(self, level_mode):
        """
        Handle set temperature level of freeze cabinet when temperature combo box change
        :param level_mode: Temperature level corressponding to index of combo box
        """
        logging.info("RPC SET level temp freeze: " + str(level_mode))
        self.mutex.acquire(timeout=1)
        self.client.SetFreezeCabinet(
            {
                'refTemperatureControl': {
                    'temperatureControl': self.temp_freeze,
                    'step': self.step_freeze,
                    'selectedTemperatureLevel': level_mode}})
        self.mutex.release()

    def on_return_pressed_step_cold(self):
        """Handle set temperature step for cold cabinet when set from line edit"""
        try:
            step_cold = round(
                float(self.line_edit_step_cold.text()) * 100)
            if 0 <= step_cold <= 10000:
                self.is_edit_step_cold = True
                data = {
                    'refTemperatureControl': {
                        'temperatureControl': self.temp_cold,
                        'step': step_cold,
                        'selectedTemperatureLevel': self.temp_level_cold}}
                self.client.SetColdCabinet(data)
            else:
                self.line_edit_step_cold.setText(str(self.step_cold))
        except Exception as e:
            logging.error("Error: " + str(e))

    def on_return_pressed_step_freeze(self):
        """Handle set temperature step for freeze cabinet when set from line edit"""
        try:
            step_freeze = round(
                float(self.line_edit_step_freeze.text()) * 100)
            if 0 <= step_freeze <= 10000:
                self.is_edit_step_freeze = True
                data = {
                    'refTemperatureControl': {
                        'temperatureControl': self.temp_freeze,
                        'step': step_freeze,
                        'selectedTemperatureLevel': self.temp_level_freeze}}
                self.client.SetFreezeCabinet(data)
            else:
                self.line_edit_step_freeze.setText(str(self.step_freeze))
        except Exception as e:
            logging.error("Error: " + str(e))

    def clear_layout_cold(self):
        """Destroy all UI widget object of cold cabinet"""
        self.step_on_cold = False
        self.select_temp_level_cold = False
        while self.grid_layout_cold.count():
            layout_item = self.grid_layout_cold.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()

    def clear_layout_freeze(self):
        """Destroy all UI widget object of freeze cabinet"""
        self.step_on_freeze = False
        self.select_temp_level_freeze = False
        while self.grid_layout_freeze.count():
            layout_item = self.grid_layout_freeze.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()

    def on_text_edited_cold(self):
        """Enable 'is_edit_clod' attribute when cold line edit is editting"""
        self.is_edit_clod = False

    def on_text_edited_freeze(self):
        """Enable 'is_edit_freezer' attribute when freeze line edit is editting"""
        self.is_edit_freezer = False

    def on_return_pressed(self):
        """
        Handle set temperature measurement for cold or
        freeze cabinet when set from line edit
        """
        try:
            value_cold = round(float(self.line_edit_cold.text()) * 100)
            value_freezer = round(
                float(self.line_edit_freezer.text()) * 100)

            if 0 <= value_cold <= 2500:
                data = {
                    "refTemperatureMeasurement": {
                        "temperatureMeasure": value_cold}}
                self.client.SetColdCabinet(data)
                self.is_edit_clod = True
            else:
                self.message_box(ER_REFRI)
                self.line_edit_cold.setText(str(self.temp_cold_sensor))

            if -2000 <= value_freezer <= 0:
                data = {
                    "refTemperatureMeasurement": {
                        "temperatureMeasure": value_freezer}}
                self.client.SetFreezeCabinet(data)
                self.is_edit_freezer = True
            else:
                self.message_box(ER_FREEZER)
                self.line_edit_freezer.setText(str(self.temp_freeze_sensor))
        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Refrigerator")
        msgBox.setText("Value out of range")
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def on_pressed_event(self):
        """
        Enable 'is_on_control' attribute when
        temperature slider of cold or freeze change"""
        self.is_on_control = True

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data_1 = {
                "refrigeratorMode": {"currentMode": 0},
                "refrigeratorAlarmFeature": {"featureMap": 1},
                "refrigeratorAlarm": {"alarm": True}}
            data_2 = {
                'coldTempControlFeature': {
                    'featureMap': 0},
                "refTemperatureControl": {
                    "temperatureControl": 545,
                    'step': 100,
                    'selectedTemperatureLevel': 0},
                "refTemperatureMeasurement": {
                    "temperatureMeasure": 211}}
            data_3 = {
                'freezeTempControlFeature': {
                    'featureMap': 0},
                "refTemperatureControl": {
                    "temperatureControl": -1555,
                    'step': 100,
                    'selectedTemperatureLevel': 0},
                "refTemperatureMeasurement": {
                    "temperatureMeasure": -524}}
            self.client.SetRefrigerator(data_1)
            self.client.SetColdCabinet(data_2)
            self.client.SetFreezeCabinet(data_3)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def handle_mode_changed(self, mode):
        """
        Handle Refrigerator mode change
        :param mode {int}: A new mode of Refrigerator mode
        """
        logging.info("RPC SET Refrigerator Mode: " + str(mode))
        system_mode = self.mod_box.currentIndex()
        self.mutex.acquire(timeout=1)
        self.client.SetRefrigerator(
            {"refrigeratorMode": {"currentMode": system_mode}})
        self.mutex.release()
        self.is_on_control = False

    def update_lb_cold(self, value):
        """
        Update temperature value for temperature label of cold cabinet
        :param value: Value of temperature slider
        """
        self.lb_cold_value.setText(str(round(value / 100.0, 2)) + "°C")

    def update_lb_freezer(self, value):
        """
        Update temperature value for temperature label of freeze cabinet
        :param value: Value of temperature slider
        """
        self.lb_freezer_value.setText(str(round(value / 100.0, 2)) + "°C")

    def dimming_freezer(self):
        """
        Handle set temperature value of freeze cabinet to matter device(backend)
        through rpc service when temperature slider change
        """
        level = self.sl_freezer_level.value()
        logging.info("RPC SET Freezer Temp level: " + str(level))
        self.mutex.acquire(timeout=1)
        data = {
            "refTemperatureControl": {
                "temperatureControl": level,
                'step': self.step_freeze,
                'selectedTemperatureLevel': self.temp_level_freeze}}
        self.client.SetFreezeCabinet(data)
        self.mutex.release()
        self.is_on_control = False

    def dimming_cold(self):
        """
        Handle set temperature value of cold cabinet to matter device(backend)
        through rpc service when temperature slider change
        """
        level = self.sl_cold_level.value()
        logging.info("RPC SET Cold cabinet Temp level: " + str(level))
        self.mutex.acquire(timeout=1)
        data = {
            "refTemperatureControl": {
                "temperatureControl": level,
                'step': self.step_cold,
                'selectedTemperatureLevel': self.temp_level_cold}}
        self.client.SetColdCabinet(data)
        self.mutex.release()
        self.is_on_control = False

    def on_device_status_changed(self, result):
        """
        Interval update all attributes value
        to UI through rpc service
        :param result {dict}: Data get all attributes value
        from matter device(backend) from rpc service
        """
        # logging.info(f'on_device_status_changed {result}, RPC Port: {str(self.parent.rpcPort)}')
        try:
            device_refri_status = result['device_refri_status']
            device_cold_status = result['device_cold_status']
            device_free_status = result['device_free_status']
            device_state = result['device_state']

            if device_refri_status['status'] == 'OK':
                if (self.system_mode !=
                        device_refri_status['reply']['refrigeratorMode']['currentMode']):
                    self.system_mode = device_refri_status['reply']['refrigeratorMode']['currentMode']
                    self.mod_box.setCurrentIndex(self.system_mode)

                if (self.alarm_state !=
                        device_refri_status['reply']['refrigeratorAlarm']['alarm']):
                    self.alarm_state = device_refri_status['reply']['refrigeratorAlarm']['alarm']
                    self.alarm_state_box.setCurrentIndex(self.alarm_state)

                # if(self.alarm_feature != device_refri_status['reply']['refrigeratorAlarmFeature']['featureMap']):
                #     self.alarm_feature = device_refri_status['reply']['refrigeratorAlarmFeature']['featureMap']
                #     self.alarm_feature_box.setCurrentIndex(self.alarm_feature)

            if device_cold_status['status'] == 'OK':
                self.temp_cold = device_cold_status['reply']['refTemperatureControl']['temperatureControl']

                self.step_cold = (
                    device_cold_status['reply']['refTemperatureControl']['step'])

                if self.temp_level_cold != (
                        device_cold_status['reply']['refTemperatureControl']['selectedTemperatureLevel']):
                    self.temp_level_cold = (
                        device_cold_status['reply']['refTemperatureControl']['selectedTemperatureLevel'])
                    if (self.select_temp_level_cold and (
                            self.level_box_cold is not None)):
                        self.level_box_cold.setCurrentIndex(
                            self.temp_level_cold)

                if self.number_temp_cold:
                    self.sl_cold_level.setValue(self.temp_cold)
                if self.step_on_cold:
                    self.sl_cold_level.setValue(self.temp_cold)
                    if self.is_edit_step_cold:
                        self.line_edit_step_cold.setText(
                            str(round(self.step_cold / 100)))
                        self.sl_cold_level.setSingleStep(self.step_cold / 100)

                self.temp_cold_sensor = round(
                    float(
                        device_cold_status['reply']['refTemperatureMeasurement']['temperatureMeasure'] /
                        100),
                    2)
                if self.is_edit_clod:
                    self.line_edit_cold.setText(str(self.temp_cold_sensor))

                if (self.cold_temp_feature !=
                        device_cold_status['reply']['coldTempControlFeature']['featureMap']):
                    self.cold_temp_feature = device_cold_status['reply']['coldTempControlFeature']['featureMap']
                    self.cold_tem_control_box.setCurrentIndex(
                        self.cold_temp_feature)

            if device_free_status['status'] == 'OK':
                self.temp_freeze = device_free_status['reply']['refTemperatureControl']['temperatureControl']
                self.step_freeze = (
                    device_free_status['reply']['refTemperatureControl']['step'])

                if self.temp_level_freeze != (
                        device_free_status['reply']['refTemperatureControl']['selectedTemperatureLevel']):
                    self.temp_level_freeze = (
                        device_free_status['reply']['refTemperatureControl']['selectedTemperatureLevel'])
                    if (self.select_temp_level_freeze and (
                            self.level_box_freeze is not None)):
                        self.level_box_freeze.setCurrentIndex(
                            self.temp_level_freeze)

                if self.number_temp_freeze:
                    self.sl_freezer_level.setValue(self.temp_freeze)

                if self.step_on_freeze:
                    self.sl_freezer_level.setValue(self.temp_freeze)
                    if self.is_edit_step_freeze:
                        self.line_edit_step_freeze.setText(
                            str(round(self.step_freeze / 100)))
                        self.sl_freezer_level.setSingleStep(
                            self.step_freeze / 100)

                self.temp_freeze_sensor = round(
                    float(
                        device_free_status['reply']['refTemperatureMeasurement']['temperatureMeasure'] /
                        100), 2)
                if self.is_edit_freezer:
                    self.line_edit_freezer.setText(
                        str(self.temp_freeze_sensor))

                if (self.free_temp_feature !=
                        device_free_status['reply']['freezeTempControlFeature']['featureMap']):
                    self.free_temp_feature = device_free_status['reply'][
                        'freezeTempControlFeature']['featureMap']
                    self.freeze_tem_control_box.setCurrentIndex(
                        self.free_temp_feature)

            self.parent.update_device_state(device_state)
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
                    if not self.is_on_control:
                        self.mutex.acquire(timeout=1)
                        device_refri_status = self.client.GetRefrigerator()
                        device_cold_status = self.client.GetColdCabinet()
                        device_free_status = self.client.GetFreezeCabinet()
                        device_state = self.client.get_device_state()
                        self.mutex.release()
                        self.sig_device_status_changed.emit(
                            {
                                'device_refri_status': device_refri_status,
                                'device_cold_status': device_cold_status,
                                'device_free_status': device_free_status,
                                'device_state': device_state})
                    time.sleep(0.5)
                except Exception as e:
                    logging.error(
                        f'{str(e)} , RPC Port: {str(self.parent.rpcPort)}')
        except Exception as e:
            logging.error(str(e))

    def stop(self):
        """
        Stop thread update device state
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
