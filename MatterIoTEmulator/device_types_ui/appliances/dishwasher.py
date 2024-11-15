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
from threading import Timer
import os
import time
import random
from rpc.dishwasher_client import DishwasherClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/Appliances/")


NO_ERROR = 0
UNABLE_TO_START_OR_RESUME = 1
UNABLE_TO_COMPLETE_OPERATION = 2
COMMAND_INVALID_INSTATE = 3

STOPPED = 0
RUNNING = 1
PAUSED = 2
ERROR = 3

STOP = 0
START = 1
PAUSE = 2
RESUME = 3

NORMAL = 0
HEAVY = 1
LIGHT = 2

WASHING = 0
RINSING = 1
DRYING = 2
COOLING = 3

IN_FLOW_ERROR = 0
DRAIN_ERROR = 1
DOOR_ERROR = 2
TEMP_TOO_LOW = 3
TEMP_TOO_HIGH = 4
WATER_LEVEL_ERROR = 5
NOERROR = 6

TEMP_NUMBER_FEATURE = 0
TEMP_LEVEL_FEATURE = 1
TEMP_STEP_FEATURE = 2


class Dishwasher(BaseDeviceUI):
    """
    Dishwasher device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `Dishwasher` UI.
        :param parent: An UI object load Dishwasher device UI controller.
        """
        super().__init__(parent)
        self.cr_phase = COOLING
        self.cr_state = STOPPED
        self.cr_mode = NORMAL
        self.cr_error_state = NO_ERROR
        self.cr_opState_index = STOP
        self.cr_dishwasher_mode_feature = False
        self.cr_dishwasher_alarm_feature = False
        self.cr_dishwasher_alarm = NOERROR
        self.cr_temperature_control_feature = 0
        self.on_off = False
        self.temperature = 0
        self.remain_time = 0
        self.countdown_time = 0
        self.cr_step = 100
        self.is_edit = True
        self.step_on = False
        self.select_temp_level = False
        self.select_temp = 0
        self.number_temp = True
        self.single_step_slide = 1
        self.time_repeat = 10
        self.time_sleep = 0
        self.is_stop_clicked = False
        self.is_run = False
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'dishwasher.png')
        self.lbl_main_icon.setFixedSize(70, 70)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('On')
        self.lbl_main_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        # Label current phase
        self.lbl_oper_status = QLabel()
        self.lbl_oper_status.setText('Current Phase : Washing')
        self.lbl_oper_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_oper_status)
        self.parent.ui.lo_controller.addWidget(QLabel(" "))

        # Add Dishwasher Mode feature
        self.lbl_dish_mode_feature = QLabel()
        self.lbl_dish_mode_feature.setText('Dishwasher Mode feature')

        dishwasher_mode_feature_list = ["Disable", "OnOff"]
        self.dishwasher_mode_feature_box = QComboBox()
        self.dishwasher_mode_feature_box.addItems(dishwasher_mode_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.dishwasher_mode_feature_box.currentIndexChanged.connect(
            self.dishwasher_mode_feature_changed)

        # Add Dishwasher Alarm feature
        self.lbl_dish_alarm_feature = QLabel()
        self.lbl_dish_alarm_feature.setText('Dishwasher Alarm Feature')

        dishwasher_alarm_feature_list = ["Disable", "Reset"]
        self.dishwasher_alarm_feature_box = QComboBox()
        self.dishwasher_alarm_feature_box.addItems(
            dishwasher_alarm_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.dishwasher_alarm_feature_box.currentIndexChanged.connect(
            self.dishwasher_alarm_feature_changed)

        # Temperature control feature
        self.lbl_temp_control_feature = QLabel()
        self.lbl_temp_control_feature.setText('Temperature Control Feature')
        temperature_control_feature_list = [
            "Temperature Number",
            "Temperature Level",
            "Temperature Step"]
        self.temperature_control_feature_box = QComboBox()
        self.temperature_control_feature_box.addItems(
            temperature_control_feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.temperature_control_feature_box.currentIndexChanged.connect(
            self.temperature_control_feature_changed)

        # Label Dishwasher alarm
        self.lbl_alarm = QLabel()
        dishwasher_alarm_list = [
            'InflowError',
            'DrainError',
            'DoorError',
            'TempTooLow',
            'TempTooHigh',
            'WaterLevelError',
            'NoError']
        self.lbl_alarm.setText('Dishwasher Alarm: ')

        # Dishwasher alarm box
        self.dishwasher_alarm_box = QComboBox()
        self.dishwasher_alarm_box.addItems(dishwasher_alarm_list)
        self.dishwasher_alarm_box.setCurrentIndex(NOERROR)
        # Connect the currentIndexChanged signal to a slot
        self.dishwasher_alarm_box.currentIndexChanged.connect(
            self.dishwasher_alarm_changed)

        self.feature_layout = QGridLayout()
        # Currently, do not add dishwasher mode dep on off
        # self.feature_layout.addWidget(self.lbl_dish_mode_feature, 0, 0)
        # self.feature_layout.addWidget(self.dishwasher_mode_feature_box, 0, 1)

        # Add Dishwasher alarm feature
        self.feature_layout.addWidget(self.lbl_dish_alarm_feature, 0, 0)
        self.feature_layout.addWidget(self.dishwasher_alarm_feature_box, 0, 1)

        # Add Dishwasher alarm box
        self.feature_layout.addWidget(self.lbl_alarm)
        self.feature_layout.addWidget(self.dishwasher_alarm_box)

        # Add Dishwasher temperature control feature
        self.feature_layout.addWidget(self.lbl_temp_control_feature, 2, 0)
        self.feature_layout.addWidget(
            self.temperature_control_feature_box, 2, 1)

        self.parent.ui.lo_controller.addLayout(self.feature_layout)

        # Temperature control
        self.sl_title = QLabel()
        self.sl_title.setText('Temperature')
        self.parent.ui.lo_controller.addWidget(self.sl_title)
        self.lb_level = QLabel()
        self.lb_level.setText('°C')
        self.lb_level.setAlignment(Qt.AlignRight)
        self.parent.ui.lo_controller.addWidget(self.lb_level)

        self.sl_level = QSlider()
        self.sl_level.setRange(0, 10000)
        self.sl_level.setOrientation(Qt.Horizontal)
        self.sl_level.valueChanged.connect(self.update_lb_level)
        self.sl_level.sliderReleased.connect(self.dimming)
        self.sl_level.sliderPressed.connect(self.on_pressed_event)

        self.slide_layout = QGridLayout()
        self.slide_layout.addWidget(self.sl_title, 0, 0)
        self.slide_layout.addWidget(self.lb_level, 0, 1)
        self.slide_layout.addWidget(self.sl_level, 1, 0, 1, 2)
        self.parent.ui.lo_controller.addLayout(self.slide_layout)

        # Show control button/switch
        self.sw_title = QLabel()
        self.sw_title.setText('Off/On')
        self.parent.ui.lo_controller.addWidget(self.sw_title)
        self.sw = Toggle()
        self.sw.setFixedSize(60, 40)
        self.sw.stateChanged.connect(self.handle_onoff_changed)
        self.parent.ui.lo_controller.addWidget(self.sw)

        # Washer mode
        self.lbl_washer_mod = QLabel()
        self.lbl_washer_mod.setText('Washer Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_washer_mod)
        # Create a fan control mode
        washer_mode_list = ["Normal", "Heavy", "Light"]
        self.washer_control_box = QComboBox()
        self.washer_control_box.addItems(washer_mode_list)
        # Connect the currentIndexChanged signal to a slot
        self.washer_control_box.currentIndexChanged.connect(
            self.handle_washer_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.washer_control_box)

        # Operational state
        self.lbl_operational_mod = QLabel()
        self.lbl_operational_mod.setText('OperationalMode')
        self.parent.ui.lo_controller.addWidget(self.lbl_operational_mod)
        operational_list = ["Stop", "Start", "Pause", "Resume"]
        self.operational_box = QComboBox()
        self.operational_box.addItems(operational_list)
        # Connect the currentIndexChanged signal to a slot
        self.operational_box.currentIndexChanged.connect(
            self.handle_operational_changed)
        self.parent.ui.lo_controller.addWidget(self.operational_box)

        # Error state label
        self.lbl_error_status = QLabel()
        self.lbl_error_status.setText('Error state : No Error')
        self.parent.ui.lo_controller.addWidget(self.lbl_error_status)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Display time process operation
        self.lbl_time = QLabel()
        self.lbl_time.setText('')
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_time)

        # Init rpc
        self.client = DishwasherClient(self.config)
        self.set_initial_value()
        self.get_timer_mode()
        self.start_update_device_status_thread()

    def temperature_control_feature_changed(self, feature_mode):
        """
        Handle display UI when temperature control feature map change
        :param feature_mode: Value feature map of temperature control cluster
        """
        self.clear_layout()
        self.step_on = False
        self.number_temp = False
        self.select_temp_level = False
        self.mutex.acquire(timeout=1)
        self.client.set({'dishTempControlFeature': {
                        'tempFeature': feature_mode}})
        self.mutex.release()
        if feature_mode == TEMP_NUMBER_FEATURE:
            self.number_temp = True
            self.sl_title = QLabel()
            self.sl_title.setText('Temperature')
            self.lb_level = QLabel()
            self.lb_level.setText('°C')
            self.lb_level.setAlignment(Qt.AlignRight)

            self.sl_level = QSlider()
            self.sl_level.setRange(0, 10000)
            self.sl_level.setSingleStep(self.single_step_slide)
            self.sl_level.setOrientation(Qt.Horizontal)
            self.sl_level.valueChanged.connect(self.update_lb_level)
            self.sl_level.sliderReleased.connect(self.dimming)
            self.sl_level.sliderPressed.connect(self.on_pressed_event)

            self.slide_layout.addWidget(self.sl_title, 0, 0)
            self.slide_layout.addWidget(
                self.lb_level, 0, 1, alignment=Qt.AlignRight)
            self.slide_layout.addWidget(self.sl_level, 1, 0, 1, 2)

        elif feature_mode == TEMP_LEVEL_FEATURE:
            self.select_temp_level = True
            self.lbl_level_mod = QLabel()
            self.lbl_level_mod.setText('Temperature level')

            level_list = ["Normal", "Warm", "Hot", "Cold"]
            self.level_box = QComboBox()
            self.level_box.addItems(level_list)
            # Connect the currentIndexChanged signal to a slot
            self.level_box.currentIndexChanged.connect(
                self.handle_level_box_changed)
            self.slide_layout.addWidget(self.lbl_level_mod, 0, 0)
            self.slide_layout.addWidget(self.level_box, 0, 1)

        elif feature_mode == TEMP_STEP_FEATURE:
            self.step_on = True
            self.number_temp = True
            self.sl_title = QLabel()
            self.sl_title.setText('Temperature')
            self.lb_level = QLabel()
            self.lb_level.setText('°C')
            self.lb_level.setAlignment(Qt.AlignRight)

            self.sl_level = QSlider()
            self.sl_level.setRange(0, 10000)

            self.sl_level.setOrientation(Qt.Horizontal)
            self.sl_level.valueChanged.connect(self.update_lb_level)
            self.sl_level.sliderReleased.connect(self.dimming)
            self.sl_level.sliderPressed.connect(self.on_pressed_event)

            self.lbl_step_mod = QLabel()
            self.lbl_step_mod.setText('Temperature step:')

            self.line_edit_step = QLineEdit()
            self.line_edit_step.setValidator(self.validator)
            self.line_edit_step.setValidator(self.double_validator)
            self.line_edit_step.textEdited.connect(self.on_text_edited)
            self.line_edit_step.returnPressed.connect(self.on_return_pressed)

            self.line_edit_step.setMaximumSize(QSize(65, 20))
            self.slide_layout.addWidget(self.sl_title, 0, 0)
            self.slide_layout.addWidget(
                self.lb_level, 0, 1, alignment=Qt.AlignRight)
            self.slide_layout.addWidget(self.sl_level, 1, 0, 1, 2)

            self.slide_layout.addWidget(self.lbl_step_mod, 2, 0)
            self.slide_layout.addWidget(
                self.line_edit_step, 2, 1, 1, 1, alignment=Qt.AlignLeft)

    def on_text_edited(self):
        """Enable 'is_edit' attribute when line edit is editting"""
        self.is_edit = False

    def on_return_pressed(self):
        """Handle set temperature step when set from line edit"""
        try:
            cr_step_value = round(float(self.line_edit_step.text()) * 100)
            if 0 <= cr_step_value <= 10000:
                data = {
                    'temperatureControl': {
                        'temperatureSetpoint': self.temperature,
                        'step': cr_step_value,
                        'selectedTemperatureLevel': self.select_temp}}
                self.client.set(data)
                self.is_edit = True
            else:
                self.line_edit_step.setText(str(self.cr_step))
        except Exception as e:
            logging.error("Error: " + str(e))

    def clear_layout(self):
        """Destroy all UI widget object"""
        self.step_on = False
        self.select_temp_level = False
        while self.slide_layout.count():
            layout_item = self.slide_layout.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()

    def handle_level_box_changed(self, level_mode):
        """
        Handle set temperature level when temperature combo box change
        :param level_mode: Temperature level corressponding to index of combo box
        """
        logging.info("RPC SET Temperature level change: " + str(level_mode))
        self.mutex.acquire(timeout=1)
        self.client.set(
            {
                'temperatureControl': {
                    'temperatureSetpoint': self.temperature,
                    'step': self.cr_step,
                    'selectedTemperatureLevel': level_mode}})
        self.mutex.release()

    def destroy_timer_dishwasher(self):
        """Destroy dishwasher timer object"""
        dict_data = self.__dict__
        if ("dishwasher_timer" in dict_data):
            if (self.dishwasher_timer is not None):
                self.dishwasher_timer.stop()
                self.dishwasher_timer = None

    def setup_timer(self, countdown_time):
        """
        Instance dishwasher timer object, start timer,
        set countdown time and connect to handler function when timer timout
        :param countdown_time: The countdown time corressponding to each dishwasher mode
        """
        self.dishwasher_timer = QTimer(self)
        if self.is_run:
            self.dishwasher_timer.start(1000)
            self.dishwasher_timer.timeout.connect(self.update_timer)
            self.countdown_time = countdown_time

    def get_timer_mode(self):
        """Set timer interval corressponding to dishwasher mode"""
        if self.washer_control_box.currentIndex() == NORMAL:
            self.time_washing = 60
            self.time_rinsing = 40
            self.time_drying = 20
            self.time_cooling = 10
        elif self.washer_control_box.currentIndex() == HEAVY:
            self.time_washing = 70
            self.time_rinsing = 45
            self.time_drying = 25
            self.time_cooling = 10
        elif self.washer_control_box.currentIndex() == LIGHT:
            self.time_washing = 80
            self.time_rinsing = 60
            self.time_drying = 35
            self.time_cooling = 20

    def set_operational_state(self,
                              cr_state=None,
                              cr_opState_index=None,
                              cr_phase=None,
                              cr_error_state=None,
                              cr_countdown_time=None):
        """
        Set value for all attributes of operational state cluster
        :param cr_state: New value of operation state attribute
        :param cr_opState_index: New value of operation state index of combo box
        :param cr_phase: New value of current phase attribute
        :param cr_error_state: New value of operation state error attribute
        """
        self.mutex.acquire(timeout=1)
        self.client.set(
            {
                'operationalState': {
                    'operationalState': cr_state if cr_state is not None else self.cr_state,
                    'currentPhase': cr_phase if cr_phase is not None else self.cr_phase,
                    'crOpStateIndex': cr_opState_index if cr_opState_index is not None else self.cr_opState_index,
                    'errState': cr_error_state if cr_error_state is not None else self.cr_error_state,
                    'countdownTime': cr_countdown_time if cr_countdown_time is not None else self.countdown_time}})
        self.mutex.release()

    def update_timer(self):
        """
        Handle set attributes value to matter device(backend)
        through rpc service when timer timout
        """
        self.set_operational_state()
        self.lbl_time.setText(
            "In processing...{}s".format(
                self.countdown_time))
        if self.countdown_time <= 0:
            self.destroy_timer_dishwasher()
            self.lbl_time.setText('...Process Done...')
            self.set_operational_state(cr_opState_index=STOP, cr_phase=COOLING)

        elif self.time_rinsing < self.countdown_time <= self.time_washing:
            if self.countdown_time == self.time_washing:
                self.set_operational_state(cr_phase=WASHING)

        elif self.time_drying < self.countdown_time <= self.time_rinsing:
            if self.countdown_time == self.time_rinsing:
                self.set_operational_state(cr_phase=RINSING)

        elif self.time_cooling < self.countdown_time <= self.time_drying:
            if self.countdown_time == self.time_drying:
                self.set_operational_state(cr_phase=DRYING)

        elif 0 < self.countdown_time <= self.time_cooling:
            if self.countdown_time == self.time_cooling:
                self.set_operational_state(cr_phase=COOLING)

        if self.countdown_time > 0:
            self.countdown_time-= 1

    def notify_process_stopped(self):
        """Set label to notice process stopped"""
        self.lbl_time.setText("...Process stopped...")

    def handle_washer_mode_changed(self, mode):
        """
        Handle dishwasher mode change
        :param mode {int}: A new mode of dishwasher mode
        """
        logging.info("RPC SET DishWasher Mode: " + str(mode))
        self.get_timer_mode()
        self.destroy_timer_dishwasher()
        self.mutex.acquire(timeout=1)
        self.client.set({'dishwasherMode': {'currentMode': mode}})
        self.mutex.release()

    def handle_operational_changed(self, mode):
        """
        Handle operational state change
        :param mode {int}: A new mode of operational state
        """
        logging.info("RPC SET DishWasher Operational state: " + str(mode))
        if mode == STOP:
            self.destroy_timer_dishwasher()
            self.countdown_time = 0
            self.set_operational_state(cr_state=STOPPED, cr_opState_index=STOP, cr_phase=COOLING)
            statusTimer = Timer(2, self.notify_process_stopped)
            statusTimer.start()

        elif mode == START:
            self.is_run = True
            self.destroy_timer_dishwasher()
            self.setup_timer(self.time_washing)
            self.set_operational_state(
                cr_state=RUNNING, cr_opState_index=START)

        elif mode == PAUSE:
            self.remain_time = self.countdown_time
            self.destroy_timer_dishwasher()
            self.is_run = False
            self.set_operational_state(cr_state=PAUSED, cr_opState_index=PAUSE)

        elif mode == RESUME:
            self.is_run = True
            if ((self.cr_error_state == NO_ERROR)
                    and (self.cr_state != STOPPED)):
                self.destroy_timer_dishwasher()
                self.remain_time = self.countdown_time
                self.setup_timer(self.remain_time)
            self.set_operational_state(
                cr_state=RUNNING, cr_opState_index=RESUME)

    def dishwasher_mode_feature_changed(self, mode):
        """
        Dishwasher mode feature changed handler
        :param mode {int}: A new mode of dishwasher feature mode
        """
        logging.info("RPC SET Dishwasher mode feature: " + str(mode))
        self.mutex.acquire(timeout=1)
        self.client.set(
            {'dishDepOnOffFeature': {'featureMapOnOff': True if mode == 1 else False}})
        self.mutex.release()

    def dishwasher_alarm_feature_changed(self, mode):
        """
        Dishwasher alarm feature changed handler
        :param mode {int}: A new alarm feature mode of dishwasher alarm feature map
        """
        logging.info("RPC SET Dishwasher alarm feature: " + str(mode))
        self.mutex.acquire(timeout=1)
        self.client.set({'dishwasherAlarmReset': {
            'featureMapReset': True if mode == 1 else False}})
        self.mutex.release()

    def dishwasher_alarm_changed(self, mode):
        """
        Dishwasher alarm changed handler
        :param mode {int}: A new alarm mode of dishwasher alarm
        """
        logging.info("RPC SET Dishwasher alarm: " + str(mode))
        self.mutex.acquire(timeout=1)
        self.client.set({'dishwasherAlarm': {'alarmState': mode}})
        self.mutex.release()

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def update_lb_level(self, value):
        """
        Update temperature value for temperature label
        :param value: Value of temperature slider
        """
        self.lb_level.setText(str(round(value / 100.0, 2)) + "°C")

    def dimming(self):
        """
        Handle set temperature value to matter device(backend)
        through rpc service when temperature slider change
        """
        temp = (self.sl_level.value())
        logging.info("RPC SET Temperature number: " + str(temp))
        self.mutex.acquire(timeout=1)
        if "On" in self.lbl_main_status.text():
            self.on_off = True
        else:
            self.on_off = False

        self.client.set(
            {
                'temperatureControl': {
                    'temperatureSetpoint': temp,
                    'step': self.cr_step,
                    'selectedTemperatureLevel': self.select_temp},
                'onOff': {
                    'onOff': self.on_off}})
        self.mutex.release()
        self.is_on_control = False

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'dishTempControlFeature': {
                    'tempFeature': TEMP_NUMBER_FEATURE},
                'temperatureControl': {
                    'temperatureSetpoint': 5015,
                    'step': 100,
                    'selectedTemperatureLevel': 0},
                'dishwasherAlarm': {
                    'alarmState': NOERROR},
                'dishwasherMode': {
                    'currentMode': NORMAL},
                'onOff': {
                    'onOff': True},
                'operationalState': {
                    'countdownTime': 0,
                    'currentPhase': WASHING,
                    'operationalState': STOPPED,
                    'crOpStateIndex': STOP,
                    'errState': NO_ERROR}}
            data_1 = {'operationalState': {'phaseList': [0, 1, 2]}}
            self.client.set(data_1)
            self.client.set(data)
            self.lbl_operational_mod.setText('Operational State : Stopped')
            self.lbl_error_status.setText('Error state : No Error')
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def check_onoff(self, is_On):
        """
        Handle disable or enable feature on UI
        when on/off attribute change
        :param is_On: Value of on-off attribute, 0: False, other True
        """
        if is_On:
            # self.sl_level.setEnabled(True)
            self.washer_control_box.setEnabled(True)
            self.operational_box.setEnabled(True)
        else:
            # self.sl_level.setEnabled(False)
            self.washer_control_box.setEnabled(False)
            self.operational_box.setEnabled(False)
            self.destroy_timer_dishwasher()
            self.client.set(
                {
                    'operationalState': {
                        'countdownTime': 0,
                        'operationalState': STOPPED,
                        'currentPhase': RINSING,
                        'crOpStateIndex': STOP,
                        'errState': NO_ERROR}})
            self.lbl_time.setText("...Process stopped...")

    def handle_onoff_changed(self, data):
        """
        Handle set on off attribute to matter device(backend)
        through rpc service when on/off toggle
        :param data: Value of on-off attribute, 0: False, other True
        """
        logging.info("RPC SET On/Off: " + str(data))
        self.mutex.acquire(timeout=1)
        if data == 0:
            self.client.set({'onOff': {'onOff': False}})
            self.check_onoff(False)
        else:
            self.client.set({'onOff': {'onOff': True}})
            self.check_onoff(True)
        self.mutex.release()

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

                if (self.cr_mode !=
                        device_status['reply']['dishwasherMode']['currentMode']):
                    self.cr_mode = device_status['reply']['dishwasherMode']['currentMode']
                    self.washer_control_box.setCurrentIndex(self.cr_mode)

                if (self.cr_state != device_status['reply']
                        ['operationalState']['operationalState']):
                    self.cr_state = device_status['reply']['operationalState']['operationalState']
                    if self.cr_state == STOPPED:
                        self.lbl_operational_mod.setText(
                            'Operational State : Stopped')
                    elif self.cr_state == RUNNING:
                        self.lbl_operational_mod.setText(
                            'Operational State : Running')
                    elif self.cr_state == PAUSED:
                        self.lbl_operational_mod.setText(
                            'Operational State : Paused')
                    elif self.cr_state == ERROR:
                        self.lbl_operational_mod.setText(
                            'Operational State : Error')

                if (self.cr_error_state !=
                        device_status['reply']['operationalState']['errState']):
                    self.cr_error_state = device_status['reply']['operationalState']['errState']
                    if self.cr_error_state == NO_ERROR:
                        self.lbl_error_status.setText('Error state : No Error')
                    elif self.cr_error_state == UNABLE_TO_START_OR_RESUME:
                        self.lbl_error_status.setText(
                            'Error state : UnableToStartOrResume')
                    elif self.cr_error_state == UNABLE_TO_COMPLETE_OPERATION:
                        self.lbl_error_status.setText(
                            'Error state : UnableToCompleteOperation')
                    elif self.cr_error_state == COMMAND_INVALID_INSTATE:
                        self.lbl_error_status.setText(
                            'Error state : CommandInvalidInState')

                if self.on_off != device_status['reply']['onOff']['onOff']:
                    self.on_off = device_status['reply']['onOff']['onOff']
                    if self.on_off:
                        self.lbl_main_status.setText('On')
                        self.sw.setCheckState(Qt.Checked)
                    else:
                        self.lbl_main_status.setText('Off')
                        self.sw.setCheckState(Qt.Unchecked)

                if (self.temperature != (
                        device_status['reply']['temperatureControl']['temperatureSetpoint'])):
                    self.temperature = (
                        device_status['reply']['temperatureControl']['temperatureSetpoint'])
                    self.sl_level.setValue(self.temperature)

                if (self.cr_step != (
                        device_status['reply']['temperatureControl']['step'])):
                    self.cr_step = (
                        device_status['reply']['temperatureControl']['step'])

                if (self.select_temp != (
                        device_status['reply']['temperatureControl']['selectedTemperatureLevel'])):
                    self.select_temp = (
                        device_status['reply']['temperatureControl']['selectedTemperatureLevel'])

                if self.number_temp:
                    self.sl_level.setValue(self.temperature)
                if self.select_temp_level:
                    self.level_box.setCurrentIndex(self.select_temp)
                if self.step_on:
                    self.sl_level.setValue(self.temperature)
                    if self.is_edit:
                        self.line_edit_step.setText(
                            str(round(self.cr_step / 100)))
                        self.sl_level.setSingleStep(self.cr_step / 100)

                if (self.cr_opState_index !=
                        device_status['reply']['operationalState']['crOpStateIndex']):
                    self.cr_opState_index = device_status['reply']['operationalState']['crOpStateIndex']
                    self.operational_box.setCurrentIndex(self.cr_opState_index)

                if (self.cr_phase !=
                        device_status['reply']['operationalState']['currentPhase']):
                    self.cr_phase = device_status['reply']['operationalState']['currentPhase']
                    if self.cr_phase == WASHING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Washing"))
                    elif self.cr_phase == RINSING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Rinsing"))
                    elif self.cr_phase == DRYING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Drying"))
                    elif self.cr_phase == COOLING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Cooling"))

                # Update feature map
                if (self.cr_dishwasher_mode_feature !=
                        device_status['reply']['dishDepOnOffFeature']['featureMapOnOff']):
                    self.cr_dishwasher_mode_feature = device_status[
                        'reply']['dishDepOnOffFeature']['featureMapOnOff']
                    self.dishwasher_mode_feature_box.setCurrentIndex(
                        int(self.cr_dishwasher_mode_feature))

                if (self.cr_dishwasher_alarm_feature !=
                        device_status['reply']['dishwasherAlarmReset']['featureMapReset']):
                    self.cr_dishwasher_alarm_feature = device_status[
                        'reply']['dishwasherAlarmReset']['featureMapReset']
                    self.dishwasher_alarm_feature_box.setCurrentIndex(
                        int(self.cr_dishwasher_alarm_feature))

                if (self.cr_dishwasher_alarm !=
                        device_status['reply']['dishwasherAlarm']['alarmState']):
                    self.cr_dishwasher_alarm = device_status['reply']['dishwasherAlarm']['alarmState']
                    self.dishwasher_alarm_box.setCurrentIndex(
                        self.cr_dishwasher_alarm)

                if (self.cr_temperature_control_feature !=
                        device_status['reply']['dishTempControlFeature']['tempFeature']):
                    self.cr_temperature_control_feature = device_status[
                        'reply']['dishTempControlFeature']['tempFeature']
                    self.temperature_control_feature_box.setCurrentIndex(
                        self.cr_temperature_control_feature)

        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device state
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
