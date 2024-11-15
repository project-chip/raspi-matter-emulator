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
from rpc.thermostat_client import ThermostatClient
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/HVAC/")

INDEX_OFF = 0
INDEX_HEAT = 1
INDEX_COOL = 2
INDEX_AUTO = 3
INDEX_EMERGENCY_HEAT = 4
INDEX_PRECOOLING    = 5
INDEX_FANONLY       = 6
INDEX_DRY           = 7
INDEX_SLEEP         = 8

MODE_OFF = 0
MODE_AUTO = 1
MODE_COOL = 3
MODE_HEAT = 4
MODE_EMERGENCY_HEAT = 5
MODE_PRECOOLING    = 6
MODE_FANONLY       = 7
MODE_DRY           = 8
MODE_SLEEP         = 9


class Thermostat(BaseDeviceUI):
    """
    Thermostat device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `Thermostat` UI.
        :param parent: An UI object load Thermostat device UI controller.
        """
        super().__init__(parent)
        self.systemMode = 0

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'thermostat.png')
        self.lbl_main_icon.setFixedSize(80, 80)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_icon)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # Local temperature
        self.lbl_main_status_local = QLabel()
        self.lbl_main_status_local.setText('Local Temperature :')
        self.lbl_main_status_local.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_local)

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
            self.lbl_main_status_local,
            alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.line_edit_temp, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_temp.textEdited.connect(self.on_text_edited)
        self.line_edit_temp.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_temp)

        # Cooling value
        self.lbl_main_status_cooling = QLabel()
        self.lbl_main_status_cooling.setText('Cooling : 0C° ')
        self.lbl_main_status_cooling.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_cooling)

        # Heating value
        self.lbl_main_status_heat = QLabel()
        self.lbl_main_status_heat.setText('Heating : 0C° ')
        self.lbl_main_status_heat.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_heat)

        self.sl_title_system = QLabel()
        self.sl_title_system.setText('Mode')
        self.parent.ui.lo_controller.addWidget(self.sl_title_system)

        # Thermostat system mode
        self.cb_mode = QComboBox()
        self.cb_mode.addItem('Off')
        self.cb_mode.addItem('Heat')
        self.cb_mode.addItem('Cool')
        self.cb_mode.addItem('Auto')
        self.cb_mode.addItem('EmergencyHeat')
        self.cb_mode.addItem('PreCooling')
        self.cb_mode.addItem('FanOnly')
        self.cb_mode.addItem('Dry')
        self.cb_mode.addItem('Sleep')
        self.parent.ui.lo_controller.addWidget(self.cb_mode)
        self.cb_mode.currentIndexChanged.connect(
            self.handle_system_mode_changed)

        # Heating slider
        self.sl_title_heat = QLabel()
        self.sl_title_heat.setText('Set Heating')
        self.lb_level_heat = QLabel()
        self.lb_level_heat.setText('C°')
        self.lb_level_heat.setAlignment(Qt.AlignCenter)

        self.sl_level_heat = QSlider()
        self.sl_level_heat.setRange(7, 30)
        self.sl_level_heat.setSingleStep(0.5)
        self.sl_level_heat.setOrientation(Qt.Horizontal)
        self.sl_level_heat.valueChanged.connect(self.update_lb_status)
        self.sl_level_heat.sliderReleased.connect(
            self.handle_level_heating_changed)
        self.sl_level_heat.sliderPressed.connect(self.on_pressed_event)

        # Cooling slider
        self.sl_title_cooling = QLabel()
        self.sl_title_cooling.setText('Set Cooling')
        self.lb_level_cooling = QLabel()
        self.lb_level_cooling.setText('C°')
        self.lb_level_cooling.setAlignment(Qt.AlignCenter)

        self.sl_level_cooling = QSlider()
        self.sl_level_cooling.setRange(16, 32)
        self.sl_level_cooling.setSingleStep(0.5)
        self.sl_level_cooling.setOrientation(Qt.Horizontal)
        self.sl_level_cooling.valueChanged.connect(self.update_lb_status)
        self.sl_level_cooling.sliderReleased.connect(
            self.handle_level_cooling_changed)
        self.sl_level_cooling.sliderPressed.connect(self.on_pressed_event)

        # Layout widget
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.sl_title_heat, 0, 0)
        self.grid_layout.addWidget(self.lb_level_heat, 0, 1)
        self.grid_layout.addWidget(self.sl_level_heat, 1, 0)
        self.grid_layout.addWidget(self.sl_title_cooling, 2, 0)
        self.grid_layout.addWidget(self.lb_level_cooling, 2, 1)
        self.grid_layout.addWidget(self.sl_level_cooling, 3, 0)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)
        self.update_lb_status()

        self.client = ThermostatClient(self.config)
        self.set_initial_value()
        self.heat_cool_deviation = 2
        self.is_edit = True

        self.start_update_device_status_thread()
        logging.debug("Init Thermostat done")

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def on_text_edited(self):
        """Enable 'is_edit' attribute when line edit is editting"""
        self.is_edit = False

    def on_return_pressed(self):
        """Handle set local temperature value when set from line edit"""
        try:
            value_temp = round(float(self.line_edit_temp.text()) * 100)
            if 0 <= value_temp <= 10000:
                data = {'localTemperature': value_temp}
                self.client.set(data)
                self.is_edit = True
            else:
                self.message_box(ER_TEMP)
                self.line_edit_temp.setText(str(self.temperature))
        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Thermostat")
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
                'systemMode': MODE_OFF,
                'localTemperature': 2550,
                'piCoolingDemand': 0,
                'piHeatingDemand': 0,
                'occupiedHeatingSetpoint': 1700,
                'occupiedCoolingSetpoint': 2600}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def update_lb_level_heat(self, value):
        """
        Update occupied heating value for occupied heating label
        :param value: Value of occupied heating slider
        """
        self.lb_level_heat.setText(str(value * 1.0) + "C°")

    def update_lb_level_cooling(self, value):
        """
        Update occupied cooling value for occupied cooling label
        :param value: Value of occupied cooling slider
        """
        self.lb_level_cooling.setText(str(value * 1.0) + "C°")

    def update_lb_status(self):
        """Update label for all attributes"""
        try:
            value_heat = self.sl_level_heat.value()
            value_cooling = self.sl_level_cooling.value()
            system_value = self.cb_mode.currentIndex()

            self.update_lb_level_heat(value_heat)
            self.update_lb_level_cooling(value_cooling)
            self.check_system_mode(system_value)

        except Exception as e:
            logging.debug("Failed to update lb_status: " + str(e))

    def check_system_mode(self, index):
        """
        Check thermostat system mode change
        then enable or disable UI corressponding to each system mode value
        :param index {int}: A index of system mode combo box
        """
        if index == INDEX_OFF:
            self.sl_level_heat.setEnabled(False)
            self.sl_level_cooling.setEnabled(False)
        elif index == INDEX_HEAT:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(False)
        elif index == INDEX_COOL:
            self.sl_level_cooling.setEnabled(True)
            self.sl_level_heat.setEnabled(False)
        elif index == INDEX_AUTO:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(True)
        elif index == INDEX_EMERGENCY_HEAT:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(False)
        elif index == INDEX_PRECOOLING:
            self.sl_level_cooling.setEnabled(True)
            self.sl_level_heat.setEnabled(False)
        elif index == INDEX_FANONLY:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(True)
        elif index == INDEX_DRY:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(True)
        elif index == INDEX_SLEEP:
            self.sl_level_heat.setEnabled(True)
            self.sl_level_cooling.setEnabled(True)          

    def handle_system_mode_changed(self):
        """
        Handle thermostat system mode change
        :param mode {int}: A new mode of thermostat system mode
        """
        index = self.cb_mode.currentIndex()
        logging.info("RPC SET index: " + str(index))
        self.mutex.acquire(timeout=1)
        self.check_system_mode(index)
        if index == INDEX_OFF:
            self.client.set({'systemMode': MODE_OFF})
        elif index == INDEX_HEAT:
            self.client.set({'systemMode': MODE_HEAT})
        elif index == INDEX_COOL:
            self.client.set({'systemMode': MODE_COOL})
        elif index == INDEX_AUTO:
            self.client.set({'systemMode': MODE_AUTO})
        elif index == INDEX_EMERGENCY_HEAT:
            self.client.set({'systemMode': MODE_EMERGENCY_HEAT})
        elif index == INDEX_PRECOOLING:
            self.client.set({'systemMode': MODE_PRECOOLING})
        elif index == INDEX_FANONLY:
            self.client.set({'systemMode': MODE_FANONLY})
        elif index == INDEX_DRY:
            self.client.set({'systemMode': MODE_DRY})
        elif index == INDEX_SLEEP:
            self.client.set({'systemMode': MODE_SLEEP})            
        self.mutex.release()
        self.is_on_control = False

    def handle_level_heating_changed(self):
        """
        Handle set OccupiedHeating value to matter device(backend)
        through rpc service when OccupiedHeating slider change
        """
        heat_value = self.sl_level_heat.value() * 100
        logging.info("RPC SET : " + str(heat_value))
        self.mutex.acquire(timeout=1)
        self.client.set({'occupiedHeatingSetpoint': heat_value})
        self.mutex.release()
        self.is_on_control = False

    def handle_level_cooling_changed(self):
        """
        Handle set OccupiedCooling value to matter device(backend)
        through rpc service when OccupiedCooling slider change
        """
        cooling_value = self.sl_level_cooling.value() * 100
        logging.info("RPC SET : " + str(cooling_value))
        self.mutex.acquire(timeout=1)
        self.client.set({'occupiedCoolingSetpoint': cooling_value})
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
            device_status = result['device_status']
            device_state = result['device_state']
            self.parent.update_device_state(device_state)
            if device_status['status'] == 'OK':
                self.temperature = round(
                    float(
                        device_status['reply'].get('localTemperature') /
                        100),
                    2)
                if self.is_edit:
                    self.line_edit_temp.setText(str(self.temperature))

                self.heat = round(
                    device_status['reply']['occupiedHeatingSetpoint'] / 100.0, 2)
                self.cooling = round(
                    device_status['reply']['occupiedCoolingSetpoint'] / 100.0, 2)

                self.sl_level_heat.setValue(self.heat)
                self.sl_level_cooling.setValue(self.cooling)

                self.update_lb_level_heat(self.heat)
                self.update_lb_level_cooling(self.cooling)

                self.lbl_main_status_heat.setText(
                    'Heating : {:.1f}C°'.format(self.heat))
                self.lbl_main_status_cooling.setText(
                    'Cooling: {:.1f}C°'.format(self.cooling))

                if (self.systemMode != round(
                        device_status['reply']['systemMode'])):
                    self.systemMode = round(
                        device_status['reply']['systemMode'])
                    if self.systemMode == MODE_OFF:
                        self.cb_mode.setCurrentIndex(INDEX_OFF)
                    elif self.systemMode == MODE_HEAT:
                        self.cb_mode.setCurrentIndex(INDEX_HEAT)
                    elif self.systemMode == MODE_COOL:
                        self.cb_mode.setCurrentIndex(INDEX_COOL)
                    elif self.systemMode == MODE_AUTO:
                        self.cb_mode.setCurrentIndex(INDEX_AUTO)
                    elif self.systemMode == MODE_EMERGENCY_HEAT:
                        self.cb_mode.setCurrentIndex(INDEX_EMERGENCY_HEAT)
                    elif self.systemMode == MODE_PRECOOLING:
                        self.cb_mode.setCurrentIndex(INDEX_PRECOOLING)
                    elif self.systemMode == MODE_FANONLY:
                        self.cb_mode.setCurrentIndex(INDEX_FANONLY)
                    elif self.systemMode == MODE_DRY:
                        self.cb_mode.setCurrentIndex(INDEX_DRY)
                    elif self.systemMode == MODE_SLEEP:
                        self.cb_mode.setCurrentIndex(INDEX_SLEEP)                        

                self.check_system_mode(self.cb_mode.currentIndex())

        except Exception as e:
            logging.error(str(e))

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
                        device_status = self.client.get()
                        device_state = self.client.get_device_state()
                        self.mutex.release()
                        self.sig_device_status_changed.emit(
                            {'device_status': device_status, 'device_state': device_state})
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
