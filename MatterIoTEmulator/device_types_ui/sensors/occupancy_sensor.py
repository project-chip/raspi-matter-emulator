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
import logging
import threading
import random
import time
import os
from rpc.sensor_client import SensorClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/sensors/")


class OccupancySensor(BaseDeviceUI):
    """
    OccupancySensor device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `OccupancySensor` UI.
        :param parent: An UI object load OccupancySensor device UI controller.
        """
        super().__init__(parent)
        self.time_repeat = 0
        self.time_sleep = 0
        self.remaining_time_interval = 0
        self.is_stop_clicked = False
        self.occupancy_value = 1

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'occupancy-sensor.png')
        self.lbl_main_icon.setFixedSize(80, 80)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # Occupancy status
        self.lbl_main_status_occupnacy = QLabel()
        self.lbl_main_status_occupnacy.setStyleSheet("font-size: 13pt;")
        self.lbl_main_status_occupnacy.setText('Occupancy status: Unoccupied')
        self.lbl_main_status_occupnacy.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status_occupnacy)

        # Add UI for set timer UI
        self.lbl_remaining_time_interval = QLabel()
        self.lbl_remaining_time_interval.setStyleSheet("font-size: 13pt;")
        self.lbl_remaining_time_interval.setText(
            'Remaining time of interval: 0 sec')
        self.lbl_remaining_time_interval.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(
            self.lbl_remaining_time_interval)
        self.lbl_remain_repeat_time = QLabel()
        self.lbl_remain_repeat_time.setStyleSheet("font-size: 13pt;")
        self.lbl_remain_repeat_time.setText('Remaining count: 0')
        self.lbl_remain_repeat_time.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_remain_repeat_time)
        # Label time interval
        self.lbl_time_edit = QLabel()
        self.lbl_time_edit.setText("Interval(sec)")
        self.lbl_time_edit.setStyleSheet("font-size: 13pt;")
        self.parent.ui.lo_controller.addWidget(self.lbl_time_edit)
        # Time Edit
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat('ss')
        self.time_edit.setFixedHeight(30)
        self.time_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.parent.ui.lo_controller.addWidget(self.time_edit)
        # Label count repeat
        self.lbl_count_repeat = QLabel()
        self.lbl_count_repeat.setText("Count")
        self.lbl_count_repeat.setStyleSheet("font-size: 13pt;")
        self.parent.ui.lo_controller.addWidget(self.lbl_count_repeat)
        self.qline_count = QLineEdit("0")
        self.qline_count.setValidator(QIntValidator(0, 6000, self))
        self.qline_count.setFixedHeight(30)
        self.qline_count.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.parent.ui.lo_controller.addWidget(self.qline_count)
        self.set_time_button = QPushButton()
        self.set_time_button.setText("Start")
        self.set_time_button.setMaximumSize(QSize(120, 100))
        self.set_time_button.clicked.connect(self.click_set)
        self.stop_button = QPushButton()
        self.stop_button.setText("Stop")
        self.stop_button.setMaximumSize(QSize(120, 100))
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        # Layout widget
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.addWidget(self.lbl_time_edit, 0, 0)
        self.grid_layout.addWidget(self.time_edit, 0, 1)
        self.grid_layout.addWidget(self.lbl_count_repeat, 1, 0)
        self.grid_layout.addWidget(self.qline_count, 1, 1)
        self.grid_layout_2 = QGridLayout()
        self.grid_layout_2.addWidget(self.set_time_button, 2, 0)
        self.grid_layout_2.addWidget(self.stop_button, 2, 1)

        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.parent.ui.lo_controller.addLayout(self.grid_layout)
        self.parent.ui.lo_controller.addWidget(QLabel(""))
        self.parent.ui.lo_controller.addLayout(self.grid_layout_2)

        # Init rpc
        self.client = SensorClient(self.config)
        self.is_set_running = False
        self.set_initial_value()

        self.start_update_device_status_thread()
        self.start_update_value_status_thread()

        logging.debug("Init Occupancy sensor done")

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {'occupancyValue': 1}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def get_time_info(self):
        """
        Get value of timer interval and repeat count
        :return time_sleep, time_repeat: value of timer interval and repeat count
        """
        value = self.time_edit.time()
        time_sleep = value.second()
        time_repeat = int(self.qline_count.text())
        return time_sleep, time_repeat

    def click_set(self):
        """Handle when click start generate random value"""
        try:
            self.is_stop_clicked = False
            self.set_time_button.setText("Restart")
            self.stop_button.setText("Stop")
            self.time_sleep, self.time_repeat = self.get_time_info()
            self.remaining_time_interval = self.time_sleep
        except Exception as e:
            logging.error("Error: " + str(e))

    def on_stop_button_clicked(self):
        """Handle when click stop generate random value"""
        if self.time_repeat != 0:
            if self.is_stop_clicked:
                self.is_stop_clicked = False
                self.stop_button.setText("Stop")
            else:
                self.is_stop_clicked = True
                self.stop_button.setText("Resume")
        else:
            self.is_stop_clicked = False

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
            self.occupancy_value = int(
                device_status['reply'].get('occupancyValue'))
            if self.occupancy_value == 1:
                self.lbl_main_status_occupnacy.setText(
                    'Occupancy status: Occupied')
            else:
                self.lbl_main_status_occupnacy.setText(
                    'Occupancy status: Unoccupied')
            self.lbl_remain_repeat_time.setText(
                'Remaining count: ' + str(self.time_repeat))
            self.lbl_remaining_time_interval.setText(
                'Remaining time of interval: ' + str(self.remaining_time_interval) + " sec")
        except Exception as e:
            logging.error("Error: " + str(e))

    def on_value_status_changed(self):
        """
        Update occupany sensor value to matter device(backend)
        through rpc service
        """
        # logging.info('on_value_status_changed')
        if self.occupancy_value == 1:
            self.occupancy_value = 0
        else:
            self.occupancy_value = 1
        self.mutex.acquire(timeout=1)
        self.client.set({'occupancyValue': self.occupancy_value})
        self.mutex.release()

    def update_value_status(self):
        """
        Handle timer thread when start generate random value
        Emit signal value status changed
        """
        try:
            while self.check_condition_update_status(
                    self.update_value_status_thread):
                if (self.time_repeat > 0) and (not self.is_stop_clicked):
                    if self.remaining_time_interval > 0:
                        self.remaining_time_interval -= 1
                    else:
                        self.sig_value_status_changed.emit()
                        self.time_repeat -= 1
                        if self.time_repeat == 0:
                            self.set_time_button.setText("Start")
                            self.remaining_time_interval = 0
                        else:
                            self.remaining_time_interval = self.time_sleep
                elif self.time_repeat == 0:
                    self.set_time_button.setText("Start")
                    self.remaining_time_interval = 0
                time.sleep(1)
        except Exception as e:
            logging.error(str(e))

    def stop(self):
        """
        Stop thread update device state
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_status_thread()
        self.stop_update_state_thread()
        self.stop_client_rpc()
