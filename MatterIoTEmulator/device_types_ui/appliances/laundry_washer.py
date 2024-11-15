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
import random
import time
from rpc.laundrywasher_client import LaundryWasherClient
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

WASHING = 0
RINSING = 1
SPINNING = 2
COOLING = 3

STOPPED = 0
RUNNING = 1
PAUSED = 2
ERROR = 3

STOP = 0
START = 1
PAUSE = 2
RESUME = 3

OFF = 0
LOW = 1
MEDIUM = 2
HIGH = 3

NORMAL = 0
DELICATE = 1
HEAVY = 2
WHITES = 3

SPIN_FEATURE = 0
RINSE_FEATURE = 1

TEMP_NUMBER_FEATURE = 0
TEMP_LEVEL_FEATURE = 1
TEMP_STEP_FEATURE = 2

NONE = 0
NORMAL = 1
EXTRA = 2
MAX = 3


class LaundryWasher(BaseDeviceUI):
    """
    LaundryWasher device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `LaundryWasher` UI.
        :param parent: An UI object load LaundryWasher device UI controller.
        """
        super().__init__(parent)
        self.cr_mode = WHITES
        self.cr_state = STOPPED
        self.cr_phase = COOLING
        self.cr_speed = MEDIUM
        self.cr_error_state = NO_ERROR
        self.cr_opState_index = STOP
        self.temperature = 0
        self.cr_step = 100
        self.select_temp = 0
        self.on_off = False
        self.remain_time = 0
        self.countdown_time = 0
        self.single_step_slide = 1

        self.crFeature_tem_control = 0
        self.crFeature_laun_mode = 0
        self.crRinse_control = 0

        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'Laundry washer.png')
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

        # Display current phase
        self.lbl_oper_status = QLabel()
        self.lbl_oper_status.setText('Current Phase : Washing')
        self.lbl_oper_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_oper_status)

        # Feature Temperature Control
        self.lbl_tem_feature = QLabel()
        self.lbl_tem_feature.setText('Temperature Control Feature')
        self.parent.ui.lo_controller.addWidget(self.lbl_tem_feature)
        # Create a fan control mode
        tem_control_list = [
            "Temperature Number",
            "Temperature Level",
            "Temperature Step"]
        self.tem_control_box = QComboBox()
        self.tem_control_box.addItems(tem_control_list)
        # Connect the currentIndexChanged signal to a slot
        self.tem_control_box.currentIndexChanged.connect(
            self.handle_temp_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.tem_control_box)

        # Add feature temperature layout
        self.grid_layout_feature_tem = QGridLayout()
        self.grid_layout_feature_tem.addWidget(self.lbl_tem_feature, 0, 0)
        self.grid_layout_feature_tem.addWidget(self.tem_control_box, 0, 1)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_feature_tem)

        # Temperature
        self.sl_title = QLabel()
        self.sl_title.setText('Temperature')
        self.parent.ui.lo_controller.addWidget(self.sl_title)
        self.lb_level = QLabel()
        self.lb_level.setText('°C')
        self.lb_level.setAlignment(Qt.AlignRight)

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

        # Feature for spin and rinse
        self.lbl_feature_mod = QLabel()
        self.lbl_feature_mod.setText('Laundry Control Feature')
        self.parent.ui.lo_controller.addWidget(self.lbl_feature_mod)

        feature_list = ["Spin", "Rinse"]
        self.feature_box = QComboBox()
        self.feature_box.addItems(feature_list)
        # Connect the currentIndexChanged signal to a slot
        self.feature_box.currentIndexChanged.connect(
            self.handle_feature_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.feature_box)

        # Spin Speed Control
        self.lbl_spin_speeds_mod = QLabel()
        self.lbl_spin_speeds_mod.setText('Spin Speed Control')
        self.parent.ui.lo_controller.addWidget(self.lbl_spin_speeds_mod)
        # Create spin speed mode
        spin_speeds_list = ["OFF", "LOW", "MEDIUM", "HIGH"]
        self.spin_speeds_box = QComboBox()
        self.spin_speeds_box.addItems(spin_speeds_list)
        # Connect the currentIndexChanged signal to a slot
        self.spin_speeds_box.currentIndexChanged.connect(
            self.handle_spin_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.spin_speeds_box)

        # Rise Control
        self.lbl_rinse_mod = QLabel()
        self.lbl_rinse_mod.setText('Rinse Control')
        self.parent.ui.lo_controller.addWidget(self.lbl_rinse_mod)
        # Create a rise mode
        rinse_list = ["None", "Normal", "Extra", "Max"]
        self.rinse_box = QComboBox()
        self.rinse_box.addItems(rinse_list)
        # Connect the currentIndexChanged signal to a slot
        self.rinse_box.setCurrentIndex(3)
        self.rinse_box.currentIndexChanged.connect(self.handle_rinse_changed)
        self.parent.ui.lo_controller.addWidget(self.rinse_box)

        # Show control button/switch
        self.parent.ui.lo_controller.addWidget(QLabel(''))
        self.sw_title = QLabel()
        self.sw_title.setText('Off/On')
        self.parent.ui.lo_controller.addWidget(self.sw_title)
        self.sw = Toggle()
        self.sw.setFixedSize(60, 40)
        self.sw.stateChanged.connect(self.handle_onoff_changed)
        self.parent.ui.lo_controller.addWidget(self.sw)

        # Create a Laundry mode
        self.lbl_mod = QLabel()
        self.lbl_mod.setText('Laundry Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_mod)
        mod_list = ["Normal", "Delicate", "Heavy", "Whites"]
        self.mod_box = QComboBox()
        self.mod_box.addItems(mod_list)
        # Connect the currentIndexChanged signal to a slot
        self.mod_box.currentIndexChanged.connect(
            self.handle_washer_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.mod_box)

        # Operational state
        self.lbl_operational_mod = QLabel()
        self.lbl_operational_mod.setText('OperationalMode')
        self.parent.ui.lo_controller.addWidget(self.lbl_operational_mod)
        # Operation list
        operational_list = ["Stop", "Start", "Pause", "Resume"]
        self.operational_box = QComboBox()
        self.operational_box.addItems(operational_list)
        # Connect the currentIndexChanged signal to a slot
        self.operational_box.currentIndexChanged.connect(
            self.handle_operational_changed)
        self.parent.ui.lo_controller.addWidget(self.operational_box)

        self.grid_layout_feature_mode = QGridLayout()
        self.grid_layout_feature_mode.addWidget(self.lbl_feature_mod, 3, 0)
        self.grid_layout_feature_mode.addWidget(self.feature_box, 3, 1)

        self.grid_layout_feature_mode.addWidget(self.lbl_spin_speeds_mod, 4, 0)
        self.grid_layout_feature_mode.addWidget(self.spin_speeds_box, 4, 1)
        self.grid_layout_feature_mode.addWidget(self.lbl_rinse_mod, 5, 0)
        self.grid_layout_feature_mode.addWidget(self.rinse_box, 5, 1)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_feature_mode)

        self.grid_layout_operation_mode = QGridLayout()
        self.grid_layout_operation_mode.addWidget(self.sw_title)
        self.grid_layout_operation_mode.addWidget(self.sw)
        self.grid_layout_operation_mode.addWidget(self.lbl_mod, 2, 0)
        self.grid_layout_operation_mode.addWidget(self.mod_box, 2, 1)
        self.grid_layout_operation_mode.addWidget(
            self.lbl_operational_mod, 4, 0)
        self.grid_layout_operation_mode.addWidget(self.operational_box, 4, 1)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_operation_mode)

        # Error state
        self.lbl_error_status = QLabel()
        self.lbl_error_status.setText('Error state : No Error')
        self.parent.ui.lo_controller.addWidget(self.lbl_error_status)

        # Label time process operation
        self.lbl_time = QLabel()
        self.lbl_time.setText('')
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_time)
        #
        self.is_run = False
        self.get_timer_mode()
        self.time_repeat = 10
        self.time_sleep = 0
        self.is_stop_clicked = False
        self.is_edit = True
        self.step_on = False
        self.select_temp_level = False
        self.number_temp = True

        # Init rpc
        self.client = LaundryWasherClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

    def handle_feature_mode_changed(self, mode):
        """
        Handle display UI when laundry control feature map change
        :param feature_mode: Value feature map of laundry control cluster
        """
        logging.info("RPC SET Laundry control feature mode: " + str(mode))
        self.client.set({'laundryControlFeature': {
                        'laundryControlFeature': mode}})
        self.mutex.acquire(timeout=1)
        if mode == SPIN_FEATURE:
            self.spin_speeds_box.setEnabled(True)
            self.rinse_box.setEnabled(False)
        else:
            self.spin_speeds_box.setEnabled(False)
            self.rinse_box.setEnabled(True)
        self.mutex.release()

    def handle_temp_feature_changed(self, feature_mode):
        """
        Handle display UI when temperature control feature map change
        :param feature_mode: Value feature map of temperature control cluster
        """
        self.clear_layout()
        self.step_on = False
        self.number_temp = False
        self.select_temp_level = False
        self.mutex.acquire(timeout=1)
        self.client.set({'tempControlFeature': {'tempFeature': feature_mode}})
        self.mutex.release()
        if feature_mode == TEMP_NUMBER_FEATURE:
            self.number_temp = True
            self.sl_title = QLabel()
            self.sl_title.setText('Temperature')
            self.lb_level = QLabel()
            self.lb_level.setText('°C')

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
            cr_step_value = round(int(self.line_edit_step.text()) * 100)
            if 0 <= cr_step_value <= 10000:
                data = {
                    'temperatureControl': {
                        'temperatureValue': self.temperature,
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

    def handle_rinse_changed(self, rinse_mode):
        """
        Handle set number of rinse when rinse combo box change
        :param rinse_mode: Number of rinse value corressponding to index of combo box
        """
        logging.info("RPC SET number of Rinse: " + str(rinse_mode))
        self.mutex.acquire(timeout=1)
        self.client.set({'numberOfRinses': {'numberOfRinses': rinse_mode}})
        self.mutex.release()

    def handle_level_box_changed(self, level_mode):
        """
        Handle set temperature level when temperature combo box change
        :param level_mode: Temperature level corressponding to index of combo box
        """
        logging.info("RPC SET temp level: " + str(level_mode))
        self.mutex.acquire(timeout=1)
        self.client.set(
            {
                'temperatureControl': {
                    'temperatureValue': self.temperature,
                    'step': self.cr_step,
                    'selectedTemperatureLevel': level_mode}})
        self.mutex.release()

    def destroy_timer_laundry(self):
        """Destroy laundrywasher timer object"""
        dict_data = self.__dict__
        if ("laundry_timer" in dict_data):
            if (self.laundry_timer is not None):
                self.laundry_timer.stop()
                self.laundry_timer = None

    def setup_timer(self, countdown_time):
        """
        Instance laundrywasher timer object, start timer,
        set countdown time and connect to handler function when timer timout
        :param countdown_time: The countdown time corressponding to each laundrywasher mode
        """
        self.laundry_timer = QTimer(self)
        if self.is_run:
            self.laundry_timer.start(1000)
            self.laundry_timer.timeout.connect(self.update_timer)
            self.countdown_time = countdown_time


    def get_timer_mode(self):
        """Set timer interval corressponding to laundrywasher mode"""
        if self.mod_box.currentIndex() == NORMAL:
            self.time_washing = 30
            self.time_rinsing = 25
            self.time_spining = 10
            self.time_cooling = 5
        elif self.mod_box.currentIndex() == DELICATE:
            self.time_washing = 30
            self.time_rinsing = 20
            self.time_spining = 15
            self.time_cooling = 10
        elif self.mod_box.currentIndex() == HEAVY:
            self.time_washing = 40
            self.time_rinsing = 30
            self.time_spining = 20
            self.time_cooling = 10
        elif self.mod_box.currentIndex() == WHITES:
            self.time_washing = 35
            self.time_rinsing = 20
            self.time_spining = 10
            self.time_cooling = 5

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
                'laundryOperationalState': {
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
            self.destroy_timer_laundry()
            self.lbl_time.setText('...Process Done...')
            self.set_operational_state(cr_opState_index=STOP, cr_phase=COOLING)

        elif self.time_rinsing < self.countdown_time <= self.time_washing:
            if self.countdown_time == self.time_washing:
                self.set_operational_state(cr_phase=WASHING)

        elif self.time_spining < self.countdown_time <= self.time_rinsing:
            if self.countdown_time == self.time_rinsing:
                self.set_operational_state(cr_phase=RINSING)

        elif self.time_cooling < self.countdown_time <= self.time_spining:
            if self.countdown_time == self.time_spining:
                self.set_operational_state(cr_phase=SPINNING)

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
        Handle laundrywasher mode change
        :param mode {int}: A new mode of laundrywasher mode
        """
        logging.info("RPC SET Laundry Washer Mode: " + str(mode))
        self.get_timer_mode()
        self.destroy_timer_laundry()
        self.mutex.acquire(timeout=1)
        self.client.set({'laundryMode': {'currentMode': mode}})
        self.mutex.release()

    def handle_spin_mode_changed(self, mode):
        """
        Handle spin speed mode change
        :param mode {int}: A new mode of spin speed mode
        """
        logging.info("RPC SET Laundry Control Spin Mode: " + str(mode))
        self.mutex.acquire(timeout=1)
        self.client.set({'spinSpeed': {'spinSpeed': mode}})
        self.mutex.release()

    def handle_operational_changed(self, mode):
        """
        Handle operational state change
        :param mode {int}: A new mode of operational state
        """
        logging.info("RPC SET Laundry Washer Operational State: " + str(mode))
        if mode == STOP:
            self.destroy_timer_laundry()
            self.countdown_time = 0
            self.set_operational_state(cr_state=STOPPED, cr_opState_index=STOP, cr_phase=COOLING)
            statusTimer = Timer(2, self.notify_process_stopped)
            statusTimer.start()

        elif mode == START:
            self.is_run = True
            self.destroy_timer_laundry()
            self.setup_timer(self.time_washing)
            self.set_operational_state(
                cr_state=RUNNING, cr_opState_index=START)

        elif mode == PAUSE:
            self.remain_time = self.countdown_time
            self.destroy_timer_laundry()
            self.is_run = False
            self.set_operational_state(cr_state=PAUSED, cr_opState_index=PAUSE)

        elif mode == RESUME:
            self.is_run = True
            if ((self.cr_error_state == NO_ERROR)
                    and (self.cr_state != STOPPED)):
                self.destroy_timer_laundry()
                self.remain_time = self.countdown_time
                self.setup_timer(self.remain_time)

            self.set_operational_state(
                cr_state=RUNNING, cr_opState_index=RESUME)

    def on_pressed_event(self):
        """Slider perssed handler"""
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
        temp = self.sl_level.value()
        self.mutex.acquire(timeout=1)
        if "On" in self.lbl_main_status.text():
            self.on_off = True
        else:
            self.on_off = False
        self.client.set(
            {
                'temperatureControl': {
                    'temperatureValue': temp,
                    'step': self.cr_step,
                    'selectedTemperatureLevel': self.select_temp},
                'onOff': {
                    'onOff': self.on_off}})
        self.is_on_control = False

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data_2 = {
                'spinSpeed': {
                    'spinSpeed': OFF},
                'laundryMode': {
                    'currentMode': DELICATE},
                'laundryModeFeature': {
                    'modeFeature': 1},
                'onOff': {
                    'onOff': True},
                'temperatureControl': {
                    'temperatureValue': 2500,
                    'step': 1,
                    'selectedTemperatureLevel': 1},
                'laundryOperationalState': {
                    'countdownTime': 0,
                    'currentPhase': WASHING,
                    'operationalState': STOPPED,
                    'crOpStateIndex': STOP,
                    'errState': NO_ERROR},
                'numberOfRinses': {
                    'numberOfRinses': MAX},
                'tempControlFeature': {
                    'tempFeature': TEMP_NUMBER_FEATURE},
                'laundryControlFeature': {
                    'laundryControlFeature': RINSE_FEATURE}}
            data_1 = {'laundryOperationalState': {'phaseList': [0, 1, 2]}}
            self.client.set(data_1)
            self.client.set(data_2)
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
            if self.crFeature_laun_mode == RINSE_FEATURE:
                self.rinse_box.setEnabled(True)
            else:
                self.spin_speeds_box.setEnabled(True)
            self.mod_box.setEnabled(True)
            self.operational_box.setEnabled(True)
            self.feature_box.setEnabled(True)
        else:
            # self.sl_level.setEnabled(False)
            self.feature_box.setEnabled(False)
            self.rinse_box.setEnabled(False)
            self.spin_speeds_box.setEnabled(False)
            self.mod_box.setEnabled(False)
            self.operational_box.setEnabled(False)
            self.destroy_timer_laundry()

            self.cr_state = STOPPED
            self.cr_opState_index = STOP
            self.cr_phase = COOLING
            self.set_operational_state()
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
                        device_status['reply']['laundryMode']['currentMode']):
                    self.cr_mode = device_status['reply']['laundryMode']['currentMode']
                    self.mod_box.setCurrentIndex(self.cr_mode)

                self.temperature = (
                    device_status['reply']['temperatureControl']['temperatureValue'])

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

                if self.on_off != device_status['reply']['onOff']['onOff']:
                    self.on_off = device_status['reply']['onOff']['onOff']
                    if self.on_off:
                        self.lbl_main_status.setText('On')
                        self.sw.setCheckState(Qt.Checked)
                    else:
                        self.lbl_main_status.setText('Off')
                        self.sw.setCheckState(Qt.Unchecked)

                if (self.cr_opState_index !=
                        device_status['reply']['laundryOperationalState']['crOpStateIndex']):
                    self.cr_opState_index = device_status['reply']['laundryOperationalState']['crOpStateIndex']
                    self.operational_box.setCurrentIndex(self.cr_opState_index)

                if (self.crFeature_tem_control !=
                        device_status['reply']['tempControlFeature']['tempFeature']):
                    self.crFeature_tem_control = device_status['reply']['tempControlFeature']['tempFeature']
                    self.tem_control_box.setCurrentIndex(
                        self.crFeature_tem_control)

                if (self.crFeature_laun_mode !=
                        device_status['reply']['laundryControlFeature']['laundryControlFeature']):
                    self.crFeature_laun_mode = device_status['reply'][
                        'laundryControlFeature']['laundryControlFeature']
                    self.feature_box.setCurrentIndex(self.crFeature_laun_mode)

                if (self.crRinse_control !=
                        device_status['reply']['numberOfRinses']['numberOfRinses']):
                    self.crRinse_control = device_status['reply']['numberOfRinses']['numberOfRinses']
                    self.rinse_box.setCurrentIndex(self.crRinse_control)

                if (self.cr_error_state !=
                        device_status['reply']['laundryOperationalState']['errState']):
                    self.cr_error_state = device_status['reply']['laundryOperationalState']['errState']
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

                if (self.cr_state != device_status['reply']
                        ['laundryOperationalState']['operationalState']):
                    self.cr_state = device_status['reply']['laundryOperationalState']['operationalState']
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

                if (self.cr_phase != device_status['reply']
                        ['laundryOperationalState']['currentPhase']):
                    self.cr_phase = device_status['reply']['laundryOperationalState']['currentPhase']
                    if self.cr_phase == WASHING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Washing "))
                    elif self.cr_phase == RINSING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Rinsing"))
                    elif self.cr_phase == SPINNING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Spinning"))
                    elif self.cr_phase == COOLING:
                        self.lbl_oper_status.setText(
                            'Current Phase : {}'.format("Cooling"))

                if (self.cr_speed != (
                        device_status['reply']['spinSpeed']['spinSpeed'])):
                    self.cr_speed = (
                        device_status['reply']['spinSpeed']['spinSpeed'])
                    if self.cr_speed == OFF:
                        self.spin_speeds_box.setCurrentIndex(OFF)
                    elif self.cr_speed == LOW:
                        self.spin_speeds_box.setCurrentIndex(LOW)
                    elif self.cr_speed == MEDIUM:
                        self.spin_speeds_box.setCurrentIndex(MEDIUM)
                    elif self.cr_speed == HIGH:
                        self.spin_speeds_box.setCurrentIndex(HIGH)
        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device state
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
