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
import time
from rpc.window_client import WindowClient
from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/closures/")
OPERATION_WINDOW_TIMER = 5000

INCREASE_LIFT_STATUS = "Tilt: Currently not moving, \n                                    Lift: Currently opening"
INCREASE_TILT_STATUS = "Tilt: Currently opening, \n                                      Lift: Currently not moving"
INCREASE_LIFT_TILT_STATUS = "Tilt and Lift: Currently opening"
DECREASE_TILT_INCREASE_LIFT = "Tilt: Currently closing, \n                                      Lift: Currently opening"
DECREASE_LIFT_STATUS = "Tilt: Currently not moving, \n                                      Lift: Currently closing"
DECREASE_TILT_STATUS = "Tilt: Currently closing, \n                                      Lift: Currently not moving"
DECREASE_TILT_DECREASE_LIFT_STATUS = "Tilt and Lift: Currently closing"
DECREASE_LIFT_INCREASE_TILT_STATUS = "Tilt: Currently opening, \n                                      Lift: Currently closing"
STOP_MOVING_STATUS = "Tilt and Lift: Currently not moving"

INCREASE_LIFT = 5
INCREASE_TILT = 17
INCREASE_LIFT_TILT = 21
DECREASE_TILT_INCREASE = 37
DECREASE_LIFT = 10
DECREASE_TILT = 34
DECREASE_TILT_DECREASE = 42
DECREASE_LIFT_INCREASE = 26
STOP_MOVING = 0


