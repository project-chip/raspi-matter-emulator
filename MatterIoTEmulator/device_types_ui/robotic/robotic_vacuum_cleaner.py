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
from rpc.robotvacuum_client import RobotVacuumClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/robotic/")


NO_ERROR = 0
UNABLE_TO_START_OR_RESUME = 1
UNABLE_TO_COMPLETE_OPERATION = 2
COMMAND_IN_VALID_INSTATE = 3
FAILED_TO_FIND_CHARGING_DOCK = 64
STUCK = 65
DUSTB_IN_MISSING = 66
DUSTB_IN_FULL = 67
WATER_TANK_EMPTY = 68
WATER_TANK_MISSING = 69
WATER_TANK_LID_OPEN = 70
MOP_CLEANING_PAD_MISSING = 71


STOPPED = 0
RUNNING = 1
PAUSED = 2
ERROR = 3
SEEKING_CHARGER = 64
CHARGING = 65
DOCKED = 66

IDLE = 0
CLEANING = 1
MAPPING = 2

QUICK = 0
AUTO = 1
DEEP_CLEAN = 2
QUIET = 3
MAXVAC = 4

CLEANING_PHASE = 0
DRYING_PHASE = 1
DOCKING_PHASE = 2
CHARGING_PHASE = 3
MAPPING_PHASE = 4

STOP = 0
START = 1
PAUSE = 2
RESUME = 3


