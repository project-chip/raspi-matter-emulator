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
from rpc.pump_client import PumpClient
import threading
import os
import time
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/pump/")
LOCAL_SPEED_SETTING = 25


class Pump(BaseDeviceUI):
    """
    Pump device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `Pump` UI.
        :param parent: An UI object load Pump device UI controller.
        """
        super().__init__(parent)
        self.on_off = True
        self.level = 25
        self.value_temp = 3197
        self.value_pres = 187
        self.value_flow = 109
        self.operation_mode = 0
        self.is_edit_temp = True
        self.is_edit_flow = True
        self.is_edit_pres = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'water-pump.png')
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
        self.lbl_main_status.setText('Pump Off')
        self.lbl_main_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        self.lbl_main_status_level = QLabel()
        self.lbl_main_status_level.setText('Setpoint : 25%')
        self.lbl_main_status_level.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_level)

        self.lbl_main_status_temperature = QLabel()
        self.lbl_main_status_temperature.setText('Temperature :')
        self.lbl_main_status_temperature.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(
            self.lbl_main_status_temperature)

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
            self.lbl_main_status_temperature,
            alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.line_edit_temp, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_temp.textEdited.connect(self.on_text_edited_temp)
        self.line_edit_temp.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_temp)

        self.lbl_main_status_pressure = QLabel()
        self.lbl_main_status_pressure.setText('Pressure :')
        self.lbl_main_status_pressure.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_pressure)

        self.line_edit_pres = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_pres.setValidator(self.validator)
        self.line_edit_pres.setValidator(self.double_validator)
        self.line_edit_pres.setMaximumSize(QSize(65, 20))
        self.lbl_measure = QLabel()
        self.lbl_measure.setText('kPa')
        self.grid_layout_pres = QHBoxLayout()
        self.grid_layout_pres.setAlignment(Qt.AlignCenter)
        self.grid_layout_pres.addWidget(
            self.lbl_main_status_pressure,
            alignment=Qt.AlignRight)
        self.grid_layout_pres.addWidget(
            self.line_edit_pres, alignment=Qt.AlignRight)
        self.grid_layout_pres.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_pres.textEdited.connect(self.on_text_edited_pres)
        self.line_edit_pres.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_pres)

        self.lbl_main_status_flow = QLabel()
        self.lbl_main_status_flow.setText('Flow :')
        self.lbl_main_status_flow.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_flow)

        self.line_edit_flow = QLineEdit()
        self.validator = QIntValidator()
        self.double_validator = QDoubleValidator()
        self.line_edit_flow.setValidator(self.validator)
        self.line_edit_flow.setValidator(self.double_validator)
        self.line_edit_flow.setMaximumSize(QSize(65, 20))
        self.lbl_measure = QLabel()
        self.lbl_measure.setText('m3/h')
        self.grid_layout_flow = QHBoxLayout()
        self.grid_layout_flow.setAlignment(Qt.AlignCenter)
        self.grid_layout_flow.addWidget(
            self.lbl_main_status_flow,
            alignment=Qt.AlignRight)
        self.grid_layout_flow.addWidget(
            self.line_edit_flow, alignment=Qt.AlignRight)
        self.grid_layout_flow.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_flow.textEdited.connect(self.on_text_edited_flow)
        self.line_edit_flow.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_flow)

        # Show control button/switch
        self.sw_title = QLabel()
        self.sw_title.setText('Off/On')
        self.parent.ui.lo_controller.addWidget(self.sw_title)
        self.sw = Toggle()
        self.sw.setFixedSize(60, 40)
        self.sw.stateChanged.connect(self.handle_onoff_changed)
        self.parent.ui.lo_controller.addWidget(self.sw)

        # Show dimmable slider
        self.sl_title = QLabel()
        self.sl_title.setText('Setpoint')
        self.parent.ui.lo_controller.addWidget(self.sl_title)
        self.lb_level = QLabel()
        self.lb_level.setText('0,5%')
        self.lb_level.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lb_level)

        self.sl_level = QSlider()
        self.sl_level.setRange(0, 100)
        self.sl_level.setSingleStep(0.5)
        self.sl_level.setOrientation(Qt.Horizontal)
        self.sl_level.valueChanged.connect(self.update_lb_level)
        self.sl_level.sliderReleased.connect(self.handle_level_changed)
        self.sl_level.sliderPressed.connect(self.on_pressed_event)
        self.parent.ui.lo_controller.addWidget(self.sl_level)

        # Operational state
        self.lbl_operational_mod = QLabel()
        self.lbl_operational_mod.setText('Operation Mode')
        self.parent.ui.lo_controller.addWidget(self.lbl_operational_mod)

        operation_mode_list = [
            "Normal",
            "Minimum Speed",
            "Maximum Speed",
            "Device Settings"]
        self.operation_mode_box = QComboBox()
        self.operation_mode_box.addItems(operation_mode_list)
        # Connect the currentIndexChanged signal to a slot
        self.operation_mode_box.currentIndexChanged.connect(
            self.handle_operation_mode_changed)
        self.parent.ui.lo_controller.addWidget(self.operation_mode_box)
        self.parent.ui.lo_controller.addWidget(QLabel(""))

        # Init rpc
        self.client = PumpClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()
        logging.debug("Init pump done")

    def on_text_edited_temp(self):
        """Handle set temperature measurement when set from line edit"""
        self.is_edit_temp = False

    def on_text_edited_flow(self):
        """Handle set flow measurement when set from line edit"""
        self.is_edit_flow = False

    def on_text_edited_pres(self):
        """Handle set pressure measurement when set from line edit"""
        self.is_edit_pres = False

    def on_return_pressed(self):
        """Handle set temperature measurement,
        pressure measurement, flow measurement
        when set from line edit"""
        try:
            temp_value = round(float(self.line_edit_temp.text()) * 100)
            pres_value = round(float(self.line_edit_pres.text()) * 10)
            flow_value = round(float(self.line_edit_flow.text()) * 10)
            if 0 <= temp_value <= 10000:
                data = {'on': True, 'temperatureValue': temp_value}
                self.client.set(data)
                self.is_edit_temp = True
            else:
                self.message_box(ER_TEMP)
                self.line_edit_temp.setText(str(self.value_temp))
            if 0 <= pres_value <= 32767:
                data = {'on': True, 'pressureValue': pres_value}
                self.client.set(data)
                self.is_edit_pres = True
            else:
                self.message_box(ER_PRES)
                self.line_edit_pres.setText(str(self.value_pres))

            if 0 <= flow_value <= 65535:
                data = {'on': True, 'flowValue': flow_value}
                self.client.set(data)
                self.is_edit_flow = True
            else:
                self.message_box(ER_FLOW)
                self.line_edit_flow.setText(str(self.value_flow))
        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Pump")
        msgBox.setText("Value out of range")
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'level': LOCAL_SPEED_SETTING,
                'on': self.on_off,
                'temperatureValue': self.value_temp,
                'pressureValue': self.value_pres,
                'flowValue': self.value_flow}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def update_lb_level(self, value):
        """
        Update level value of level control cluster for level label
        :param value: Value of level slider
        """
        self.lb_level.setText(str(value) + "%")

    def handle_onoff_changed(self, data):
        """
        Handle set on off attribute to matter device(backend)
        through rpc service when on/off toggle
        :param data: Value of on-off attribute, 0: False, other True
        """
        logging.info("RPC SET On/Off: " + str(data))
        self.mutex.acquire(timeout=1)
        if data == 0:
            self.on_off = False
        else:
            self.on_off = True
        self.client.set({"on": self.on_off})
        self.mutex.release()

    def handle_level_changed(self):
        """
        Handle set level attribute to matter device(backend)
        through rpc service when level value change
        """
        self.level = round(self.sl_level.value() * 2)
        logging.info("RPC SET Level: " + str(self.level))
        self.mutex.acquire(timeout=1)
        self.client.set({'on': self.on_off, "level": self.level})
        self.mutex.release()
        self.is_on_control = False

    def handle_operation_mode_changed(self, mode):
        """
        Handle set operation state attribute to matter device(backend)
        through rpc service when operation state value change
        :param mode: A new mode of operation state
        """
        if mode == 0:
            self.client.set({'on': self.on_off, "operation_mode": mode})
            self.sl_level.setEnabled(True)
        elif mode == 3:
            self.client.set({'on': self.on_off,
                             "level": LOCAL_SPEED_SETTING,
                             "operation_mode": mode})
            self.sl_level.setEnabled(False)
        else:
            self.client.set({'on': self.on_off, "operation_mode": mode})
            self.sl_level.setEnabled(False)
        self.mutex.acquire(timeout=1)
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
                self.level = round(device_status['reply'].get('level') / 2)
                self.value_temp = round(
                    float(
                        device_status['reply'].get('temperatureValue') /
                        100),
                    2)
                self.value_pres = round(
                    float(
                        device_status['reply'].get('pressureValue') /
                        10),
                    1)
                self.value_flow = round(
                    float(device_status['reply'].get('flowValue') / 10), 1)

                if self.operation_mode != device_status['reply'].get(
                        'operationMode'):
                    self.operation_mode = device_status['reply'].get(
                        'operationMode')
                    self.operation_mode_box.setCurrentIndex(
                        self.operation_mode)

                if self.level > 100:
                    self.level = 100
                self.sl_level.setValue(int(self.level))

                if self.is_edit_temp:
                    self.line_edit_temp.setText(str(self.value_temp))
                if self.is_edit_pres:
                    self.line_edit_pres.setText(str(self.value_pres))
                if self.is_edit_flow:
                    self.line_edit_flow.setText(str(self.value_flow))

                self.on_off = device_status['reply'].get('on')
                if self.on_off:
                    self.lbl_main_status_level.setText(
                        'Setpoint :{}%'.format(self.level))
                    self.lbl_main_status.setText('Pump On')
                    self.sw.setCheckState(Qt.Checked)
                else:
                    self.lbl_main_status_level.setText(
                        'Setpoint :{}%'.format(self.level))
                    self.lbl_main_status.setText('Pump Off')
                    self.sw.setCheckState(Qt.Unchecked)
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
