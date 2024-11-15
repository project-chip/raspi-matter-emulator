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
import time
import os
from rpc.hvac_client import HvacClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/HVAC/")


class HeatingCooling(BaseDeviceUI):
    """
    HeatingCooling device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `HeatingCooling` UI.
        :param parent: An UI object load HeatingCooling device UI controller.
        """
        super().__init__(parent)
        self.on_off = True
        self.level = 25

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'heating-unit.png')
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

        # Heating Cooling status
        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('Heating Cooling')
        self.lbl_main_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        # Show control button/switch
        self.sw_title = QLabel()
        self.sw_title.setText('Off/On')
        self.parent.ui.lo_controller.addWidget(self.sw_title)
        self.sw = Toggle()
        self.sw.setFixedSize(60, 40)
        self.sw.stateChanged.connect(self.handle_onoff_changed)
        self.parent.ui.lo_controller.addWidget(self.sw)

        # Show level slider
        self.sl_title = QLabel()
        self.sl_title.setText('Level')
        self.parent.ui.lo_controller.addWidget(self.sl_title)
        self.lb_level = QLabel()
        self.lb_level.setText('0%')
        self.lb_level.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lb_level)

        self.sl_level = QSlider()
        self.sl_level.setRange(0, 100)
        self.sl_level.setOrientation(Qt.Horizontal)
        self.sl_level.valueChanged.connect(self.update_lb_level)
        self.sl_level.sliderReleased.connect(self.handle_level_changed)
        self.sl_level.sliderPressed.connect(self.on_pressed_event)
        self.parent.ui.lo_controller.addWidget(self.sl_level)

        # Init rpc
        self.client = HvacClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

        logging.debug("Init heating done")

    def on_pressed_event(self):
        """Slider pressed handler"""
        self.is_on_control = True

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {'level': self.level, 'on': self.on_off}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def update_lb_level(self, value):
        """
        Update level attribute value of level control cluster for level label
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
        self.level = round(self.sl_level.value() * 2.54)
        logging.info("RPC SET Level: " + str(self.level))
        self.mutex.acquire(timeout=1)
        self.client.set({'on': self.on_off, "level": self.level})
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
                self.level = round(device_status['reply'].get('level') / 2.54)
                self.sl_level.setValue(int(self.level))

                self.on_off = device_status['reply'].get('on')
                if self.on_off:
                    self.lbl_main_status.setText(
                        'Heating On\n{}%'.format(self.level))
                    self.sw.setCheckState(Qt.Checked)
                else:
                    self.lbl_main_status.setText(
                        'Heating Off\n{}%'.format(self.level))
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
