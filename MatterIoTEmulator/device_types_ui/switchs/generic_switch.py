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
from qtwidgets import Toggle, AnimatedToggle
import logging
import threading
import os
from threading import Timer
import time
from rpc.lighting_client import LightingClient
from rpc.generic_switch_client import GenericSwitchClient

from ..stoppablethread import UpdateStatusThread
from constants import *
from ..device_base_ui import *


SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/switchs/")


SHORT_PRESS = 'ShortPress'
LONG_PRESS = 'LongPress'
MULTI_PRESS = 'MultiPress'
PRESS_MESS = 'Click to select press:'

INDEX_LATCHING = 0
INDEX_SWITCH = 1
INDEX_SWITCH_RELEASE = 2
INDEX_SWITCH_LONG = 3
INDEX_SWITCH_MULTI = 4

NUMBER_OF_POSITIONS = 2
MULTI_PRESS_MAX = 2

TIME_INIT_SHORT = 1000
TIME_INIT_LONG = 2000
TIME_GOING_MULTI = 1000
TIME_COMPLETE_MULTI = 2000


class GenericSwitch(BaseDeviceUI):
    """
    GenericSwitch device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """
    event_short_release = Signal()
    event_long_press = Signal()
    event_multi_press_going = Signal()
    event_multi_press_complete = Signal()

    def __init__(self, parent) -> None:
        """
        Create a new `GenericSwitch` UI.
        :param parent: An UI object load GenericSwitch device UI controller.
        """
        super().__init__(parent)
        self.cr_feature_type = 0
        self.number_of_press = 0
        self.current_position = 1
        self.switch_press_list = []
        self.is_multi = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'generic_switch.png')
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

        # Current position
        self.lbl_main_status = QLabel()
        self.lbl_main_status.setText('Postision : ')
        self.lbl_main_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_main_status)

        # Switch feature
        self.lbl_switch_mod = QLabel()
        self.lbl_switch_mod.setText('Feature Map')
        self.parent.ui.lo_controller.addWidget(self.lbl_switch_mod)

        switch_list = [
            "LatchingSwitch",
            "MomentarySwitch",
            "MomentarySwitchRelease",
            "MomentarySwitchLongPress",
            "MomentarySwitchMultiPress"]
        self.switch_box = QComboBox()
        self.switch_box.addItems(switch_list)
        # Connect the currentIndexChanged signal to a slot
        self.switch_box.currentIndexChanged.connect(
            self.handle_switch_feature_changed)
        self.parent.ui.lo_controller.addWidget(self.switch_box)

        # Switch button
        self.sw_title_on = QLabel()
        self.sw_title_on.setText('Switch')
        self.sw_on_off = AnimatedToggle(
            checked_color="#FFB000", pulse_checked_color="#44FFB000")
        self.sw_on_off.setFixedSize(60, 40)
        self.sw_on_off.autoRepeatDelay()
        logging.info(self.sw_on_off.autoRepeat())

        self.on_layout = QVBoxLayout()
        self.sw_on_off.stateChanged.connect(self.handle_position_changed)
        self.on_layout.addWidget(self.sw_title_on)
        self.on_layout.addWidget(self.sw_on_off)
        self.parent.ui.lo_controller.addLayout(self.on_layout)

        self.lb_title = QLabel()
        self.lb_title.setText('')
        self.parent.ui.lo_controller.addWidget(self.lb_title)

        # Show control button/switch
        self.event_short_release.connect(self.short_release)
        self.event_long_press.connect(self.long_press)
        self.event_multi_press_going.connect(self.multi_press_on_going)
        self.event_multi_press_complete.connect(self.multi_press_complete)

        # Init rpc
        self.client = GenericSwitchClient(self.config)
        self.set_initial_value()
        self.start_update_device_status_thread()

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'genericSwitch': {
                    'numberOfPositions': NUMBER_OF_POSITIONS,
                    'multiPressMax': MULTI_PRESS_MAX,
                    'currentPosition': 1,
                    'numberOfPress': 0},
                'featureMap': {
                    'featureMap': 0}}
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.info("can not set initial value: " + str(e))

    def handle_switch_feature_changed(self, mode):
        """
        Handle set switch feature map attribute to matter device(backend)
        through rpc service and display UI respectively
        when select feature of switch combo box
        :param mode: Current index of switch combo box
        """
        self.mutex.acquire(timeout=1)
        self.current_position = 0
        self.client.set(
            {
                'genericSwitch': {
                    'numberOfPositions': NUMBER_OF_POSITIONS,
                    'multiPressMax': MULTI_PRESS_MAX,
                    'currentPosition': self.current_position,
                    'numberOfPress': 0},
                'featureMap': {
                    'featureMap': mode}})
        self.mutex.release()
        self.clear_layout()
        if mode == 0:
            self.sw_title_on = QLabel()
            self.sw_title_on.setText('Switch')
            self.sw_on_off = AnimatedToggle(
                checked_color="#FFB000", pulse_checked_color="#44FFB000")
            self.sw_on_off.setFixedSize(60, 40)
            self.sw_on_off.autoRepeatDelay()
            logging.info(self.sw_on_off.autoRepeat())
            self.sw_on_off.stateChanged.connect(self.handle_position_changed)
            self.on_layout.addWidget(self.sw_title_on)
            self.on_layout.addWidget(self.sw_on_off)
        else:
            self.lbl_momentary = QLabel()
            self.lbl_momentary.setText('Switch Press')
            self.parent.ui.lo_controller.addWidget(self.lbl_momentary)

            switch_press_list = self.get_pressbox()
            self.switch_press_box = QComboBox()
            self.switch_press_box.addItems(switch_press_list)
            # Connect the currentIndexChanged signal to a slot
            self.switch_press_box.currentIndexChanged.connect(
                self.handle_switch_press_changed)

            self.lbl_event = QLabel()
            self.lbl_event.setText('Switch status : No Event')

            self.on_layout.addWidget(self.lbl_momentary)
            self.on_layout.addWidget(self.switch_press_box)
            self.on_layout.addWidget(self.lbl_event)

    def get_pressbox(self):
        """
        Handle set 'switch_press_list' contain all support press types
        when switch feature change
        """
        index_switch_box = self.switch_box.currentIndex()
        if index_switch_box == INDEX_SWITCH:
            # self.switch_press_list =[PRESS_MESS, SHORT_PRESS, LONG_PRESS, MULTI_PRESS]
            self.switch_press_list = [PRESS_MESS, SHORT_PRESS]
        elif index_switch_box == INDEX_SWITCH_RELEASE:
            self.switch_press_list = [PRESS_MESS, SHORT_PRESS]
        elif index_switch_box == INDEX_SWITCH_LONG:
            self.switch_press_list = [PRESS_MESS, SHORT_PRESS, LONG_PRESS]
        elif index_switch_box == INDEX_SWITCH_MULTI:
            self.switch_press_list = [PRESS_MESS, SHORT_PRESS, MULTI_PRESS]
        return self.switch_press_list

    def handle_switch_press_changed(self, mode_press):
        """
        Call handler function corressponding to
        current switch feature and mode press
        """
        index_switch_box = self.switch_box.currentIndex()
        self.lbl_event.setText('Switch status :Switch is being pressed!')
        if index_switch_box == INDEX_SWITCH:
            if mode_press == 1:
                self.on_click_short_press()
            elif mode_press == 2:
                self.on_click_long_press()
            elif mode_press == 3:
                self.on_click_multi_press()
        elif index_switch_box == INDEX_SWITCH_RELEASE:
            if mode_press == 1:
                self.on_click_short_press()
            elif mode_press == 2:
                self.on_click_long_press()
            elif mode_press == 3:
                self.on_click_multi_press()
        elif index_switch_box == INDEX_SWITCH_LONG:
            if mode_press == 1:
                self.on_click_short_press()
            elif mode_press == 2:
                self.on_click_long_press()
        elif index_switch_box == INDEX_SWITCH_MULTI:
            if mode_press == 1:
                self.on_click_short_press()
            elif mode_press == 2:
                self.on_click_multi_press()

    def clear_layout(self):
        """Destroy UI object when change switch feature"""
        while self.on_layout.count():
            layout_item = self.on_layout.takeAt(0)
            if layout_item.widget():
                layout_item.widget().deleteLater()

    def handle_position_changed(self, data):
        """
        Handle set current position attributes
        to matter device(backend) through rpc service
        when switch latch position change
        :param data: Current positionof switch latch feature
        """
        logging.info("RPC SET Position: " + str(data))
        self.mutex.acquire(timeout=1)
        if data == 0:
            self.current_position = 0
        else:
            self.current_position = 1
        rpc_data = {
            'genericSwitch': {
                'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX,
                'currentPosition': self.current_position}}
        self.client.set(rpc_data)
        self.client.OnSwitchLatch(rpc_data)
        self.mutex.release()

    def init_press(self):
        """Set event Initial Press to matter device through rpc service"""
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 1}})
        self.client.OnInitialPress(data)
        self.client.set(data)

    def short_release(self):
        """Set event Short Release to matter device through rpc service"""
        if self.is_multi:
            self.set_default_press_box_index()
            self.lbl_event.setText('Switch status :Switch is released!')

        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 1}})
        self.client.OnShortRelease(data)
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 0}})
        self.client.set(data)

    def long_press(self):
        """Set event Long Press to matter device through rpc service"""
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 1}})
        self.client.OnLongPress(data)
        self.client.set(data)
        self.long_release()
        self.set_default_press_box_index()
        self.lbl_event.setText('Switch status : Switch is released!')

    def long_release(self):
        """Set event Long Release to matter device through rpc service"""
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 1}})
        self.client.OnLongRelease(data)
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                'multiPressMax': MULTI_PRESS_MAX, 'currentPosition': 0}})
        self.client.set(data)

    def multi_press_on_going(self):
        """Set event Multi Press on going to matter device through rpc service"""
        self.number_of_press = 1
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                                   'multiPressMax': MULTI_PRESS_MAX,
                                   'currentPosition': 1,
                                   'numberOfPress': self.number_of_press}})
        self.client.OnMultiPressOngoing(data)
        self.client.set(data)

    def multi_press_complete(self):
        """Set event Multi Press complete to matter device through rpc service"""
        self.short_release()
        self.number_of_press = 2
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                                   'multiPressMax': MULTI_PRESS_MAX,
                                   'currentPosition': 1,
                                   'numberOfPress': self.number_of_press}})
        self.client.OnMultiPressComplete(data)
        data = ({'genericSwitch': {'numberOfPositions': NUMBER_OF_POSITIONS,
                                   'multiPressMax': MULTI_PRESS_MAX,
                                   'currentPosition': 0,
                                   'numberOfPress': self.number_of_press}})
        self.client.set(data)
        self.set_default_press_box_index()
        self.lbl_event.setText('Switch status :Switch is released!')

    def emit_short_release_signal(self):
        """Emit signal short release, destroy press timer"""
        logging.info("Emit short_release")
        self.event_short_release.emit()
        self.destroy_timer(self.press_timer, "press_timer")

    def emit_long_press_signal(self):
        """Emit signal long press, destroy press timer"""
        logging.info("Emit long_press")
        self.event_long_press.emit()
        self.destroy_timer(self.press_timer, "press_timer")

    def emit_multi_press_going_signal(self):
        """Emit signal multi press on going, destroy press timer"""
        logging.info("Emit emit_multi_press_going_signal")
        self.event_multi_press_going.emit()
        self.destroy_timer(
            self.multi_press_timer_going,
            "multi_press_timer_going")

    def emit_multi_press_complete_signal(self):
        """Emit signal multi press complete, destroy press timer"""
        logging.info("Emit emit_multi_press_complete_signal")
        self.event_multi_press_complete.emit()
        self.destroy_timer(
            self.multi_press_timer_complete,
            "multi_press_timer_complete")
        self.set_default_press_box_index()

    def destroy_timer(self, timer, timer_name):
        """
        Destroy timer object corresspods to timer_name
        :param timer: timer instance object
        :param timer_name: timer attribute name
        """
        dict_data = self.__dict__
        if (timer_name in dict_data):
            if (timer is not None):
                logging.info("Destroy timer " + str(timer_name))
                timer.stop()
                timer = None

    def set_default_press_box_index(self):
        """Set press box index to default value 0"""
        self.switch_press_box.setCurrentIndex(0)

    def handle_press_timer_timeout(self, time, handle_timeout):
        """
        Setup timer object and
        handle timeout signal connect to callback function handle_timeout
        """
        self.press_timer = QTimer(self)
        self.press_timer.start(time)
        self.press_timer.timeout.connect(handle_timeout)

    def on_click_short_press(self):
        """Handle emit signal when select to short press"""
        self.is_multi = True
        logging.info("ShortPress")
        self.init_press()
        self.handle_press_timer_timeout(
            TIME_INIT_SHORT, self.emit_short_release_signal)

    def on_click_long_press(self):
        """Handle emit signal when select to long press"""
        logging.info("LongPress")
        self.init_press()
        self.handle_press_timer_timeout(
            TIME_INIT_LONG, self.emit_long_press_signal)

    def on_click_multi_press(self):
        """Handle emit signal when select to multi press"""
        logging.info("MultiPress")
        self.is_multi = False
        self.init_press()
        self.handle_press_timer_timeout(
            TIME_INIT_SHORT, self.emit_short_release_signal)

        self.multi_press_timer_going = QTimer(self)
        self.multi_press_timer_going.start(TIME_GOING_MULTI)
        self.multi_press_timer_going.timeout.connect(
            self.emit_multi_press_going_signal)

        self.multi_press_timer_complete = QTimer(self)
        self.multi_press_timer_complete.start(TIME_COMPLETE_MULTI)
        self.multi_press_timer_complete.timeout.connect(
            self.emit_multi_press_complete_signal)

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
                if (self.cr_feature_type !=
                        device_status['reply']['featureMap']['featureMap']):
                    self.cr_feature_type = device_status['reply']['featureMap']['featureMap']
                    self.switch_box.setCurrentIndex(self.cr_feature_type)

                index_switch_box = self.switch_box.currentIndex()
                self.current_position = int(
                    device_status['reply']['genericSwitch']['currentPosition'])
                if index_switch_box == 0:
                    if self.current_position == 1:
                        self.sw_on_off.setCheckState(Qt.Checked)
                    else:
                        self.sw_on_off.setCheckState(Qt.Unchecked)
                self.lbl_main_status.setText(
                    'Current Postision : {}'.format(
                        self.current_position))
        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