class WindowCovering(BaseDeviceUI):
    """
    WindowCovering device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `WindowCovering` UI.
        :param parent: An UI object load WindowCovering device UI controller.
        """
        super().__init__(parent)
        self.timer_tilt = None
        self.timer_lift = None

        # Show Icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'window-covering.png')
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

        # Lift status
        self.lbl_main_lift = QLabel()
        self.lbl_main_lift.setText('Window : Close')
        self.lbl_main_lift.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_lift)

        # Tift status
        self.lbl_main_tilt = QLabel()
        self.lbl_main_tilt.setText('Tilt : 10°')
        self.lbl_main_tilt.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_tilt)

        # Show lift slider
        self.lb_lift = QLabel()
        self.lb_lift.setText('Lift')
        self.parent.ui.lo_controller.addWidget(self.lb_lift)
        self.lb_lift_value = QLabel()
        self.lb_lift_value.setText('0%')
        self.lb_lift_value.setAlignment(Qt.AlignCenter)

        self.sl_lift = QSlider()
        self.sl_lift.setRange(0, 100)
        self.sl_lift.setOrientation(Qt.Horizontal)
        self.sl_lift.valueChanged.connect(self.update_lb_lift)
        self.sl_lift.sliderPressed.connect(self.on_pressed_event)
        self.sl_lift.sliderReleased.connect(self.handle_lift_release)
        self.sl_lift.valueChanged.connect(self.handle_lift_value_change)

        # Show tilt slider
        self.lb_tilt = QLabel()
        self.lb_tilt.setText('Tilt')
        self.parent.ui.lo_controller.addWidget(self.lb_tilt)
        self.lb_tilt_value = QLabel()
        self.lb_tilt_value.setText('0°')
        self.lb_tilt_value.setAlignment(Qt.AlignCenter)

        self.sl_tilt = QSlider()
        self.sl_tilt.setRange(0, 100)
        self.sl_tilt.setOrientation(Qt.Horizontal)
        self.sl_tilt.valueChanged.connect(self.update_lb_tilt)
        self.sl_tilt.sliderReleased.connect(self.handle_tilt_release)
        self.sl_tilt.sliderPressed.connect(self.on_pressed_event)
        self.sl_tilt.valueChanged.connect(self.handle_tilt_value_change)

        # Layout widget
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.lb_lift, 0, 0)
        self.grid_layout.addWidget(self.lb_lift_value, 0, 1)
        self.grid_layout.addWidget(self.sl_lift, 1, 0)
        self.grid_layout.addWidget(self.lb_tilt, 2, 0)
        self.grid_layout.addWidget(self.lb_tilt_value, 2, 1)
        self.grid_layout.addWidget(self.sl_tilt, 3, 0)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        self.parent.ui.lo_controller.addWidget(QLabel())

        self.lb_operational_status = QLabel()
        self.lb_operational_status.setText('Operational Status: ')
        self.parent.ui.lo_controller.addWidget(self.lb_operational_status)

        # Init rpc
        self.client = WindowClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()
        logging.debug("Init Window done")

    def __del__(self):
        """Destructor of 'WindowCovering' object"""
        self.destroy_timer_window_covering()

    def on_pressed_event(self):
        """Slider perssed handler, enable 'is_on_control' attribute"""
        self.is_on_control = True

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {'liftPercent100': 0, 'tiltPercent100': 0}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("Can not set initial value: " + str(e))

    def update_lb_lift(self, value):
        """
        Update target lift percentage value for target lift percentage label
        :param value: Value of target lift percentage slider
        """
        self.lb_lift_value.setText(str(value) + "%")

    def update_lb_tilt(self, value):
        """
        Update target tilt percentage value for target tilt percentage label
        :param value: Value of target tilt percentage slider
        """
        self.lb_tilt_value.setText(str(value) + '°')

    def destroy_timer_window_covering(self):
        """Destroy lift timer object and tilt timer object"""
        self.destroy_timer_tilt()
        self.destroy_timer_lift()

    def destroy_timer_tilt(self):
        """Destroy lift timer object"""
        dict_data = self.__dict__
        if ('timer_tilt' in dict_data):
            if self.timer_tilt is not None:
                self.timer_tilt.stop()
                self.timer_tilt = None

    def destroy_timer_lift(self):
        """Destroy lift timer object"""
        dict_data = self.__dict__
        if ('timer_lift' in dict_data):
            if self.timer_lift is not None:
                self.timer_lift.stop()
                self.timer_lift = None

    def handle_lift_value_change(self):
        """
        Setup timer for setting current lift percentage after
        slider lift release in a interval
        Connect to slot function to set when timer timeout
        """
        self.timer_lift = QTimer()
        self.timer_lift.start(OPERATION_WINDOW_TIMER)
        self.timer_lift.timeout.connect(self.set_current_lift_position)

    def handle_tilt_value_change(self):
        """
        Setup timer for setting current tilt percentage after
        slider tilt release in a interval
        Connect to slot function to set when timer timeout
        """
        self.timer_tilt = QTimer()
        self.timer_tilt.start(OPERATION_WINDOW_TIMER)
        self.timer_tilt.timeout.connect(self.set_current_tilt_position)

    def set_current_lift_position(self):
        """
        Handle set current lift percentage after
        slider lift release in a interval
        """
        level_lift = round((100 - self.target_lift) * 100)
        if (self.client is not None):
            self.client.set({'current_position_lift_percent100': level_lift})
        self.destroy_timer_lift()

    def set_current_tilt_position(self):
        """
        Handle set current tilt percentage after
        slider tilt release in a interval
        """
        level_tilt = round((100 - self.target_tilt) * 100)
        if (self.client is not None):
            self.client.set({'current_position_tilt_percent100': level_tilt})
        self.destroy_timer_tilt()

    def handle_lift_release(self):
        """
        Handle set target lift percentage when slider tilt release
        """
        level_lift = round((100 - self.sl_lift.value()) * 100)
        logging.info("RPC SET lift level : " + str(level_lift))
        self.mutex.acquire(timeout=1)
        self.client.set({'liftPercent100': level_lift})
        self.mutex.release()
        self.is_on_control = False

    def handle_tilt_release(self):
        """
        Handle set target tilt percentage when slider tilt release
        """
        level_tilt = ((100 - self.sl_tilt.value()) * 100)
        logging.info("RPC SET tilt level : " + str(level_tilt))
        self.mutex.acquire(timeout=1)
        self.client.set({'tiltPercent100': level_tilt})
        self.mutex.release()
        self.is_on_control = False

    def handle_operational_status(self, op_status):
        """
        Handle operational status of window covering change
        :param op_status {int}: A new operational status of window covering
        """
        status_text = ""
        if (op_status == INCREASE_LIFT):
            status_text = INCREASE_LIFT_STATUS
        elif (op_status == INCREASE_TILT):
            status_text = INCREASE_TILT_STATUS
        elif (op_status == INCREASE_LIFT_TILT):
            status_text = INCREASE_LIFT_TILT_STATUS
        elif (op_status == DECREASE_TILT_INCREASE):
            status_text = DECREASE_TILT_INCREASE_LIFT
        elif (op_status == DECREASE_LIFT):
            status_text = DECREASE_LIFT_STATUS
        elif (op_status == DECREASE_TILT):
            status_text = DECREASE_TILT_STATUS
        elif (op_status == DECREASE_TILT_DECREASE):
            status_text = DECREASE_TILT_DECREASE_LIFT_STATUS
        elif (op_status == DECREASE_LIFT_INCREASE):
            status_text = DECREASE_LIFT_INCREASE_TILT_STATUS
        elif (op_status == STOP_MOVING):
            status_text = STOP_MOVING_STATUS
        return status_text

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
                self.target_lift = 100 - \
                    round(device_status['reply'].get('liftPercent100') / 100)
                self.target_tilt = 100 - \
                    round(device_status['reply'].get('tiltPercent100') / 100)
                self.sl_lift.setValue(int(self.target_lift))
                self.sl_tilt.setValue(int(self.target_tilt))
                if self.target_lift > 0:
                    self.lbl_main_lift.setText(
                        'Window : Open {}%'.format(
                            self.target_lift))
                else:
                    self.lbl_main_lift.setText('Window : Close')
                self.lbl_main_tilt.setText(
                    'Tilt : {}°'.format(self.target_tilt))

                self.cr_lift = 100 - \
                    round(device_status['reply'].get('currentPositionLiftPercent100') / 100)
                self.cr_tilt = 100 - \
                    round(device_status['reply'].get('currentPositionTiltPercent100') / 100)

                self.op_status = (
                    device_status['reply'].get('operationalStatus'))
                status = self.handle_operational_status(self.op_status)
                self.lb_operational_status.setText(
                    'Operational Status({}): {}'.format(
                        self.op_status, status))
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
        Stop thread update device state
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
