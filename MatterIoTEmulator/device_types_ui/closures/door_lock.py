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
from PySide2.QtCore import Qt as Qt_core
from PySide2.QtWidgets import *
import logging
import threading
import time
import random
import os
import json
from qtwidgets import Toggle
from rpc.lock_client import LockClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/closures/")

INCOMPLETE_LOCKED = 0
LOCKED = 1
UN_LOCKED = 2

OPENED = 0
CLOSED = 1
JAMMED = 2
FORCED_OPEN = 3
INVALID = 4
FORCED_AJAR = 5


class DoorLock(BaseDeviceUI):
    """
    DoorLock device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `DoorLock` UI.
        :param parent: An UI object load DoorLock device UI controller.
        """
        super().__init__(parent)
        self.lock_state = LOCKED
        self.previous_lock_state = LOCKED

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'door_lock.png')
        self.lbl_main_icon.setFixedSize(80, 80)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 20, 0, 0)
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        self.lbl_main_status_clock = QLabel()
        self.lbl_main_status_clock.setText('Lock State: Locked')
        self.lbl_main_status_clock.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_clock)

        self.lbl_main_status_contact = QLabel()
        self.lbl_main_status_contact.setText('Door State: Door Close')
        self.lbl_main_status_contact.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_contact)

        self.sw_title = QLabel()
        self.sw_title.setText('Lock Control')
        self.parent.ui.lo_controller.addWidget(self.sw_title)

        # Create a combo box
        self.lock_control_box = QComboBox()
        self.lock_control_box.addItem("Not Fully Lock")
        self.lock_control_box.addItem("Lock")
        self.lock_control_box.addItem("Unlock")
        # Connect the currentIndexChanged signal to a slot
        self.lock_control_box.currentIndexChanged.connect(
            self.handle_lock_state_changed)
        self.parent.ui.lo_controller.addWidget(self.lock_control_box)

        # Init rpc
        self.client = LockClient(self.config)
        self.set_initial_value()

        self.start_update_device_status_thread()
        self.start_update_value_status_thread()

        logging.debug("Init door lock done")

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {'klockState': LOCKED, 'doorState': CLOSED}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def handle_lock_state_changed(self, data):
        """
        Handle set lock state to matter device(backend)
        when set lock state from UI
        :param data: Lock state value
        INCOMPLETE_LOCKED = 0, LOCKED = 1, UN_LOCKED = 2
        """
        logging.info("RPC SET lock/unlock: " + str(data))
        self.mutex.acquire(timeout=1)
        self.client.set({"klockState": int(data)})
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
                if (self.lock_state !=
                        device_status['reply'].get('klockState')):
                    self.lock_state = device_status['reply'].get('klockState')
                    if self.lock_state == INCOMPLETE_LOCKED:
                        self.lock_control_box.setCurrentIndex(
                            INCOMPLETE_LOCKED)
                        self.lbl_main_status_clock.setText(
                            'Lock State: Incomplete Locked')
                    elif self.lock_state == LOCKED:
                        self.lock_control_box.setCurrentIndex(LOCKED)
                        self.lbl_main_status_clock.setText(
                            'Lock State: Locked')
                    elif self.lock_state == UN_LOCKED:
                        self.lock_control_box.setCurrentIndex(UN_LOCKED)
                        self.lbl_main_status_clock.setText(
                            'Lock State: UnLocked')

                door_state = device_status['reply'].get('doorState')
                str_door = 'Door State:'
                if door_state == OPENED:
                    self.lbl_main_status_contact.setText(str_door + ' Opened')
                elif door_state == CLOSED:
                    self.lbl_main_status_contact.setText(str_door + ' Closed')
                elif door_state == JAMMED:
                    self.lbl_main_status_contact.setText(str_door + ' Jammed')
                elif door_state == FORCED_OPEN:
                    self.lbl_main_status_contact.setText(
                        str_door + ' Forced Open')
                elif door_state == INVALID:
                    self.lbl_main_status_contact.setText(
                        str_door + ' Invalid for unspecified reason')
                elif door_state == FORCED_AJAR:
                    self.lbl_main_status_contact.setText(
                        str_door + ' Forced Ajar')
        except Exception as e:
            logging.info("Error: " + str(e))

    def on_value_status_changed(self):
        """
        Update value for all attributes on UI
        when set timer for change random attribute value
        """
        if self.lock_state != self.previous_lock_state:
            if "UnLocked" in self.lbl_main_status_clock.text():
                self.mutex.acquire(timeout=1)
                self.client.set({'doorState': OPENED})
                self.mutex.release()
            else:
                self.mutex.acquire(timeout=1)
                self.client.set({'doorState': CLOSED})
                self.mutex.release()
            self.previous_lock_state = self.lock_state

    def stop(self):
        """
        Stop thread update device status
        Stop thread update device state
        Stop rpc client
        """
        self.stop_update_status_thread()
        self.stop_update_state_thread()
        self.stop_client_rpc()
