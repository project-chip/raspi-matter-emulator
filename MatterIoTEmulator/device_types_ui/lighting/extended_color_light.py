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
import colorsys
import logging
import threading
import os
import time
from rpc.lighting_client import LightingClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/lighting/")


class ExtendedColorLight(BaseDeviceUI):
    """
    ExtendedColorLight device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `ExtendedColorLight` UI.
        :param parent: An UI object load ExtendedColorLight device UI controller.
        """
        super().__init__(parent)
        self.on_off = True
        self.level = 25
        self.color_hue = 30
        self.color_saturation = 10

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'bulb_light_icon.png')
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_icon)

        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('Light On\n100%')
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

        # Level slider
        self.lb_level_title = QLabel()
        self.lb_level_title.setText('Level')
        self.lb_level = QLabel()
        self.lb_level.setText('0%')
        self.lb_level.setAlignment(Qt.AlignCenter)

        self.sl_level = QSlider()
        self.sl_level.setRange(0, 100)
        self.sl_level.setOrientation(Qt.Horizontal)
        self.sl_level.valueChanged.connect(self.update_lb_status)
        self.sl_level.sliderReleased.connect(self.handle_level_changed)
        self.sl_level.sliderPressed.connect(self.on_pressed_event)

        # Saturation slider
        self.lb_saturation_title = QLabel()
        self.lb_saturation_title.setText('Saturation')
        self.lb_saturation_value = QLabel()
        self.lb_saturation_value.setText('0%')
        self.lb_saturation_value.setAlignment(Qt.AlignCenter)

        self.sl_saturation = QSlider()
        self.sl_saturation.setRange(0, 254)
        self.sl_saturation.setOrientation(Qt.Horizontal)
        self.sl_saturation.valueChanged.connect(self.update_lb_status)
        self.sl_saturation.sliderReleased.connect(
            self.handle_color_saturation_changed)
        self.sl_saturation.sliderPressed.connect(self.on_pressed_event)

        # Hue slider
        self.lb_hue_title = QLabel()
        self.lb_hue_title .setText('Hue')
        self.lb_hue_value = QLabel()
        self.lb_hue_value.setText('0')
        self.lb_hue_value.setAlignment(Qt.AlignCenter)

        self.sl_hue = QSlider()
        self.sl_hue.setRange(0, 254)
        self.sl_hue.setOrientation(Qt.Horizontal)
        self.sl_hue.valueChanged.connect(self.update_lb_status)
        self.sl_hue.sliderReleased.connect(self.handle_color_hue_changed)
        self.sl_hue.sliderPressed.connect(self.on_pressed_event)

        self.lb_color = QLabel()
        self.lb_color.setFixedSize(40, 40)
        self.lb_color.setStyleSheet("background-color: red")

        # Layout widget
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.lb_level_title, 0, 0)
        self.grid_layout.addWidget(self.lb_level, 0, 1)
        self.grid_layout.addWidget(self.sl_level, 1, 0)
        self.grid_layout.addWidget(self.lb_hue_title, 2, 0)
        self.grid_layout.addWidget(self.lb_hue_value, 2, 1)
        self.grid_layout.addWidget(self.sl_hue, 3, 0)
        self.grid_layout.addWidget(self.lb_saturation_title, 4, 0)
        self.grid_layout.addWidget(self.lb_saturation_value, 4, 1)
        self.grid_layout.addWidget(self.sl_saturation, 5, 0)
        self.grid_layout.addWidget(self.lb_color, 6, 0)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        # Init rpc
        self.client = LightingClient(self.config)
        self.set_initial_value()
        self.update_lb_status()
        self.start_update_device_status_thread()

        logging.debug("Init Extended color light done")

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
                'on': self.on_off,
                'level': self.level,
                'color': {
                    'hue': self.color_hue,
                    'saturation': self.color_saturation}}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def rgb_to_hex(self, rgb):
        """
        Convert rgb value to hexa
        :param rgb: rgb value of color of light
        """
        return "#" + str('%02x%02x%02x' % rgb)

    def hex_to_rgb(self, value):
        """
        Convert hexa to rgb value
        :param value: value is hexa unit of color of light
        """
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16)
                     for i in range(0, lv, lv // 3))

    def convert_hsv_to_rgb(self, hsv_value):
        """
        Convert hsv to rgb value
        :param hsv_value: hsv_value is list of current hue,
        current saturation and level attribute
        """
        # input
        (h, s, v) = hsv_value
        # normalize
        (h, s, v) = (h / 254, s / 254, v / 100)
        # convert to RGB
        (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
        # expand RGB range
        (r, g, b) = (int(r * 255), int(g * 255), int(b * 255))
        # logging.info("Convert HSV raw: {} --> RGB value: {}".format(hsv_value, (r, g, b)))
        return (r, g, b)

    def update_lb_level(self, value):
        """
        Update level value of level control cluster for level label
        :param value: Value of level slider
        """
        self.lb_level.setText(str(value) + "%")

    def update_lb_hue(self, value):
        """
        Update current hue value of
        color control cluster for current hue label
        :param value: Value of current hue slider
        """
        self.lb_hue_value.setText(str(value))

    def update_lb_saturation(self, value):
        """
        Update current saturation value of
        color control cluster for current saturation label
        :param value: Value of current saturation slider
        """
        self.lb_saturation_value.setText(str(value))

    def update_lb_status(self):
        """
        Update update_lb_level, update_lb_hue, update_lb_saturation
        """
        try:
            self.level = self.sl_level.value()
            self.color_hue = self.sl_hue.value()
            self.color_saturation = self.sl_saturation.value()

            self.update_lb_level(self.level)
            self.update_lb_hue(self.color_hue)
            self.update_lb_saturation(self.color_saturation)

            hex_color = self.rgb_to_hex(self.convert_hsv_to_rgb(
                (self.color_hue, self.color_saturation, self.level)))
            self.lb_color.setStyleSheet(
                "background-color: {}".format(hex_color))
        except Exception as e:
            logging.debug("Failed to update lb_status: " + str(e))

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

    def handle_color_hue_changed(self):
        """
        Handle set current hue attribute to matter device(backend)
        through rpc service when current hue value change
        """
        self.color_hue = self.sl_hue.value()
        logging.info("RPC SET Hue: " + str(self.color_hue))
        self.mutex.acquire(timeout=1)
        self.client.set({'on': self.on_off,
                         'color': {'hue': self.color_hue,
                                   'saturation': self.color_saturation}})
        self.mutex.release()
        self.is_on_control = False

    def handle_color_saturation_changed(self):
        """
        Handle set current saturation attribute to matter device(backend)
        through rpc service when current saturation value change
        """
        self.color_saturation = self.sl_saturation.value()
        logging.info("RPC SET Color Saturation: " + str(self.color_saturation))
        self.mutex.acquire(timeout=1)
        self.client.set({'on': self.on_off,
                         'color': {'hue': self.color_hue,
                                   'saturation': self.color_saturation}})
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
                self.color_hue = round(device_status['reply']['color']['hue'])
                self.color_saturation = round(
                    device_status['reply']['color']['saturation'])

                self.sl_level.setValue(int(self.level))
                self.sl_hue.setValue(int(self.color_hue))
                self.sl_saturation.setValue(int(self.color_saturation))

                self.on_off = device_status['reply'].get('on')
                if self.on_off:
                    self.lbl_main_status.setText(
                        'Light On\n{}%'.format(self.level))
                    self.sw.setCheckState(Qt.Checked)
                else:
                    self.lbl_main_status.setText(
                        'Light Off\n{}%'.format(self.level))
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