class RobotVacuum(BaseDeviceUI):
    """
    RobotVacuum device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `RobotVacuum` UI.
        :param parent: An UI object load RobotVacuum device UI controller.
        """
        super().__init__(parent)
        self.run_mode = IDLE
        self.clean_mode = QUICK
        self.cr_State = STOPPED
        self.cr_phase = CLEANING_PHASE
        self.cr_error_state = NO_ERROR
        self.cr_opState_index = 0
        self.change_mode_status = NO_ERROR
        self.enable_update = True
        self.remain_time = 0
        self.countdown_time = 0
        self.time_repeat = 10
        self.time_sleep = 0
        self.is_stop_clicked = False
        self.docked = False
        self.charging = False

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'robot-vacuum-cleaner.png')
        self.lbl_main_icon.setFixedSize(70, 70)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # Current phase
        self.lbl_oper_status = QLabel()
        self.lbl_oper_status.setText('Current Phase : Cleaning')
        self.lbl_oper_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_oper_status)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Run mode
        self.lbl_runmode = QLabel()
        self.lbl_runmode.setText('Run Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_runmode)
        runmode_list = ["Idle", "Cleaning", "Mapping"]
        self.runmode_box = QComboBox()
        self.runmode_box.addItems(runmode_list)
        self.runmode_box.currentIndexChanged.connect(
            self.handle_run_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.runmode_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Clean mode
        self.lbl_cleanmode = QLabel()
        self.lbl_cleanmode.setText('Clean Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_cleanmode)
        cleanmode_list = ["Quick", "Auto", "Deep Clean", "Quiet", "Max Vac"]
        self.cleanmode_box = QComboBox()
        self.cleanmode_box.addItems(cleanmode_list)
        self.cleanmode_box.currentIndexChanged.connect(
            self.handle_clean_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.cleanmode_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Operational state
        self.lbl_operational_mod = QLabel()
        self.lbl_operational_mod.setText('OperationalMode')
        self.parent.ui.lo_controller.addWidget(self.lbl_operational_mod)

        operational_list = ["Stop", "Run", "Pause", "Resume"]
        self.operational_box = QComboBox()
        self.operational_box.addItems(operational_list)
        # Connect the currentIndexChanged signal to a slot
        self.operational_box.currentIndexChanged.connect(
            self.handle_operational_changed)
        self.parent.ui.lo_controller.addWidget(self.operational_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        self.lbl_error_status = QLabel()
        self.lbl_error_status.setText('Error state : No Error')
        self.lbl_error_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_error_status)

        # self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.lbl_time = QLabel()
        self.lbl_time.setText('')
        self.parent.ui.lo_controller.addWidget(self.lbl_time)

        self.lbl_error_status_mode = QLabel()
        self.lbl_error_status_mode.setText('')
        self.lbl_error_status_mode.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_error_status_mode)

        # Init rpc
        self.client = RobotVacuumClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

    def set_crphase_drying(self):
        """Set current phase attribute to DRYING_PHASE"""
        self.cr_phase = DRYING_PHASE
        self.client.set({'rvcOpStatePhase': {'currentPhase': self.cr_phase}})

    def destroy_timer_cleaning(self):
        """Destroy timer object of cleaning run mode"""
        dict_data = self.__dict__
        if ('timer_cleaning' in dict_data):
            if self.timer_cleaning is not None:
                self.timer_cleaning.stop()
                self.timer_cleaning = None

    def destroy_timer_mapping(self):
        """Destroy timer object of mapping run mode"""
        dict_data = self.__dict__
        if ('timer_mapping' in dict_data):
            if self.timer_mapping is not None:
                self.timer_mapping.stop()
                self.timer_mapping = None

    def setup_timer_process_cleaning(self, countdown_time):
        """
        Setup timer for cleaning process
        Start timer with interval 1s
        Connect to slot function handle cleaning process when Timer timeout
        """
        self.timer_cleaning = QTimer()
        self.timer_cleaning.start(1000)
        self.timer_cleaning.timeout.connect(self.run_process_cleaning)
        self.countdown_time = countdown_time

    def setup_timer_process_mapping(self, countdown_time):
        """
        Setup timer for mapping process
        Start timer with interval 1s
        Connect to slot function handle mapping process when Timer timeout
        """
        self.timer_mapping = QTimer()
        self.timer_mapping.start(1000)
        self.timer_mapping.timeout.connect(self.run_process_mapping)
        self.countdown_time = countdown_time

    def run_process_cleaning(self):
        """
        Handle cleaning process
        Update current phase, operational state, error state
        """
        self.client.set(
                {'rvcOpState': {'operationalState': self.cr_State, 'countdownTime': self.countdown_time}})
        
        self.lbl_time.setText(
            "In Cleaning processing...{}s".format(
                self.countdown_time))
        if self.countdown_time <= 0:
            self.destroy_timer_cleaning()
            self.countdown_time = 0
            self.cr_phase = DOCKING_PHASE
            self.client.set({'rvcOpState': {'operationalState': STOPPED, 'countdownTime': self.countdown_time}})
            self.client.set(
                {'rvcOpStateIndex': {'errState': self.cr_error_state, 'crOpStateIndex': 0}})
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
            self.client.set({'runMode': {'currentMode': IDLE}})
            self.lbl_time.setText('...Cleaning process Done...')
            dockingTimer = Timer(5, self.set_crphase_drying)
            dockingTimer.start()

        elif 20 < self.countdown_time <= 30:
            self.cr_phase = CLEANING_PHASE
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})

        elif 10 < self.countdown_time <= 20:
            if self.countdown_time <= 20:
                self.client.set(
                    {'rvcOpState': {'operationalState': SEEKING_CHARGER, 'countdownTime': self.countdown_time}})
                self.cr_phase = CHARGING_PHASE
                self.client.set(
                    {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})

        elif 0 < self.countdown_time <= 10:
            if self.countdown_time <= 10:
                self.client.set({'rvcOpState': {'operationalState': CHARGING, 'countdownTime': self.countdown_time}})
                self.client.set(
                    {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
        
        if self.countdown_time > 0:
            self.countdown_time -= 1

    def run_process_mapping(self):
        """
        Handle mapping process
        Update current phase, operational state, error state
        """
        self.client.set(
                {'rvcOpState': {'operationalState': self.cr_State, 'countdownTime': self.countdown_time}})

        self.lbl_time.setText(
            "In Mapping processing...{}s".format(
                self.countdown_time))
        if self.countdown_time <= 0:
            self.destroy_timer_mapping()
            self.handle_mapping_done()

        elif 0 < self.countdown_time <= 20:
            self.cr_phase = MAPPING_PHASE
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})

        if self.countdown_time > 0:
            self.countdown_time -= 1

    def handle_mapping_done(self):
        """
        Handle mapping process done
        Update current phase, operational state, error state, run mode
        Notify mapping process done
        """
        self.cr_phase = DOCKING_PHASE
        self.countdown_time = 0
        self.client.set({'rvcOpState': {'operationalState': STOPPED, 'countdownTime': self.countdown_time}})
        self.client.set(
            {'rvcOpStateIndex': {'errState': self.cr_error_state, 'crOpStateIndex': STOP}})
        self.client.set({'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
        self.client.set({'runMode': {'currentMode': IDLE}})
        self.lbl_time.setText('...Mapping process Done...')

    def enable_update_mode(self):
        """Enable attribute 'enable_update' for enable update value of combo box"""
        self.enable_update = True

    def disable_error_text(self):
        """Display error text as empty"""
        self.lbl_error_status_mode.setText("")

    def handle_run_mode_changed(self, newMode):
        """
        Handle set current mode when run mode change
        :param newMode: A new mode of run mode cluster
        """
        self.enable_update = False
        QTimer.singleShot(2, self.enable_update_mode)

        logging.info("RPC SET run Mode: " + str(newMode) + ", " +
                     str(self.run_mode) + ", " + str(self.cr_State))
        if (newMode == self.run_mode):
            return
        if (self.cr_State == STOPPED) or (
                self.cr_State == CHARGING) or (self.cr_State == DOCKED):
            if (self.run_mode != IDLE) and (newMode != IDLE):
                self.lbl_error_status_mode.setText(
                    "! Change to the mapping or \ncleaning mode is only allowed from idle.")
                self.lbl_error_status_mode.setStyleSheet("color: orange;")
                return
        elif (self.cr_State == RUNNING):
            if (newMode != IDLE):
                self.lbl_error_status_mode.setText(
                    "! Can only change to the idle mode \nat running operational state.")
                self.lbl_error_status_mode.setStyleSheet("color: orange;")
                return

        self.disable_error_text()
        self.mutex.acquire(timeout=1)
        if ((newMode == MAPPING) or (newMode == IDLE)):
            self.countdown_time = 20
        else:
            pass
        self.client.set({'runMode': {'currentMode': newMode}})
        self.mutex.release()

    def handle_clean_mode_changed(self, newMode):
        """
        Handle set current mode when clean mode change
        :param newMode: A new mode of clean mode cluster
        """
        self.enable_update = False
        QTimer.singleShot(2, self.enable_update_mode)
        self.disable_error_text()
        logging.info("RPC SET clean Mode: " + str(newMode))
        if (self.run_mode != IDLE):
            self.lbl_error_status_mode.setText(
                "! Change of the cleaning mode \nis only allowed in Idle of run mode.")
            self.lbl_error_status_mode.setStyleSheet("color: orange;")
            return

        self.disable_error_text()
        self.mutex.acquire(timeout=1)
        self.client.set({'cleanMode': {'currentMode': newMode}})
        self.mutex.release()

    def notify_process_stopped(self):
        """Notify process of run mode stopped"""
        self.lbl_time.setText("...Process stopped...")

    def handle_operational_changed(self, mode):
        """
        Handle operational state command when operational state index change
        :param mode: A new mode of rvc operational state cluster
        """
        self.mutex.acquire(timeout=1)
        self.lbl_error_status_mode.setText("")
        if mode == STOP:
            if (self.run_mode != MAPPING):
                self.destroy_timer_cleaning()
            else:
                self.destroy_timer_mapping()
            self.remain_time = 0
            self.countdown_time = 0
            self.cr_phase = DOCKING_PHASE
            self.client.set({'rvcOpStateIndex': {
                            'errState': self.cr_error_state, 'crOpStateIndex': STOPPED}})
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
            self.run_mode = IDLE
            self.client.set({'runMode': {'currentMode': self.run_mode}})
            statusTimer = Timer(2, self.notify_process_stopped)
            statusTimer.start()

        elif mode == START:
            self.client.set({'rvcOpStateIndex': {
                            'errState': self.cr_error_state, 'crOpStateIndex': RUNNING}})
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
            if (self.run_mode != MAPPING):
                self.destroy_timer_cleaning()
                self.setup_timer_process_cleaning(30)
            else:
                self.destroy_timer_mapping()
                self.setup_timer_process_mapping(20)
        elif mode == PAUSE:
            self.remain_time = self.countdown_time
            self.client.set(
                {'rvcOpStateIndex': {'errState': self.cr_error_state, 'crOpStateIndex': PAUSED}})
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
            if self.cr_phase != CHARGING_PHASE:
                if (self.run_mode != MAPPING):
                    self.destroy_timer_cleaning()
                else:
                    self.destroy_timer_mapping()
            else:
                self.lbl_error_status_mode.setText(
                    "! Can not pause at SeekingCharger or Charging state.")
                self.lbl_error_status_mode.setStyleSheet("color: orange;")

        elif mode == RESUME:
            if ((self.cr_phase != CHARGING_PHASE) and (
                    self.cr_State != STOPPED) and (self.cr_error_state == NO_ERROR)):
                self.remain_time = self.countdown_time
                if (self.run_mode != MAPPING):
                    self.destroy_timer_cleaning()
                    self.setup_timer_process_cleaning(self.remain_time)
                else:
                    self.destroy_timer_mapping()
                    self.setup_timer_process_mapping(self.remain_time)
            self.client.set(
                {'rvcOpStateIndex': {'errState': self.cr_error_state, 'crOpStateIndex': RESUME}})
            self.client.set(
                {'rvcOpStatePhase': {'currentPhase': self.cr_phase}})
        self.mutex.release()

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def update_lb_level(self, value):
        """
        Update temperature measurement for temperature label
        :param value: Value of temperature slider
        """
        self.lb_level.setText(str(value) + "°C")

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data_1 = {'rvcOpStatePhase': {'phaseList': [0, 1, 2, 3]}}
            data_2 = {'rvcOpState': {'operationalState': STOPPED, 'countdownTime': 0}}
            data_3 = {
                'runMode': {
                    'currentMode': IDLE}, 'cleanMode': {
                    'currentMode': DEEP_CLEAN}, 'rvcOpStatePhase': {
                    'currentPhase': DOCKING_PHASE}, 'rvcOpStateIndex': {
                    'errState': NO_ERROR, 'crOpStateIndex': STOP}}
            self.client.set(data_1)
            self.client.set(data_2)
            self.client.set(data_3)
            self.lbl_operational_mod.setText('Operational State : Stopped')
            self.lbl_error_status.setText('Error state : No Error')
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

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
                    self.run_mode = device_status['reply']['runMode']['currentMode']
                    self.runmode_box.setCurrentIndex(self.run_mode)

                if (self.change_mode_status !=
                        device_status['reply']['rvcOpStatePhase']['changeModeStatus']):
                    self.change_mode_status = device_status['reply']['rvcOpStatePhase']['changeModeStatus']
                    if self.change_mode_status == NO_ERROR:
                        self.status = ""
                    elif self.change_mode_status == 3:
                        self.status = "! Change to the mapping or \ncleaning mode is only allowed from idle."
                        if self.cr_State == RUNNING:
                            self.status = "! Can only change to the idle mode \nat running operational state."
                    elif self.change_mode_status == 64:
                        self.status = "! Change of the cleaning mode \nis only allowed in Idle of run mode."

                    self.lbl_error_status_mode.setText(self.status)
                    self.lbl_error_status_mode.setStyleSheet("color: orange;")

                if (self.cr_error_state !=
                        device_status['reply']['rvcOpStateIndex']['errState']):
                    self.cr_error_state = device_status['reply']['rvcOpStateIndex']['errState']
                    if self.cr_error_state == NO_ERROR:
                        self.lbl_error_status.setText('Error state : No Error')
                    elif self.cr_error_state == UNABLE_TO_START_OR_RESUME:
                        self.lbl_error_status.setText(
                            'Error state : UnableToStartOrResume')
                    elif self.cr_error_state == UNABLE_TO_COMPLETE_OPERATION:
                        self.lbl_error_status.setText(
                            'Error state : UnabrleToCompleteOperation')
                    elif self.cr_error_state == COMMAND_IN_VALID_INSTATE:
                        self.lbl_error_status.setText(
                            'Error state : CommandInvalidInState')
                    elif self.cr_error_state == FAILED_TO_FIND_CHARGING_DOCK:
                        self.lbl_error_status.setText(
                            'Error state : FailedToFindChargingDock')
                    elif self.cr_error_state == STUCK:
                        self.lbl_error_status.setText('Error state : Stuck')
                    elif self.cr_error_state == DUSTB_IN_MISSING:
                        self.lbl_error_status.setText(
                            'Error state : DustBinMissing')
                    elif self.cr_error_state == DUSTB_IN_FULL:
                        self.lbl_error_status.setText(
                            'Error state : DustBinFull')
                    elif self.cr_error_state == WATER_TANK_EMPTY:
                        self.lbl_error_status.setText(
                            'Error state : WaterTankEmpty')
                    elif self.cr_error_state == WATER_TANK_MISSING:
                        self.lbl_error_status.setText(
                            'Error state : WaterTankMissing')
                    elif self.cr_error_state == WATER_TANK_LID_OPEN:
                        self.lbl_error_status.setText(
                            'Error state : WaterTankLidOpen')
                    elif self.cr_error_state == MOP_CLEANING_PAD_MISSING:
                        self.lbl_error_status.setText(
                            'Error state : MopCleaningPadMissing')

                if (self.cr_opState_index !=
                        device_status['reply']['rvcOpStateIndex']['crOpStateIndex']):
                    self.cr_opState_index = device_status['reply']['rvcOpStateIndex']['crOpStateIndex']
                    self.operational_box.setCurrentIndex(self.cr_opState_index)

                if (self.cr_State !=
                        device_status['reply']['rvcOpState']['operationalState']):
                    self.cr_State = device_status['reply']['rvcOpState']['operationalState']
                    if self.cr_State == STOPPED:
                        self.lbl_operational_mod.setText(
                            'Operational State : Stopped')
                    elif self.cr_State == RUNNING:
                        self.lbl_operational_mod.setText(
                            'Operational State : Running')
                    elif self.cr_State == PAUSED:
                        self.lbl_operational_mod.setText(
                            'Operational State : Paused')
                    elif self.cr_State == ERROR:
                        self.lbl_operational_mod.setText(
                            'Operational State : Error')
                    elif self.cr_State == SEEKING_CHARGER:  # 0x40 kSeekingCharger
                        self.lbl_operational_mod.setText(
                            'Operational State : SeekingCharger')
                    elif self.cr_State == CHARGING:  # 0x41 kCharging
                        self.lbl_operational_mod.setText(
                            'Operational State : Charging')
                    elif self.cr_State == DOCKED:  # 0x42 kDocked
                        self.lbl_operational_mod.setText(
                            'Operational State : Docked')

                self.cr_phase = device_status['reply']['rvcOpStatePhase']['currentPhase']
                if self.cr_phase == CLEANING_PHASE:
                    self.lbl_oper_status.setText(
                        'Current Phase : {}'.format("Cleaning"))
                elif self.cr_phase == DRYING_PHASE:
                    self.lbl_oper_status.setText(
                        'Current Phase : {}'.format("Drying"))
                elif self.cr_phase == DOCKING_PHASE:
                    self.lbl_oper_status.setText(
                        'Current Phase : {}'.format("Docking"))
                elif self.cr_phase == CHARGING_PHASE:
                    self.lbl_oper_status.setText(
                        'Current Phase : {}'.format("Charging"))
                elif self.cr_phase == MAPPING_PHASE:
                    self.lbl_oper_status.setText(
                        'Current Phase : {}'.format("Mapping"))

                if self.enable_update:
                    self.clean_mode = device_status['reply']['cleanMode']['currentMode']
                    self.cleanmode_box.setCurrentIndex(self.clean_mode)

        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
