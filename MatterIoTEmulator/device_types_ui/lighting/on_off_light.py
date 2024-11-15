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
from rpc.lighting_client import LightingClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/lighting/")


class OnOffLight(BaseDeviceUI):
    """
    OnOffLight device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `OnOffLight` UI.
        :param parent: An UI object load OnOffLight device UI controller.
        """
        super().__init__(parent)
        self.on_off = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'bulb_light_icon.png')
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_icon)

        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('On')
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

        # Init rpc
        self.client = LightingClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'level': 25,
                'color': {
                    'hue': 0,
                    'saturation': 0},
                'on': self.on_off}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

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
                self.on_off = device_status['reply'].get('on')
                if self.on_off:
                    self.lbl_main_status.setText('On')
                    self.sw.setCheckState(Qt.Checked)
                else:
                    self.lbl_main_status.setText('Off')
                    self.sw.setCheckState(Qt.Unchecked)
        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
