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
from device_types_ui.stoppablethread import UpdateStatusThread
from constants import *


class BaseDeviceUI(QObject):
    """
    Class base for device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """
    sig_device_status_changed = Signal(dict)
    sig_value_status_changed = Signal()

    def __init__(self, parent) -> None:
        """
        Initial attributes value, connect signal slot.
        :param parent: An UI object load device UI controller instance object.
        """
        QObject.__init__(self)
        self.parent = parent

        self.sig_device_status_changed.connect(self.on_device_status_changed)
        self.sig_value_status_changed.connect(self.on_value_status_changed)

        # Init rpc
        rpc_port = str(self.parent.rpcPort)
        self.mutex = threading.Lock()
        self.config = "localhost:" + rpc_port
        self.client = None

        self.is_on_control = False

        self.parent.is_rpc_timer_running = True
        self.update_device_status_thread = None
        self.update_value_status_thread = None

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        # ToDo: set initial rpc value here
        pass

    def check_condition_update_status(self, thread_instance):
        """
        Check condition of thread to update status
        :param thread_instance: thread instance object
        """
        if (thread_instance is None):
            return False
        return ((not thread_instance.stop_flag)
                and self.parent.is_rpc_timer_running)

    def on_device_status_changed(self, result):
        """
        Interval update all attributes value
        to UI through rpc service
        :param result {dict}: Data get all attributes value
        from matter device(backend) from rpc service
        """
        logging.info(
            f'on_device_status_changed {result}, RPC Port: {str(self.parent.rpcPort)}')
        try:
            # ToDo: Frequently get data from device to update UI
            pass
        except Exception as e:
            print("Error: " + str(e))

    def on_value_status_changed(self):
        """
        Handle update value of attributes on UI
        when update random value by timer
        """
        # ToDo: Do update value when run random set value from UI
        pass

    def update_device_status(self):
        """
        Use for emit signal 'sig_device_status_changed' to update value of
        attributes on UI from Backend (matter device)
        """
        try:
            while self.check_condition_update_status(
                    self.update_device_status_thread):
                try:
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

    def update_value_status(self):
        """
        Use for Use for emit signal 'sig_value_status_changed' to update value
        of attributes on UI when update random value by timer
        """
        try:
            while self.check_condition_update_status(
                    self.update_value_status_thread):
                self.sig_value_status_changed.emit()
                time.sleep(1)
        except Exception as e:
            logging.error(str(e))

    def start_update_device_status_thread(self):
        """
        Use for start thread update device value from Backend (matter device)
        """
        self.update_device_status_thread = UpdateStatusThread(
            target=self.update_device_status, name="update device status thread")
        self.update_device_status_thread.start()

    def start_update_value_status_thread(self):
        """
        Use for start thread update device value
        when update random value by timer on UI
        """
        self.update_value_status_thread = UpdateStatusThread(
            target=self.update_value_status, name="update value status thread")
        self.update_value_status_thread.start()

    def stop_update_status_thread(self):
        """
        Use for stop thread update device value from Backend (matter device)
        """
        if self.update_value_status_thread is not None:
            self.update_value_status_thread.stop()

    def stop_update_state_thread(self):
        """
        Use for stop thread update device value
        when update random value by timer on UI
        """
        if self.update_device_status_thread is not None:
            self.update_device_status_thread.stop()

    def stop_client_rpc(self):
        """
        Stop rpc client process
        """
        if self.client is not None:
            self.client.stop()
