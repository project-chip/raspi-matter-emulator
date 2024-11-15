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


import time
import datetime
from datetime import date
import subprocess
import shlex
import re
import configparser
import shutil

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from ui.ui_matter import Ui_Matter
from ui.ui_widget import OverlayWidget
import sys
from sys import exit as sysExit
import json
import platform
from threading import Thread, Timer
import logging
import os
from typing import Optional
import qrcode
from PIL import Image

from utils.network_interface_priority import *
from utils.device_runner import DeviceRunner
from utils.getIP import CreateIpAddress
from utils.handle_recover import HandleRecoverDevices
from constants import *

# Import lighting device types
from device_types_ui.lighting.on_off_light import OnOffLight
from device_types_ui.lighting.dimmable_light import DimmableLight
from device_types_ui.lighting.color_temperature_light import ColorTemperatureLight
from device_types_ui.lighting.extended_color_light import ExtendedColorLight
# Import smart plug device types
from device_types_ui.smart_plug.on_off_plugin_unit import OnOffPluginUnit
from device_types_ui.smart_plug.dimmable_plugin_unit import DimmablePluginUnit
# Import Pump device types
from device_types_ui.pump.pump import Pump
# Import Sensor device types
from device_types_ui.sensors.contact_sensor import ContactSensor
from device_types_ui.sensors.flow_sensor import FlowSensor
from device_types_ui.sensors.humidity_sensor import HumiditySensor
from device_types_ui.sensors.light_sensor import LightSensor
from device_types_ui.sensors.occupancy_sensor import OccupancySensor
from device_types_ui.sensors.temperature_sensor import TemperatureSensor
from device_types_ui.sensors.pressure_sensor import PressureSensor
from device_types_ui.sensors.air_quality_sensor import AirQualitySensor
from device_types_ui.sensors.smoke_co_alarm import SmokeCoAlarm


from device_types_ui.closures.door_lock import DoorLock
from device_types_ui.closures.window_covering import WindowCovering
from device_types_ui.HVAC.fan import Fan
from device_types_ui.HVAC.thermostat import Thermostat
from device_types_ui.HVAC.heating_cooling_unit import HeatingCooling
from device_types_ui.HVAC.air_purifier import AirPurifier
from credentials.development.gen_dac_cert import GenDacTool

from device_types_ui.appliances.laundry_washer import LaundryWasher
from device_types_ui.appliances.room_air_conditioner import RoomAirConditioner
from device_types_ui.appliances.dishwasher import Dishwasher
from device_types_ui.appliances.refrigerator import Refrigerator

from device_types_ui.robotic.robotic_vacuum_cleaner import RobotVacuum
from device_types_ui.switchs.generic_switch import GenericSwitch

from setup_payload.generate_setup_payload import CommissioningFlow, SetupPayload

SOURCE_PATH = os.path.dirname(os.path.realpath(__file__))
RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/")
CONFIG_FILE_PATH = os.path.join(SOURCE_PATH, CONFIG_FILE)
DEVICE_LIST_PATH = os.path.join(SOURCE_PATH, "res/config/deviceList.dat")
NETWORK_INFO_PATH = SOURCE_PATH + LOG_PATH


class Worker(QThread):
    """
    Worker class definition for creating a Thread.
    """
    connect_status = Signal(int)
    onboarding_code = Signal(str, str)
    generate_ip_done = Signal()

    def __init__(self, parent=None):
        """
        Initialize a Worker thread instance.

        Arguments:
            parent {Object} -- the parent object of this thread
        """
        QThread.__init__(self)
        self.parent = parent
        pass

    # generate ip function
    def run(self):
        """
        Starting the Worker thread.
        """
        logging.info(".............Start generate ip............")
        list_ip = []
        self.connect_status.emit(STT_IP_GENERATE_STARTING)
        startTime = time.perf_counter()
        self.parent.generateIp_done = False
        self.parent.ip_value = CreateIpAddress()
        self.parent.targetId = self.parent.generate_targetId()

        if (self.parent.ipv4 != "" and self.parent.ipv6 != ""):
            list_ip.append(self.parent.ipv4)
            list_ip.append(self.parent.ipv6)

        if len(list_ip) == 2:
            if ((not self.parent.ip_value.pingOnlyOne(self.parent.ipv4)) or (
                    not self.parent.ip_value.pingOnlyOne(self.parent.ipv6))):
                self.parent.generateIp_done = True
                self.connect_status.emit(STT_RECOVER_FAIL)
                HandleRecoverDevices.set_is_click_from_callback(False)
                self.parent.notify_recover_done()
                return
            self.parent.ip_value.is_base_ip = False
            # Get interface index from recover device
            self.parent.ip_value.interface_index = self.parent.interface_index
        else:
            self.parent.ip_value.is_base_ip = True

        logging.info(
            "List ip recover: {},  is base ip: {}".format(
                list_ip, self.parent.ip_value.is_base_ip))
        self.parent.scan_ip = self.parent.ip_value.scanAndCreateIp(list_ip)
        self.parent.ipv4 = self.parent.ip_value.getIpv4Address()
        self.parent.ipv6 = self.parent.ip_value.getIpv6Address()
        self.parent.interfaceName = self.parent.ip_value.interface
        self.parent.interface_index = self.parent.ip_value.interface_index

        if ((len(self.parent.ipv4) > 0) and (len(self.parent.ipv6) > 0)):
            while ((not self.parent.generateIp_done) and (self.parent.ip_value.pingOnlyOne(
                    self.parent.ipv6) or self.parent.ip_value.pingOnlyOne(self.parent.ipv4))):
                # Waitting
                endTime = time.perf_counter()
                if (int(endTime - startTime) > 60):
                    break
        self.parent.generateIp_done = True
        self.generate_ip_done.emit()
        endTime = time.perf_counter()
        logging.info(".............Completed generate ip............after {} seconds".format(
            int(endTime - startTime)))

    def __del__(self):
        """
        Finishing the Worker thread.
        """
        self.wait()


class ULongValidator(QValidator):
    """
    ULongValidator class definition for validating the input data
    """

    def __init__(self, max=9223372036854775807):
        """
        Initialize a ULongValidator instance.

        Arguments:
            max {ulong} -- the maximum of input value
        """
        super().__init__()
        self.regex = QRegExp("^[1-9][0-9]{0,18}$")
        self.max_value = max

    def validate(self, input_str, pos):
        """
        Validate a Worker thread instance.

        Arguments:
            input_str {str} -- the input string
            pos {str} -- the position need to be validated
        """
        if input_str == "":
            return (QValidator.Acceptable, input_str, pos)
        elif self.regex.exactMatch(input_str):
            value = int(input_str)
            if value > self.max_value:
                return (QValidator.Invalid, input_str, pos)
            else:
                return (QValidator.Acceptable, input_str, pos)
        else:
            return (QValidator.Invalid, input_str, pos)


class MainWindow(QMainWindow):
    """
    MainWindow class definition for creating emulator
    """
    ip_value: Optional[CreateIpAddress]

    device_changed = Signal(str)
    device_started = Signal(str)
    device_stopped = Signal(str)
    device_recover_done = Signal()

    global list_device_connect, list_tab, list_status_device
    list_device_connect = []
    list_tab = []
    list_status_device = []

    def __init__(self):
        """
        Initialize a MainWindow instance.
        """
        super(MainWindow, self).__init__()
        self.config_logging(TEST_MODE)
        self._runner = None
        self.is_rpc_timer_running = False
        self.get_app_version()
        self.ui = Ui_Matter()
        self.ui.setupUi(self)
        self.wkr = Worker(parent=self)
        self.update_ui()
        self.update_label_constraints()
        self.qrcode = ""
        self.manual_code = ""
        self.path_log = ""

        # get IP
        self.ip_value = None
        self.ipv4 = ""
        self.ipv6 = ""
        self.targetId = ""
        self.rpcPort = 33000
        self.rpc_port_default = 33000
        self.generateIp_done = False
        self.isIPBindFail = False
        self.check_recover = False
        self.create_time = int(time.time())
        self.interface_index = 0
        self.is_recover = 0
        self.unique_id = 0
        self.today = date.today()
        self.handle_recover_devices = HandleRecoverDevices()
        self.payloads = SetupPayload()

        # Bind event
        self.resizeEvent = self.on_resize_event
        self.ui.cbb_device_selection.currentTextChanged.connect(
            self.update_settings)
        self.ui.txt_serial_number.textChanged.connect(self.update_settings)
        self.ui.txt_vendorid.textChanged.connect(self.update_settings)
        self.ui.txt_productid.textChanged.connect(self.update_settings)
        self.ui.txt_discriminator.textChanged.connect(self.update_settings)
        self.ui.txt_pincode.textChanged.connect(self.update_settings)
        self.ui.btn_start_device.clicked.connect(self.on_click_start_device)
        self.wkr.connect_status.connect(self.update_connect_status)
        self.wkr.onboarding_code.connect(self.gen_qrcode)
        self.wkr.generate_ip_done.connect(self.start_device_running_thread)

        self.ui.cbb_device_selection.currentIndexChanged.connect(
            self.notify_device_changed)
        self.connected_device = False

    def create_date(self):
        """
        Create a folder as date.

        Raises:
            Exception: if folder creation has an error
        """
        try:
            path_date = SOURCE_PATH + "/log/" + str(self.today)
            os.mkdir(path_date)
        except Exception as e:
            pass

    def get_idDevice(self, name_device):
        """
        Return id of a device.

        Arguments:
            name_device {str} -- the device name
        """
        patter = '[\\dxA-F]+'
        value = re.findall(patter, name_device)[-1]
        return value

    def save_deviceConnect(self, name_device):
        """
        Save a device to the list device connected.

        Arguments:
            name_device {str} -- the device name
        """
        value = (self.get_idDevice(name_device))
        list_device_connect.append(value)
        logging.info(value + " Value")

    def remove_info_list(self, name_device):
        """
        Remove a device from the list device connected.

        Arguments:
            name_device {str} -- the device name
        """
        value = self.get_idDevice(name_device)
        logging.info(value + " Value remove")
        if value in list_device_connect:
            list_device_connect.remove(value)
        else:
            pass

    def notify_device_changed(self):
        """
        Notify device changed.
        """
        self.device_changed.emit(
            self.ui.cbb_device_selection.currentText()[:-8])

    def notify_device_started(self):
        """
        Notify device started.
        """
        self.device_started.emit(self.generate_targetId())

    def notify_device_stopped(self):
        """
        Notify device stopped.
        """
        self.device_stopped.emit(self.targetId)

    def notify_recover_done(self):
        """
        Notify recover done.
        """
        self.device_recover_done.emit()

    def update_ui(self):
        """
        Update on UI emulator.
        """
        # Update window title
        self.setWindowIcon(QIcon(RESOURCE_PATH + '/icons/matter_icon.jpg'))
        self.setWindowTitle(
            "Matter IoT Emulator v{}".format(
                self.get_app_version()))

        # Update window size
        settings = QSettings("LGE.HE.TSC", "MatterIoTEmulator")
        w = settings.value("width")
        if not w:
            w = 640
        h = settings.value("height")
        if not h:
            h = 480
        self.resize(int(w), int(h))

        # Update device type list
        for device in self.get_device_types():
            self.ui.cbb_device_selection.addItem(device)
        # Set device type
        self.ui.cbb_device_selection.setCurrentText(
            settings.value("cbb_device_selection", "On/Off Light(0x0100)"))

        # Hide QR
        self.ui.lbl_qr_image.hide()
        self.ui.lbl_qr_code.hide()

        # Set value from QSettings
        self.ui.txt_serial_number.setText(str(self.generate_serial_number()))
        self.ui.txt_vendorid.setText(settings.value("txt_vendorid", "65521"))
        self.ui.txt_productid.setText(settings.value("txt_productid", "32788"))
        self.ui.txt_discriminator.setText(settings.value("txt_discriminator", "3840"))
        self.ui.txt_pincode.setText(settings.value("txt_pincode", "20202021"))

        # Accept number only
        validator = ULongValidator(MAX_SERIAL_NUMBER)
        self.ui.txt_serial_number.setValidator(validator)
        self.ui.txt_vendorid.setValidator(QIntValidator(0, MAX_VID, self))
        self.ui.txt_productid.setValidator(QIntValidator(0, MAX_PID, self))
        self.ui.txt_discriminator.setValidator(QIntValidator(0, MAX_DISCRIMINATOR, self))
        self.ui.txt_pincode.setValidator(QIntValidator(0, MAX_PINCODE, self))

        # Set button name/ icon
        self.ui.btn_start_device.setText("Start Device")
        self.ui.btn_start_device.setIcon(
            QIcon(RESOURCE_PATH + "/icons/start_icon.png"))

        # Set connection's status
        self.update_status(
            "Not connected.",
            RED,
            "Please select device type for commissioning.",
            BLACK)

    def generate_serial_number(self):
        settings = QSettings("LGE.HE.TSC", "MatterIoTEmulator")
        list_running_device = [device.split('-')[-1] for device in self.get_list_device_from_file()]
        temp_serial = int(settings.value("txt_serial_number", "2021")) + 1
        if temp_serial > MAX_SERIAL_NUMBER:
            temp_serial = 1
        settings.setValue("txt_serial_number", temp_serial)
        if hex(temp_serial)[2:] not in list_running_device:
            return temp_serial
        else:
            return self.generate_serial_number()

    def update_settings(self):
        """
        Update on setting.
        """
        settings = QSettings("LGE.HE.TSC", "MatterIoTEmulator")
        settings.setValue("width", self.width())
        settings.setValue("height", self.height())
        settings.setValue(
            "txt_serial_number",
            self.ui.txt_serial_number.text())
        settings.setValue("txt_vendorid", self.ui.txt_vendorid.text())
        settings.setValue("txt_productid", self.ui.txt_productid.text())
        settings.setValue(
            "txt_discriminator",
            self.ui.txt_discriminator.text())
        settings.setValue("txt_pincode", self.ui.txt_pincode.text())
        if self.ui.cbb_device_selection.count() != 0:
            settings.setValue(
                "cbb_device_selection",
                self.ui.cbb_device_selection.currentText())
        self.check_parameter_constraints()

    def on_resize_event(self, ev):
        """
        Update when a resize event happening.
        """
        self.update_settings()

    def update_connect_status(self, connect_status):
        """
        Update connect status.
        """
        logging.debug("update_connect_status")
        if connect_status == STT_DISCONNECTED:
            self.update_status(
                "Not connected.",
                RED,
                "Please select device type for commissioning.",
                BLACK)
        elif connect_status == STT_DAC_GENERATE_STARTING:
            self.update_status(
                "Start generating DAC,",
                YELLOW,
                "Please check it again!",
                BLACK)
        elif connect_status == STT_IP_GENERATE_FAIL:
            self.update_status(
                " Fail to create IP ",
                RED,
                "Please check your internet connection!",
                BLACK)
            self.ui.btn_start_device.setText("Start Device")
            self.ui.btn_start_device.setIcon(
                QIcon(RESOURCE_PATH + "/icons/start_icon.png"))
            self.ui.lbl_qr_image.hide()
            self.ui.lbl_qr_code.hide()
            self.clear_layout(self.ui.lo_controller)
            if len(list_status_device) > 0:
                list_status_device.remove(1)
        elif connect_status == STT_DAC_GENERATE_FAIL:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status("Fail to create DAC!", RED, "", BLACK)
        elif connect_status == STT_DAC_GENERATED:
            self.update_status(
                "The DAC files were successfully created!",
                GREEN,
                "",
                BLACK)
        elif connect_status == STT_DEVICE_DUPLICATE:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status(
                "Device already exists.",
                RED,
                "Please check the device information again!",
                BLACK)
        elif connect_status == STT_DEVICE_UNSUPPORTED:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status(
                "Target device type is currently not supported.",
                RED,
                "Please select other device type",
                BLACK)
        elif connect_status == STT_DEVICE_STARTING:
            self.update_status(
                "Device is generating QR code!",
                YELLOW,
                "Please wait...",
                BLACK)
            self.timeqr = Timer(20, self.re_gennerate_qr)
            if (not self.isDeviceStarted):
                self.timeqr.start()
        elif connect_status == STT_DEVICE_STARTED:
            self.update_status(
                "Device started.",
                GREEN,
                "You can start commission",
                BLACK)
        elif connect_status == STT_CONNECTING:
            self.update_status("", RED, "Commissioning...", GREEN)
        elif connect_status == STT_COMMISSIONING_FAIL_BLUETOOTH:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status(
                "Bluez notify CHIPoBluez connection disconnected",
                RED,
                "Please stop and start the device again",
                BLACK)
        elif connect_status == STT_CONNECTED:
            self.update_status(
                "", RED, "Device is connected succesfully!", GREEN)
            self.ui.lbl_qr_image.hide()
            self.ui.lbl_qr_code.hide()
            self.show_controller()
            if len(list_status_device) > 0:
                list_status_device.remove(1)
        if connect_status == STT_COMMISSIONING_FAIL:
            self.update_status(
                "Failed to commissioning.",
                RED,
                "Please recomissioning again!",
                BLACK)
            if len(list_status_device) > 0:
                list_status_device.remove(1)
        elif connect_status == STT_IP_GENERATE_STARTING:
            self.update_status(
                "WAITING",
                YELLOW,
                "Device is generating IP!",
                BLACK)
        elif connect_status == STT_IP_GENERATED:
            self.update_status("Done", GREEN, "Device generated IP!", BLACK)
        elif connect_status == STT_BIND_IP_FAIL_BACKEND:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status(
                "Bind IP fail in backend",
                RED,
                "Please stop and start the device again",
                BLACK)
        elif connect_status == STT_WAITING_RUNING_DEVICE:
            self.update_status(
                "Please wait for a few seconds",
                YELLOW,
                "Another device is ready to commissioning!",
                BLACK)
        elif connect_status == STT_RPC_INIT_FAIL:
            if len(list_status_device) > 0:
                list_status_device.remove(1)
            self.update_status(
                "RPC Init fail",
                RED,
                "Please stop and start the device again",
                BLACK)
        elif connect_status == STT_RECOVER_FAIL:
            self.update_status(
                "IP of this recover device was be used",
                RED,
                "Please recover this device when IP be available",
                BLACK)
            self.stop_device()

    def show_controller(self):
        """
        Show controller on UI emulator.
        """
        self.current_device_type = self.ui.cbb_device_selection.currentText()
        if self.current_device_type == "Dimmable Light(0x0101)":
            self.ctrl = DimmableLight(self)
        elif self.current_device_type == "On/Off Light(0x0100)":
            self.ctrl = OnOffLight(self)
        elif self.current_device_type == "Color Temperature Light(0x010C)":
            self.ctrl = ColorTemperatureLight(self)
        elif self.current_device_type == "Extended Color Light(0x010D)":
            self.ctrl = ExtendedColorLight(self)
        elif self.current_device_type == "On/Off Plug-in Unit(0x010A)":
            self.ctrl = OnOffPluginUnit(self)
        elif self.current_device_type == "Dimmable Plug-in Unit(0x010B)":
            self.ctrl = DimmablePluginUnit(self)
        elif self.current_device_type == "Pump(0x0303)":
            self.ctrl = Pump(self)
        elif self.current_device_type == "Contact Sensor(0x0015)":
            self.ctrl = ContactSensor(self)
        elif self.current_device_type == "Light Sensor(0x0106)":
            self.ctrl = LightSensor(self)
        elif self.current_device_type == "Occupancy Sensor(0x0107)":
            self.ctrl = OccupancySensor(self)
        elif self.current_device_type == "Temperature Sensor(0x0302)":
            self.ctrl = TemperatureSensor(self)
        elif self.current_device_type == "Pressure Sensor(0x0305)":
            self.ctrl = PressureSensor(self)
        elif self.current_device_type == "Flow Sensor(0x0306)":
            self.ctrl = FlowSensor(self)
        elif self.current_device_type == "Humidity Sensor(0x0307)":
            self.ctrl = HumiditySensor(self)
        elif self.current_device_type == "Door Lock(0x000A)":
            self.ctrl = DoorLock(self)
        elif self.current_device_type == "Window Covering(0x0202)":
            self.ctrl = WindowCovering(self)
        elif self.current_device_type == "Fan(0x002B)":
            self.ctrl = Fan(self)
        elif self.current_device_type == "Thermostat(0x0301)":
            self.ctrl = Thermostat(self)
        elif self.current_device_type == "HeatingCoolingUnit(0x0300)":
            self.ctrl = HeatingCooling(self)
        elif self.current_device_type == "Air Purifier(0x002D)":
            self.ctrl = AirPurifier(self)
        elif self.current_device_type == "Air Quality Sensor(0x002C)":
            self.ctrl = AirQualitySensor(self)
        elif self.current_device_type == "Dishwasher(0x0075)":
            self.ctrl = Dishwasher(self)
        elif self.current_device_type == "Laundry Washer(0x0073)":
            self.ctrl = LaundryWasher(self)
        elif self.current_device_type == "Room Air Conditioner(0x0072)":
            self.ctrl = RoomAirConditioner(self)
        elif self.current_device_type == "Refrigerator(0x0070)":
            self.ctrl = Refrigerator(self)
        elif self.current_device_type == "Smoke&Carbon Alarm(0x0076)":
            self.ctrl = SmokeCoAlarm(self)
        elif self.current_device_type == "Robot Vaccum Cleaner(0x0074)":
            self.ctrl = RobotVacuum(self)
        elif self.current_device_type == "Generic Switch(0x000F)":
            self.ctrl = GenericSwitch(self)
        else:
            logging.info(self.ui.cbb_device_selection.currentText())
            self.update_status(
                "This device's controller is not supported yet.",
                RED,
                "Please select other device types.",
                BLACK)

    def check_attr_exist(self, attr):
        """
        Check a attribute exist or not.

        Arguments:
            attr {str} -- the attribute need to be checked
        Return:
            True: if attribute is existsed
            False: if attribute is not existsed
        """
        dict_data = self.__dict__
        if (attr in dict_data):
            return True
        else:
            return False

    def clear_widgets(self, layout):
        """
        Clear the memory of widget.

        Arguments:
            layout {Object} -- the widget object
        """
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.deleteLater()
            elif layoutItem.spacerItem() is not None:
                pass
            else:
                layoutToRemove = layout.itemAt(i)
                self.clear_layout(layoutToRemove)
                layoutToRemove.deleteLater()

    def clear_layout(self, layout):
        """
        Clear the memory of layout.

        Arguments:
            layout {Object} -- the layout object
        """
        logging.info("--> Clear layout: " + str(layout))
        if (self.check_attr_exist("current_device_type")
                and self.check_attr_exist("ctrl")):
            if (self.current_device_type == "Robot Vaccum Cleaner(0x0074)"):
                logging.info("Robot vaccum destroy timer")
                self.ctrl.destroy_timer_cleaning()
                self.ctrl.destroy_timer_mapping()
            elif (self.current_device_type == "Window Covering(0x0202)"):
                logging.info("Window Covering destroy timer")
                self.ctrl.destroy_timer_window_covering()
            elif (self.current_device_type == "Dishwasher(0x0075)"):
                logging.info("Dishwasher destroy timer")
                self.ctrl.destroy_timer_dishwasher()
            elif (self.current_device_type == "Laundry Washer(0x0073)"):
                logging.info("Laundry Washer destroy timer")
                self.ctrl.destroy_timer_laundry()
        self.is_rpc_timer_running = False
        # clear layouts and widgets
        self.clear_widgets(layout)

    def update_status(
            self,
            status_line1,
            status_color1,
            status_line2,
            status_color2):
        """
        Update statue on UI emulator.

        Arguments:
            status_line1 {str} -- the line1 object
            status_color1 {str} -- the color1 object
            status_line2 {str} -- the line2 object
            status_color2 {str} -- the color2 object
        """
        self.ui.lbl_status_1.setText(status_line1)
        self.ui.lbl_status_1.setStyleSheet("color: " + status_color1 + ";")
        self.ui.lbl_status_2.setText(status_line2)
        self.ui.lbl_status_2.setStyleSheet("color: " + status_color2 + ";")

    def generate_targetId(self):
        """
        Generate target id of a device.
        """
        vendorID = int(self.ui.txt_vendorid.text())
        productID = int(self.ui.txt_productid.text())
        serialNumber = int(self.ui.txt_serial_number.text())

        VID_PID_Str = (hex(vendorID)[2:]) + (hex(productID)[2:])
        serialNumberStr = hex(serialNumber)[2:]
        targetId = VID_PID_Str + '-' + serialNumberStr
        return targetId

    def get_list_device_from_file(self):
        """
        Return a list device which is save from a file.
        """
        listDevices = []
        try:
            file = open(DEVICE_LIST_PATH, "r")
            listDevices = file.read().split(':')
            file.close()
            return listDevices
        except OSError as err:
            logging.error(
                "Fail to open file to get device list: {}".format(err))
            return listDevices

    def remove_targetId(self):
        """
        Remove a device which has a targetid from list devices.
        """
        listDevices = self.get_list_device_from_file()
        if self.targetId in listDevices:
            listDevices.remove(self.targetId)
            deviceList = ":".join(listDevices)
            try:
                fileListDevice = open(DEVICE_LIST_PATH, "w+")
                fileListDevice.write(deviceList)
                fileListDevice.close()
            except OSError as err:
                logging.error(
                    "Fail to write device list to file: {}".format(err))

    def check_recover_device(self):
        """
        Check recover device.
        """
        targerId = self.targetId
        if str(targerId) in self.handle_recover_devices.get_targetid_device_recover():
            self.check_recover = True
        else:
            self.check_recover = False
        logging.info(f"check recover device: {self.check_recover}")

    def check_duplicate_device(self):
        """
        Check duplicate device.

        Return:
            True: if the device has targetid is existed in list devices
            False: if the device has targetid is not existed in list devices
        """
        listDevices = self.get_list_device_from_file()
        self.targetId = self.generate_targetId()
        if len(listDevices) == 0:
            return True
        elif (len(listDevices) >= 1) and (listDevices[0] == ''):
            return True
        if self.targetId in listDevices:
            return False
        else:
            return True

    def permit_edit_text(self, isEnable):
        """
        Change editable property of text.

        Arguments:
            isEnable {boolean} -- the boolean value
        """
        self.ui.txt_serial_number.setEnabled(isEnable)
        self.ui.txt_vendorid.setEnabled(isEnable)
        self.ui.txt_productid.setEnabled(isEnable)
        self.ui.txt_discriminator.setEnabled(isEnable)
        self.ui.txt_pincode.setEnabled(isEnable)
        self.ui.cbb_device_selection.setEnabled(isEnable)

    def load_network_configFromFile(self):
        """
        Load network configuration from config file.
        Return network information in dictionary.
        """
        fullpath = NETWORK_INFO_PATH + NETWORK_INFO_FILENAME
        try:
            with open(fullpath, 'r') as file:
                ip_data = json.load(file)
        except Exception as e:
            logging.error(str(e))
            ip_data = "[]"
        return ip_data

    def get_IPaddresses(self, ip_dict):
        """
        Return Ip address (ipv4, ipv6).

        Arguments:
            ip_dict {dict} -- the network configuration dict
        """
        ip_ver4 = ""
        ip_ver6 = ""

        if (ip_dict == "[]"):
            logging.info("So skip recover routine!")
            # logging.info(f'{NETWORK_INFO_PATH + NETWORK_INFO_FILENAME} does not exist.')
            return ip_ver4, ip_ver6

        # Get addr_info
        error_value = 0
        for key, value in ip_dict.items():
            if (key == "addr_info"):
                addr_info_list = value

        for item in addr_info_list:
            if (item.get("family") == IP_VERSION4 and
                item.get("prefixlen") == IP_VERSION4_PREFIXLEN and
                item.get("scope") == IP_VERSION4_SCOPE and
                item.get("label") == NETWORK_IF_NAME and
                    item.get("secondary") != True):
                ip_ver4 = item['local']
                logging.info(f"ip_ver4: {ip_ver4}")
                break

        for item in addr_info_list:
            if (item.get("family") == IP_VERSION6 and
                item.get("prefixlen") == IP_VERSION6_PREFIXLEN and
                item.get("scope") == IP_VERSION6_SCOPE and
                    item.get("temporary") != True):
                ip_ver6 = item['local']
                logging.info(f"ip_ver6: {ip_ver6}")
                break

        return ip_ver4, ip_ver6

    def execute_cmd(self, cmd):
        """
        Return the results after executing a string command.

        Arguments:
            cmd {str} -- the command string
        """
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        out, err = proc.communicate()
        out_utf8 = out.decode('utf-8').strip()
        err_utf8 = err.decode('utf-8').strip()

        if err_utf8 != "":
            logging.info("[ERR_UTF8] : " + err_utf8)
        if out_utf8 != "":
            pass

        return out_utf8, err_utf8

    def load_network_config(self):
        """
        Return Ip address (ipv4, ipv6) from network config.
        """
        logging.info(
            f"---------------- start load_network_config() -----------Network Interface: {NETWORK_IF_NAME}")
        ip_json = self.load_network_configFromFile()

        inet, inet6 = self.get_IPaddresses(ip_json)

        if inet != "" and inet6 != "":
            ipv4_format = inet + "/" + str(IP_VERSION4_PREFIXLEN)
            ipv6_format = inet6 + "/" + str(IP_VERSION6_PREFIXLEN)

            ip_show_cmd = f"ip addr show {NETWORK_IF_NAME}"
            out_utf8, err_utf8 = self.execute_cmd(ip_show_cmd)

            if err_utf8 != "":
                logging.error(err_utf8)
                # sys.exit(1)
            if out_utf8 != "":
                if (out_utf8.find(ipv6_format)) == -1:
                    ipv6_add_cmd = "sudo ip -6 addr add " + ipv6_format + " dev " + NETWORK_IF_NAME
                    self.execute_cmd(ipv6_add_cmd)
                    time.sleep(1)
                elif (out_utf8.find(ipv4_format)) == -1:
                    ipv4_add_cmd = "sudo ip addr add " + ipv4_format + " dev " + NETWORK_IF_NAME
                    self.execute_cmd(ipv4_add_cmd)
                    time.sleep(1)
                else:
                    logging.info(
                        "The primary IP ver4 and ver6 addresses exist. ")
        else:
            logging.info("Skip recover routine.")
        return inet, inet6

    def on_click_start_device(self):
        """
        Handle when press start device button.
        """
        is_parameters_valid = self.check_parameter_constraints()
        if is_parameters_valid:

            if self.ui.btn_start_device.text() == "Start Device":
                self.isDeviceStarted = False
                if (not HandleRecoverDevices.get_is_click_from_callback() and (
                        self.generate_targetId() in self.handle_recover_devices.get_targetid_device_recover())):
                    HandleRecoverDevices.get_recover_device_when_add_tab(
                        self.generate_targetId(), self)

                if ((len(list_status_device) < 1) or (
                        HandleRecoverDevices.get_is_click_from_callback())):
                    list_status_device.append(1)

                    self.create_date()
                    timer = time.localtime()
                    self.time_start = time.strftime("%H-%M-%S", timer)

                    can_start_device = self.check_duplicate_device()
                    self.check_recover_device()
                    self.notify_device_started()
                    # Update SN config file
                    self.update_payload_file(
                        SOURCE_PATH +
                        self.read_config()['qrtool_subpath'] +
                        "payload.txt",
                        self.ui.txt_vendorid.text(),
                        self.ui.txt_productid.text(),
                        self.ui.txt_pincode.text(),
                        self.ui.txt_discriminator.text())
                    self.create_qrcode()

                    if (not os.path.exists(SOURCE_PATH + TEMP_PATH + self.targetId)):
                        # create temp folder to storage device info
                        self.handle_recover_devices.create_storage_folder(
                            SOURCE_PATH, self.targetId)
                        # create current time
                        self.create_time = int(time.time())
                        self.ipv4 = ""
                        self.ipv6 = ""
                        self.is_recover = ""
                        self.interface_index = ""
                        self.unique_id = ""
                        self.rpcPort = self.rpc_port_default
                        # update factory config file
                        self.update_factory_config_file()

                    # Generate DAC
                    gen_dac_tool = GenDacTool(self.targetId)
                    is_gen_dac_done = gen_dac_tool.gen_dac_cert()
                    if can_start_device:
                        if is_gen_dac_done:
                            self.permit_edit_text(False)
                            self.start_device()
                        else:
                            self.wkr.connect_status.emit(STT_DAC_GENERATE_FAIL)
                    else:
                        self.wkr.connect_status.emit(STT_DEVICE_DUPLICATE)
                else:
                    self.wkr.connect_status.emit(STT_WAITING_RUNING_DEVICE)

            elif self.ui.btn_start_device.text() == "Stop Device":
                self.stop_device()
        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Matter IoT Emulator")
            msgBox.setText("Some input parameters are invalid.")
            msgBox.setInformativeText("Please input them in valid range")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

    def start_device(self):
        """
        Handle start device.
        """
        logging.debug("Start thread")
        self.ui.btn_start_device.setText("Stop Device")
        self.ui.btn_start_device.setIcon(
            QIcon(RESOURCE_PATH + "/icons/stop_icon.png"))
        self.name_device = self.ui.cbb_device_selection.currentText()
        self.load_network_config()
        # Start generating ip
        self.wkr.start()

    def stop_device(self):
        """
        Handle stop device.
        """
        self.isDeviceStarted = False
        # remove temp folder
        if ((not self.connected_device) and (not self.is_recover)):
            self.handle_recover_devices.remove_storage_folder(self.targetId)
        self.destroy_timer_qr()
        if (self.generateIp_done or self.isIPBindFail):
            if (len(list_status_device) > 0):
                list_status_device.remove(1)
            self.notify_device_stopped()
            self.permit_edit_text(True)
            self.ip_value.removeIpAfterStopDevice()
            self.ip_value.releaseRpcPort(self.rpcPort)
            self.remove_targetId()
            self.stop_thread()
            if self.connected_device:
                self.remove_info_list(
                    self.ui.cbb_device_selection.currentText())
                self.connected_device = False
            if self.isIPBindFail:
                self.isIPBindFail = False

    def start_device_running_thread(self):
        """
        Starting device_running thread.
        """
        device_thread = Thread(target=self.device_running)
        device_thread.daemon = True
        device_thread.start()

    def handle_device_not_supported(self):
        """
        Handle device is not supported.
        """
        logging.debug("Stop thread")
        self.ui.btn_start_device.setText("Start Device")
        self.ui.btn_start_device.setIcon(
            QIcon(RESOURCE_PATH + "/icons/start_icon.png"))
        self.wkr.connect_status.emit(STT_DEVICE_UNSUPPORTED)
        self.ui.lbl_qr_image.hide()
        self.ui.lbl_qr_code.hide()
        self.clear_layout(self.ui.lo_controller)

    def stop_thread(self):
        """
        Handle stop thread.

        Raises:
            Exception: if can not stop thread
        """
        logging.debug("Stop thread")
        self.ui.btn_start_device.setText("Start Device")
        self.ui.btn_start_device.setIcon(
            QIcon(RESOURCE_PATH + "/icons/start_icon.png"))
        try:
            if self._runner is not None:
                self._runner.stop()
                self._runner = None

            if (hasattr(self, "ctrl") and hasattr(self.ctrl, "stop")):
                self.ctrl.stop()

        except PermissionError:
            logging.error('Command is already done')
        self.wkr.connect_status.emit(STT_DISCONNECTED)
        self.ui.lbl_qr_image.hide()
        self.ui.lbl_qr_code.hide()
        self.clear_layout(self.ui.lo_controller)
        self.ctrl = None

    def get_runner_script(self):
        """
        Return script which run application.
        """
        if "Windows" in platform.platform():
            return "run.bat"
        elif "Linux" in platform.platform():
            return "/bin/sh run.sh"
        else:
            logging.warning(
                "Please define runner script for {}".format(
                    platform.platform()))
            return None

    def destroy_timer_qr(self):
        """
        Destroy timer generation QR code
        """
        dic_data = self.__dict__
        if ("timeqr" in dic_data):
            logging.info("destroy timer qr")
            self.timeqr.cancel()

    def update_factory_config_file(self):
        """
        Update factory information to config file.
        """
        config_file = SOURCE_PATH + TEMP_PATH + \
            "{}/{}".format(self.targetId, CHIP_FACTORY_FILE)
        DeviceRunner("cd").update_SN_config_file(
            config_file,
            self.ui.txt_serial_number.text(),
            self.ui.txt_productid.text(),
            self.ui.txt_discriminator.text(),
            self.ui.txt_pincode.text(),
            self.ui.cbb_device_selection.currentText(),
            self.create_time,
            self.ipv4,
            self.ipv6,
            self.rpcPort,
            self.interface_index,
            self.is_recover,
            self.ui.txt_vendorid.text(),
            self.unique_id)

    def re_gennerate_qr(self):
        """
        Re generate QR code.
        """
        if (not self.isDeviceStarted):
            self.isDeviceStarted = True
            self.wkr.connect_status.emit(STT_DEVICE_STARTED)
            self.wkr.onboarding_code.emit(self.qrcode, self.manual_code)

    def create_rpc_port(self, rpc_port):
        """
        Return Rpc port number.

        Arguments:
            rpc_port {int} -- a start port number
        """
        if (rpc_port not in HandleRecoverDevices.list_recover_rpc_port):
            return rpc_port
        else:
            rpc_port = rpc_port + 1
            return self.create_rpc_port(rpc_port)

    def device_running(self):
        """
        Handle device running.
        """
        # TODO : Run virtual device
        self.connected_device = False
        if ((len(self.ipv4) == 0) or (len(self.ipv6) == 0)):
            self.remove_targetId()
            self.notify_device_stopped()
            self.permit_edit_text(True)
            time.sleep(3)
            self.wkr.connect_status.emit(STT_IP_GENERATE_FAIL)
            return

        # update factory config file
        if (not HandleRecoverDevices.get_is_click_from_callback()):
            self.update_factory_config_file()

        # create rpc port if rpc port value is default
        if (self.rpcPort == self.rpc_port_default):
            rpc_port = self.rpc_port_default + 1
            self.rpcPort = self.create_rpc_port(rpc_port)

        self.wkr.connect_status.emit(STT_IP_GENERATED)
        time.sleep(1)
        self.wkr.connect_status.emit(STT_DAC_GENERATE_STARTING)
        time.sleep(1)
        self.wkr.connect_status.emit(STT_DAC_GENERATED)
        time.sleep(1)
        self.wkr.connect_status.emit(STT_DEVICE_STARTING)
        cmd = self.get_running_app_command()
        if cmd is not None:
            self._runner = DeviceRunner(cmd)
            self._runner.execute()
            self.load_network_config()

            for line in self._runner.get_log():
                try:
                    patter = "(?:\\[\\d+\\.\\d+\\])(?:\\[\\d+:\\d+\\]){0,1}\\s*(.+)"
                    if TEST_MODE:
                        current_time = datetime.datetime.now()
                        value = re.findall(patter, line)
                        if value != []:
                            self.save_log("[{}]".format(
                                current_time) + str(value[-1]))
                except Exception as ex:
                    logging.warning("Get_log bug--> " + repr(ex))
                    pass

                if FLAG_BLUETOOTH_FAIL in line:
                    self.wkr.connect_status.emit(
                        STT_COMMISSIONING_FAIL_BLUETOOTH)
                else:
                    if FLAG_BIND_IP_FAIL in line:
                        self.isIPBindFail = True
                        self.wkr.connect_status.emit(STT_BIND_IP_FAIL_BACKEND)

                    elif ((FLAG_DEVICE_STARTED in line) and (not self.isDeviceStarted)):
                        self.isDeviceStarted = True
                        if self.check_recover:
                            # If recovering, do not gen qr code
                            if (len(list_status_device) > 0):
                                list_status_device.remove(1)
                            time.sleep(3)
                            self.wkr.connect_status.emit(STT_CONNECTED)
                            self.save_deviceConnect(
                                self.ui.cbb_device_selection.currentText())
                            self.connected_device = True
                            if (HandleRecoverDevices.get_is_click_from_callback()):
                                HandleRecoverDevices.set_is_click_from_callback(
                                    False)
                                self.notify_recover_done()
                        else:
                            self.wkr.connect_status.emit(STT_DEVICE_STARTED)
                            self.wkr.onboarding_code.emit(
                                self.qrcode, self.manual_code)

                    elif FLAG_CONNECTING in line:
                        self.wkr.connect_status.emit(STT_CONNECTING)
                    # TODO : Waiting pairing status of virtual device
                    elif (FLAG_CONNECTED in line) and (not self.connected_device):
                        self.wkr.connect_status.emit(STT_CONNECTED)
                        self.save_deviceConnect(
                            self.ui.cbb_device_selection.currentText())
                        HandleRecoverDevices.add_recover_devices(self.targetId)
                        self.connected_device = True
                        # update factory config file
                        self.is_recover = 1
                        config_file = SOURCE_PATH + TEMP_PATH + \
                            "{}/{}".format(self.targetId, CHIP_FACTORY_FILE)
                        factory_dict = HandleRecoverDevices.read_config_file(
                            config_file, self.targetId)
                        self.unique_id = factory_dict.get('unique-id')
                        self.update_factory_config_file()

                        # store ip for all tab
                        if (self.ipv4 not in HandleRecoverDevices.list_recover_ipv4):
                            HandleRecoverDevices.list_recover_ipv4.append(
                                self.ipv4)
                        if (self.ipv6 not in HandleRecoverDevices.list_recover_ipv6):
                            HandleRecoverDevices.list_recover_ipv6.append(
                                self.ipv6)

                        # store interface index
                        if (self.interface_index not in HandleRecoverDevices.list_recover_interface_index):
                            HandleRecoverDevices.list_recover_interface_index.append(
                                self.interface_index)

                        # store rpc port
                        if (self.rpcPort not in HandleRecoverDevices.list_recover_rpc_port):
                            HandleRecoverDevices.list_recover_rpc_port.append(
                                self.rpcPort)

                    elif FLAG_COMMISSIONING_FAIL in line:
                        self.wkr.connect_status.emit(STT_COMMISSIONING_FAIL)
        else:
            self.handle_device_not_supported()

    def save_log(self, line):
        """
        Handle save log to file.

        Arguments:
            line {str} -- the text need to write to file
        """
        self.path_log = "/log/{}/{}--{}--{}".format(str(self.today),
                                                    self.time_start,
                                                    self.get_idDevice(self.ui.cbb_device_selection.currentText()),
                                                    self.targetId)
        file_path = SOURCE_PATH + self.path_log
        with open(file_path, 'a', encoding='utf8') as file:
            file.write(line + "\n")
            file.close()

    def get_running_app_command(self):
        """
        Return appliucation command running.

        Raises:
            Exception: if can not get running app command
        """
        try:
            self.name_device = self.ui.cbb_device_selection.currentText()
            sub_path = SOURCE_PATH + \
                self.get_device_info(self.name_device)['sub_path']
            cmd = sub_path + " --wifi --discriminator " + self.ui.txt_discriminator.text() \
                + " --passcode " + self.ui.txt_pincode.text() + " --vendor-id " \
                + self.ui.txt_vendorid.text() \
                  + " --product-id " + self.ui.txt_productid.text() + " --capabilities 6" \
                  + " --KVS {}{}{}/chip_kvs_".format(SOURCE_PATH, TEMP_PATH, self.targetId) + self.targetId \
                  + " --RPC-server-port " + str(self.rpcPort) \
                  + " --IPv4-Addr " + self.ipv4 \
                  + " --IPv6-Addr " + self.ipv6
            logging.info(cmd)
            return cmd
        except BaseException:
            logging.warning("Can't get running app command")
            return None

    def update_payload_file(
            self,
            file_path,
            vendor_id,
            product_id,
            setup_code,
            discriminator):
        """
        Update payload file.

        Raises:
            Exception: if can not open file for updating
        """
        try:
            with open(file_path, 'w+') as file:
                line_1 = "version 0\n"
                line_2 = "vendorID {}\n".format(vendor_id)
                line_3 = "productID {}\n".format(product_id)
                line_4 = "commissioningFlow 0\n"
                line_5 = "rendezVousInformation 6\n"
                line_6 = "setUpPINCode {}\n".format(setup_code)
                line_7 = "discriminator {}".format(discriminator)
                file.writelines(
                    [line_1, line_2, line_3, line_4, line_5, line_6, line_7])
                file.close()
        except Exception as e:
            logging.error("Failed to update payload file: " + str(e))

    def create_qrcode(self):
        """
        Handle creating a qrcode.
        """
        self.qrcode = self.payloads.generate_qrcode(
            int(
                self.ui.txt_pincode.text()), discriminator=int(
                self.ui.txt_discriminator.text()), vid=int(
                self.ui.txt_vendorid.text()), pid=int(
                    self.ui.txt_productid.text()))
        self.manual_code = self.payloads.generate_manualcode(
            int(
                self.ui.txt_pincode.text()), discriminator=int(
                self.ui.txt_discriminator.text()), vid=int(
                self.ui.txt_vendorid.text()), pid=int(
                    self.ui.txt_productid.text()))
        logging.info("QR code: {}{}".format(self.qrcode, self.manual_code))

    def gen_qrcode(self, onboarding_payload, manual_pairing_code):
        """
        Handle generating a qrcode.
        """
        if (self.ui.btn_start_device.text() == "Start Device") and (onboarding_payload == "") and (manual_pairing_code == ""):
            self.destroy_timer_qr()
            return
        pix = QPixmap(self.generate_qr_image(onboarding_payload))
        ratio = 1
        pix.setDevicePixelRatio(ratio)
        self.ui.lbl_qr_image.show()
        self.ui.lbl_qr_code.show()
        self.ui.lbl_qr_image.setPixmap(pix)
        self.ui.lbl_qr_code.setText(
            f"\nQR Code: {str(onboarding_payload)}\n \nManual Code: {str(manual_pairing_code)}")
        self.destroy_timer_qr()

    def generate_qr_image(self, qr_payload):
        """
        Handle generating a qr image.

        Raises:
            Exception: if can not generate qr image from payload
        """
        try:
            # instance QR code
            qr_instance = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )

            # QR code add data
            qr_instance.add_data(self.qrcode)
            qr_instance.make(fit=True)

            # Convert the QR code to an png image
            qr_img = qr_instance.make_image(fill="black", back_color="white")

            # Save qr code image to path
            img_path = SOURCE_PATH + "/setup_payload/qrcode.png"
            qr_img.save(img_path)
            logging.info("Generate QR code image success")
            return img_path
        except Exception as ex:
            logging.warning("Can't generate qr image from payload: " + str(ex))
            return None

    def get_app_version(self):
        """
        Return application version.

        Raises:
            Exception: if can not read version
        """
        try:
            return self.read_config()['version']
        except BaseException:
            logging.warning("Can't read version")
            return None

    def get_limit_devices_number(self):
        """
        Return limit device number.

        Raises:
            Exception: if can not get limit device number
        """
        try:
            return self.read_config()['max_number_of_device']
        except BaseException:
            logging.warning("Can't read max number of devices")
            return 15

    def get_parameter_constraints(self):
        """
        Return parameter constraints.

        Raises:
            Exception: if can not get parameter constraints
        """
        try:
            return self.read_config()['parameter_constraints']
        except BaseException:
            logging.warning("Can't get parameter constraints from config file")
            return None

    def get_device_types(self):
        """
        Return device type.

        Raises:
            Exception: if can not get device type
        """
        try:
            return self.read_config()['device_list']
        except BaseException:
            logging.warning("Can't read device list")
            return []

    def get_serial_number_list(self):
        """
        Return list serial number.

        Raises:
            Exception: if can not get list serial number
        """
        try:
            return self.read_config()['serial_number_list']
        except BaseException:
            logging.warning("Can't read serial number list")
            return []

    def read_config(self):
        """
        Return config information from file.

        Raises:
            Exception: if can not open config file
        """
        f = open(CONFIG_FILE_PATH)
        configs = json.load(f)
        f.close()
        return configs

    def config_logging(self, logging_mode=TEST_MODE):
        """
        Config logging information.

        Arguments:
            logging_mode {str} -- the logging mode (default = DEBUG_MODE)
        """
        if logging_mode:
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] [%(threadName)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] %(levelname)s - %(message)s"
            )

    def get_device_info(self, name_device):
        """
        Return device information.

        Arguments:
            name_device {str} -- the device name
        Raises:
            Exception: if can not read device info
        """
        try:
            logging.info("Device name: {}".format(name_device))
            value = name_device.split("(")[1][:-1]
            device_info = self.read_config()['device_types']
            result = ""
            for i in device_info:
                if i.get('device_id') == value:
                    result = i
            return result
        except Exception as e:
            logging.warning("Can't read device Info: " + str(e))
            return None

    def update_label_constraints(self):
        """
        Update label content on UI.
        """
        parameter_constraints = self.get_parameter_constraints()

        # Update Serial Number Constraints
        self.ui.lb_serial_number_constraint.setText("(" +
                                                    str(parameter_constraints["serial_number"]["range"][0]) +
                                                    "-" +
                                                    str(parameter_constraints["serial_number"]["range"][1]) +
                                                    ")")
        # Update Vendor ID Constraints
        self.ui.lb_vendor.setText(
            "(" + str(parameter_constraints["vendor_id"]["default_value"]) + ")")
        # Update Product ID Constraints
        self.ui.lb_product.setText("(" +
                                   str(parameter_constraints["product_id"]["range"][0]) +
                                   "-" +
                                   str(parameter_constraints["product_id"]["range"][1]) +
                                   ")")
        # Update Discriminator Constraints
        self.ui.lb_dicriminator.setText("(" +
                                        str(parameter_constraints["discriminator"]["range"][0]) +
                                        "-" +
                                        str(parameter_constraints["discriminator"]["range"][1]) +
                                        ")")
        # Update Pincode Constraints
        self.ui.lb_pincode.setText("(" +
                                   str(parameter_constraints["pin_code"]["range"][0]) +
                                   "-" +
                                   str(parameter_constraints["pin_code"]["range"][1]) +
                                   ")")

    def check_parameter_constraints(self):
        """
        Check parameter constraints.

        Return:
            True: if parameters are satify the constaints
            False: if parameters are not satify the constaints
        """
        try:
            is_input_parameters_valid = True
            parameter_constraints = self.get_parameter_constraints()
            # Check Serial Number
            self.serial_number_default_value = str(
                parameter_constraints["serial_number"]["default_value"])
            if int(
                    self.ui.txt_serial_number.text()) not in range(
                    parameter_constraints["serial_number"]["range"][0],
                    parameter_constraints["serial_number"]["range"][1] + 1):
                self.update_parameter_status(RED, None, None, None, None)
                self.update_status(
                    "Serial Number is invalid.",
                    RED,
                    "Please input Serial Number in valid range",
                    BLACK)
                is_input_parameters_valid = False
            else:
                self.update_parameter_status(BLACK, None, None, None, None)

            # Check Vendor ID
            self.vendor_id_default_value = str(
                parameter_constraints["vendor_id"]["default_value"])
            if self.ui.txt_vendorid.text() != self.vendor_id_default_value:
                self.update_parameter_status(None, RED, None, None, None)
                self.update_status(
                    "Vendor ID is invalid.",
                    RED,
                    "Please input Vendor ID in valid range",
                    BLACK)
                is_input_parameters_valid = False
            else:
                self.update_parameter_status(None, BLACK, None, None, None)

            # Check Product ID
            self.product_id_default_value = str(
                parameter_constraints["product_id"]["default_value"])
            if int(
                    self.ui.txt_productid.text()) not in range(
                    parameter_constraints["product_id"]["range"][0],
                    parameter_constraints["product_id"]["range"][1] + 1):
                self.update_parameter_status(None, None, RED, None, None)
                self.update_status(
                    "Product ID is invalid.",
                    RED,
                    "Please input Product ID in valid range",
                    BLACK)
                is_input_parameters_valid = False
            else:
                self.update_parameter_status(None, None, BLACK, None, None)
            # Check Discriminator
            self.discriminator_default_value = str(
                parameter_constraints["discriminator"]["default_value"])
            if int(
                    self.ui.txt_discriminator.text()) not in range(
                    parameter_constraints["discriminator"]["range"][0],
                    parameter_constraints["discriminator"]["range"][1] + 1):
                self.update_parameter_status(None, None, None, RED, None)
                self.update_status(
                    "Discriminator is invalid.",
                    RED,
                    "Please input Discriminator in valid range",
                    BLACK)
                is_input_parameters_valid = False
            else:
                self.update_parameter_status(None, None, None, BLACK, None)
            # Check Pincode
            self.pincode_default_value = str(
                parameter_constraints["pin_code"]["default_value"])
            if int(
                    self.ui.txt_pincode.text()) not in range(
                    parameter_constraints["pin_code"]["range"][0],
                    parameter_constraints["pin_code"]["range"][1] + 1):
                self.update_parameter_status(None, None, None, None, RED)
                self.update_status(
                    "Pin code is invalid.",
                    RED,
                    "Please input Pin Code in valid range",
                    BLACK)
                is_input_parameters_valid = False
            elif int(self.ui.txt_pincode.text()) in INVALID_PASSCODES:
                self.update_parameter_status(None, None, None, None, RED)
                self.update_status(
                    "Pin code is insecure and unusable.",
                    RED,
                    "Please change Pin Code in valid range",
                    BLACK)
                is_input_parameters_valid = False
            else:
                self.update_parameter_status(None, None, None, None, BLACK)
            if is_input_parameters_valid:
                if (self.ui.btn_start_device.text() == "Start Device"):
                    self.update_status(
                        "Not connected.",
                        RED,
                        "Please select device type for commissioning.",
                        BLACK)
            return is_input_parameters_valid
        except Exception as e:
            logging.debug("Fail in checking parameter constraints: " + str(e))
            return False

    def update_parameter_status(
            self,
            serial_number_color,
            vendor_id_color,
            product_id_color,
            discriminator_color,
            pincode_color):
        """
        Update color for labels on UI.

        Arguments:
            serial_number_color {str} -- the color of serial number label
            vendor_id_color {str} -- the color of vendor id label
            product_id_color {str} -- the color of product id label
            discriminator_color {str} -- the color of discriminator label
            pincode_color {str} -- the color of pin code label
        """
        if serial_number_color is not None:
            self.ui.txt_serial_number.setStyleSheet(
                "color: " + serial_number_color + ";")
        if vendor_id_color is not None:
            self.ui.txt_vendorid.setStyleSheet(
                "color: " + vendor_id_color + ";")
        if product_id_color is not None:
            self.ui.txt_productid.setStyleSheet(
                "color: " + product_id_color + ";")
        if discriminator_color is not None:
            self.ui.txt_discriminator.setStyleSheet(
                "color: " + discriminator_color + ";")
        if pincode_color is not None:
            self.ui.txt_pincode.setStyleSheet("color: " + pincode_color + ";")

    def save_config(
            self,
            name_device,
            vendor,
            product,
            discriminator,
            pincode):
        """
        Update color for labels on UI.

        Arguments:
            name_device {str} -- the device name string
            vendor {str} -- the vendor string
            product {str} -- the product string
            discriminator {str} -- the discriminator string
            pincode {str} -- the pin code string
        Raises:
            Exception: if can not open file
        """
        try:
            patter = '[\\dx]+'
            value = re.findall(patter, name_device)[-1]
            with open(CONFIG_FILE, 'r+') as f:
                data = json.load(f)
                for device_type in data.get('device_types'):
                    if device_type.get('device_id') == value:
                        config_info = device_type['config_info']
                        config_info['vendor_id'] = vendor
                        config_info['product_id'] = product
                        config_info['discriminator'] = discriminator
                        config_info['pin_code'] = pincode
                        f.seek(0)
                        break
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            logging.error("Failed to update payload file: " + str(e))

    def handle_delete_device(self):
        """
        Update color for labels on UI.

        Arguments:
            name_device {str} -- the device name string
            vendor {str} -- the vendor string
            product {str} -- the product string
            discriminator {str} -- the discriminator string
            pincode {str} -- the pin code string
        Raises:
            Exception: if can not open file
        """
        self.connected_device = False
        self.is_recover = False
        # Remove storage folder
        self.handle_recover_devices.remove_storage_folder(self.targetId)
        # remove store ip
        if (self.ipv4 in HandleRecoverDevices.list_recover_ipv4):
            HandleRecoverDevices.list_recover_ipv4.remove(self.ipv4)
        if (self.ipv6 in HandleRecoverDevices.list_recover_ipv6):
            HandleRecoverDevices.list_recover_ipv6.remove(self.ipv6)
        # remove store interface index
        if (self.interface_index in HandleRecoverDevices.list_recover_interface_index):
            HandleRecoverDevices.list_recover_interface_index.remove(
                self.interface_index)
        # remove store rpc port
        if (self.rpcPort in HandleRecoverDevices.list_recover_rpc_port):
            HandleRecoverDevices.list_recover_rpc_port.remove(self.rpcPort)
        # stop device
        self.stop_device()
        # update device status
        self.update_status(
            f"Device was deleted by commissioner!",
            RED,
            "Please start device to commissioning again",
            BLACK)

    def convert_string_dec_to_hex(self, dec_value):
        """
        Convert a string from decimal to hex.

        Arguments:
            dec_value {str} -- the decimal string value
        Return:
            hex string
        """
        hex_str = hex(int(dec_value))[2:]
        return "0x" + hex_str

    def update_device_state(self, device_state_info):
        """
        Update device state.

        Arguments:
            device_state_info {str} -- the device state information
        """
        device_state = ""
        try:
            fabric_info_len = len(device_state_info["reply"]["fabricInfo"])
            if fabric_info_len > 0:
                fabric_id = self.convert_string_dec_to_hex(
                    device_state_info["reply"]["fabricInfo"][0]["fabricId"])
                node_id = self.convert_string_dec_to_hex(
                    device_state_info["reply"]["fabricInfo"][0]["nodeId"])
                device_state = "Status: " + device_state_info["status"] + ", FabricID: " + \
                    fabric_id + ", NodeID: " + node_id
            else:
                if (self.connected_device):
                    self.handle_delete_device()

        except Exception as e:
            logging.error(str(device_state_info) + "\n" + str(e))
        if (self.isDeviceStarted):
            self.update_status(
                f"Device is connected succesfully! {self.interfaceName}-{self.ipv4}/{str(self.rpcPort)}",
                "green",
                device_state,
                "black")

    def generate_dac(self, path):
        """
        Generate DAC.

        Arguments:
            path {str} -- the device state information
        Return:
            True -- if DAC files were successfully created
            False -- if DAC files were not created
        """
        return DeviceRunner("generate dac").generate_dac(path)


class Main(QMainWindow):
    """
    Main class definition for creating emulator
    """

    def __init__(self):
        """
        Initialize a Main instance.
        """
        super().__init__()
        self.listTab = []
        self.listDevice = []
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setUsesScrollButtons(True)
        self.tabWidget.setStyleSheet("QTabBar::scroller  { width: 100px; }")
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.addButton = QPushButton("+", self)
        self.addButton.setGeometry(20, 10, 30, 30)
        self.addButton.clicked.connect(self.addNewTab)

        self.infoButton = QPushButton("I \n N \n F \n O", self)
        self.infoButton.setGeometry(20, 40, 30, 100)
        self.infoButton.clicked.connect(self.showOverlay)
        self.tab = MainWindow()

        self.overlay_widget = OverlayWidget(self)
        self.overlay_widget.hide()
        self.tab.update_label_constraints()
        self.tab.update_ui()
        self.update_ui_tab()
        self.number_tab = 0
        self.addNewTab()
        self.tabName = ""
        self.compact_folder_log(self.get_all_dir_log_need_remove())
        base_ipv4, base_ipv6 = self.get_network_config()
        self.releaseIP_when_start_app(base_ipv4, base_ipv6)

        self.tcpDump = None
        tcpDump_thread = Thread(target=self.tcpDumpFunc)
        tcpDump_thread.start()

        # handle recover tab info
        HandleRecoverDevices.remove_un_commissioned_storage_folder()
        
        HandleRecoverDevices.handle_recover_devices(
            self.addNewTab, self.listTab)
        self.is_recover_device = HandleRecoverDevices.check_recover()

    def tcpDumpFunc(self):
        """
        TCP dump network data on a interface.
        """
        cmd = f"sudo tcpdump -i {NETWORK_IF_NAME} -n udp port 5540"
        self.tcpDump = DeviceRunner(cmd)
        self.tcpDump.execute()

    def showOverlay(self):
        """
        Add a label on UI emulator.
        """
        if self.infoButton.text() == "I \n N \n F \n O":
            self.overlay_widget.show()
            self.update_lbwidget(len(list_device_connect), self.number_tab)
            self.list_device_connect = list_device_connect
            self.update_widget()

    def update_lbwidget(self, num_connect, num_tab):
        """
        Update content of label widget.

        Arguments:
            num_connect {str} -- the current connected devicess
            num_tab {str} -- the open tabs index
        """
        self.overlay_widget.label_tt.setText(
            "Current connected Devices / Open Tabs : {}/{}".format(num_connect, num_tab))

    def update_widget(self):
        """
        Update widget on UI.
        """
        self.overlay_widget.label_2.setText(
            "On/Off Light(0x0100) : {}".format(list_device_connect.count("0x0100")))
        self.overlay_widget.label.setText(
            "Dimmable Light(0x0101) : {}".format(
                list_device_connect.count("0x0101")))
        self.overlay_widget.label_3.setText(
            "Color Temperature Light(0x010C) : {}".format(
                list_device_connect.count("0x010C")))
        self.overlay_widget.label_4.setText(
            "Extended Color Light(0x010D) : {}".format(
                list_device_connect.count("0x010D")))
        self.overlay_widget.label_5.setText(
            "On/Off Plug-in Unit(0x010A) : {}".format(list_device_connect.count("0x010A")))
        self.overlay_widget.label_6.setText(
            "Dimmable Plug-in Unit(0x010B) : {}".format(list_device_connect.count("0x010B")))
        self.overlay_widget.label_7.setText(
            "Pump(0x0303) : {}".format(
                list_device_connect.count("0x0303")))
        self.overlay_widget.label_8.setText(
            "Contact Sensor(0x0015) : {}".format(
                list_device_connect.count("0x0015")))
        self.overlay_widget.label_9.setText(
            "Light Sensor(0x0106) : {}".format(
                list_device_connect.count("0x0106")))
        self.overlay_widget.label_10.setText(
            "Occupancy Sensor(0x0107) : {}".format(
                list_device_connect.count("0x0107")))
        self.overlay_widget.label_11.setText(
            "Temperature Sensor(0x0302) : {}".format(
                list_device_connect.count("0x0302")))
        self.overlay_widget.label_12.setText(
            "Pressure Sensor(0x0305) : {}".format(
                list_device_connect.count("0x0305")))
        self.overlay_widget.label_13.setText(
            "Flow Sensor(0x0306) : {}".format(
                list_device_connect.count("0x0306")))
        self.overlay_widget.label_14.setText(
            "Humidity Sensor(0x0307) : {}".format(
                list_device_connect.count("0x0307")))
        self.overlay_widget.label_15.setText(
            "Door Lock(0x000A) : {}".format(
                list_device_connect.count("0x000A")))
        self.overlay_widget.label_16.setText(
            "Window Covering(0x0202) : {}".format(
                list_device_connect.count("0x0202")))
        self.overlay_widget.label_17.setText(
            "HeatingCoolingUnit(0x0300) : {}".format(
                list_device_connect.count("0x0300")))
        self.overlay_widget.label_18.setText(
            "Thermostat(0x0301) : {}".format(
                list_device_connect.count("0x0301")))
        self.overlay_widget.label_19.setText(
            "Fan(0x002B) : {}".format(
                list_device_connect.count("0x002B")))

        self.overlay_widget.label_21.setText(
            "Air Purifier(0x002D) : {}".format(
                list_device_connect.count("0x002D")))
        self.overlay_widget.label_22.setText(
            "Air Quality Sensor(0x002C) : {}".format(
                list_device_connect.count("0x002C")))
        self.overlay_widget.label_23.setText(
            "Dishwasher(0x0075) : {}".format(
                list_device_connect.count("0x0075")))
        self.overlay_widget.label_24.setText(
            "Laundry Washer(0x0073) : {}".format(
                list_device_connect.count("0x0073")))
        self.overlay_widget.label_25.setText(
            "Room Air Conditioner(0x0072) : {}".format(
                list_device_connect.count("0x0072")))
        self.overlay_widget.label_26.setText(
            "Refrigerator(0x0070) : {}".format(
                list_device_connect.count("0x0070")))
        self.overlay_widget.label_27.setText(
            "Smoke&Carbon Alarm(0x0076) : {}".format(
                list_device_connect.count("0x0076")))
        self.overlay_widget.label_28.setText(
            "Robot Vaccum Cleaner(0x0074) : {}".format(
                list_device_connect.count("0x0074")))

    def get_all_dir_log_need_remove(self):
        """
        Get all of log directory need to be remove.

        Raise:
            Exception: if can not get path of log folder
        Return:
            Directory of log folder
        """
        self.pathLog = SOURCE_PATH + "/log/"
        try:
            list_dir = os.listdir(self.pathLog)
        except OSError as err:
            logging.error("Fail to get path of log folder: {}".format(err))
        dict_dir_time = {}
        for dir in list_dir:
            fullPath = self.pathLog + str(dir)
            if (not os.path.isdir(fullPath)):
                continue
            dict_dir_time[str(dir)] = int(
                self.get_create_folder_time(fullPath))
        dirs = self.sort_date_time_all_dir(dict_dir_time)
        return dirs

    def get_create_folder_time(self, path):
        """
        Return created time of a folder.

        Arguments:
            path {str} -- the path of a folder
        Raise:
            Exception: if can not get created time of a folder
        """
        try:
            create_time = os.path.getctime(path)
        except OSError as err:
            logging.error(
                "Fail to get create Time of log folder: {}".format(err))
        return create_time

    def compact_folder_log(self, list_dir):
        """
        Remove the path of a folder.

        Arguments:
            list_dir {str} -- the path of a folder
        Raise:
            Exception: if can not remove a folder
        """
        for dir in list_dir:
            try:
                shutil.rmtree(dir)
            except OSError as err:
                logging.error(
                    "Fail to remove folder {} {}log".format(
                        dir, err))

    def sort_date_time_all_dir(self, dict_dir_time):
        """
        Return a list of folder after sorted.

        Arguments:
            dict_dir_time {dict} -- the dictionary of path and datetime
        """
        list_dir_need_remove = []
        list_time_value = list(dict_dir_time.values())
        list_time_value.sort(reverse=True)
        if (len(list_time_value) > NUMBER_OF_FOLDER_LOG):
            list_time_value = list_time_value[2:]
            for val in list_time_value:
                key = self.get_key_dict(val, dict_dir_time)
                if ("None" not in key):
                    list_dir_need_remove.append(self.pathLog + str(key))
        return list_dir_need_remove

    def get_key_dict(self, val, dict):
        """
        Find a key with input value in a dictionary.

        Arguments:
            val {str} -- the valur need to be search
            dict {dict} -- the dictionary data
        """
        for key, value in dict.items():
            if val == value:
                return key
        return "None"

    def show_message_box(self):
        """
        Show message box.
        """
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Warning)
        self.msgBox.setWindowTitle("Matter IoT Emulator")
        self.msgBox.setText("The Matter Emulator is in recovering process...")
        self.msgBox.setInformativeText("Please wait a moment!")
        self.msgBox.setStandardButtons(QMessageBox.NoButton)
        self.msgBox.setFixedSize(400, 300)  # Set the fixed size
        self.msgBox.exec_()

    def close_message_box(self):
        """
        Close message box.
        """
        if self.msgBox is not None:
            self.msgBox.accept()
            self.msgBox = None

    def execute_command(self, cmd):
        """
        Return the output result after executing the command.

        Arguments:
            cmd {str} -- the command string
        """
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        out, err = proc.communicate()
        out_utf8 = out.decode('utf-8').strip()
        err_utf8 = err.decode('utf-8').strip()

        if err_utf8 != "":
            logging.info("[ERR_UTF8] : " + err_utf8)
        if out_utf8 != "":
            pass

        return out_utf8, err_utf8

    def store_network_config(self, data):
        """
        Write network cionfig information to file.

        Arguments:
            data {str} -- the data string need to write to file
        """
        fullpath = NETWORK_INFO_PATH + NETWORK_INFO_FILENAME

        if os.path.isfile(fullpath):
            logging.info(fullpath + " exist")
            os.remove(fullpath)

        try:
            with open(fullpath, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logging.error("Failed to write network info file: " + str(e))

    def convert_dataFormat(self, input_str):
        """
        Convert input string.

        Arguments:
            input_str {str} -- input data string need to be converted
        Return:
            A tuple of an error add network address informations
        """
        error_value = 0
        addr_info_list = []

        if (input_str == "[]" or input_str == ""):
            logging.info("Cannot get ip info. Connect to a Wi-Fi network.")
            error_value = 1
            # os._exit(0)
        else:
            # Remove bracket : []
            str_data = str(input_str)[1:-1]

            # convert str to json(python dict)
            dict_data = json.loads(str_data)

            # store data to file
            self.store_network_config(dict_data)

            # Get addr_info
            for key, value in dict_data.items():
                if ((key == "operstate") and (
                        value == "DOWN" or value == "DORMANT")):
                    error_value = 1
                    logging.info("operstate : {}".format(value))
                    break
                elif (key == "addr_info"):
                    addr_info_list = value

        return error_value, addr_info_list

    def get_IPaddress(self, info_list):
        """
        Return Ip address (ipv4, ipv6).

        Arguments:
            info_list {dict} -- the network configuration dictionary
        """
        ip_ver4 = ""
        ip_ver6 = ""

        for item in info_list:
            if (item.get("family") == IP_VERSION4 and
                item.get("prefixlen") == IP_VERSION4_PREFIXLEN and
                item.get("scope") == IP_VERSION4_SCOPE and
                item.get("label") == NETWORK_IF_NAME and
                    item.get("secondary") != True):
                ip_ver4 = item['local']
                logging.info(f"ip_ver4: {ip_ver4}")
                break

        for item in info_list:
            if (item.get("family") == IP_VERSION6 and
                item.get("prefixlen") == IP_VERSION6_PREFIXLEN and
                item.get("scope") == IP_VERSION6_SCOPE and
                    item.get("temporary") != True):
                ip_ver6 = item['local']
                logging.info(f"ip_ver6: {ip_ver6}")
                break

        return ip_ver4, ip_ver6

    def get_network_config(self):
        """
        Return Ip address (ipv4, ipv6).
        """
        ipver4 = ""
        ipver6 = ""

        get_network_info_cmd = f"ip -j addr show {NETWORK_IF_NAME}"
        network_info_utf8, network_info_err_utf8 = self.execute_command(
            get_network_info_cmd)

        error_value, addr_info_list = self.convert_dataFormat(
            network_info_utf8)

        if error_value:
            logging.info("Connect to a Wi-Fi network.")
            os._exit(0)
        else:
            ipver4, ipver6 = self.get_IPaddress(addr_info_list)

        if ipver4 == "" or ipver6 == "":
            logging.info("Cannot get IP ver4 or ver6 address")
            # os._exit(0)
        return ipver4, ipver6

    def releaseIP_when_start_app(self, base_ipv4, base_ipv6):
        """
        Relaese Ip address (ipv4, ipv6) when starting application.

        Arguments:
            base_ipv4 {str} -- the ipv4 address
            base_ipv6 {str} -- the ipv6 address
        """
        listAllIpv6 = []
        listCreatedIpv6 = []
        listCreatedIpv4 = []
        self.clear_file()
        cmd = f"ip addr show {NETWORK_IF_NAME}"
        argus = shlex.split(cmd)
        temp = subprocess.Popen(argus, stdout=subprocess.PIPE)
        # get the output as a string
        output = str(temp.communicate())
        wlan0OutputList = output.split('\\n')

        for ipv4 in wlan0OutputList:
            pattern = fr'inet ([0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}).*?scope .*?{NETWORK_IF_NAME}:\d+'
            createdIpv4 = re.findall(pattern, ipv4)
            if (len(createdIpv4) > 0):
                listCreatedIpv4.append(createdIpv4[0])
        for Ipv6 in wlan0OutputList:
            createdIpv6 = re.findall('inet6 (.*)/128 scope link', Ipv6)
            allIpv6 = re.findall('inet6 (.*)/[0-9]{1,3} scope link', Ipv6)

            if (len(allIpv6) > 0):
                listAllIpv6.append(allIpv6[0])

            if (len(createdIpv6) > 0):
                listCreatedIpv6.append(createdIpv6[0])

        # If list ip need to remove contain base ip ->remove it from list
        if (base_ipv4 in listCreatedIpv4):
            listCreatedIpv4.remove(base_ipv4)

        if (base_ipv6 in listCreatedIpv6):
            listCreatedIpv6.remove(base_ipv6)

        if ((len(listCreatedIpv4) > 0) or (len(listCreatedIpv6) > 0)):
            logging.info(
                f"Release Ip when start app: {listCreatedIpv4}, {listCreatedIpv6}")
        # remove ipv4
        if (len(listCreatedIpv4) > 0):
            for ipv4 in listCreatedIpv4:
                subprocess.run(["sudo", "ip", "addr", "del",
                               ipv4, "dev", NETWORK_IF_NAME])
            logging.info("Remove Ipv4 done!!!")
        # remove ipv6
        if (len(listCreatedIpv6) > 0) and (len(listAllIpv6) > 1):
            for ipv6 in listCreatedIpv6:
                subprocess.run(["sudo", "ip", "addr", "del",
                               ipv6, "dev", NETWORK_IF_NAME])
            logging.info("Remove Ipv6 done!!!")

    def update_ui_tab(self):
        """
        update UI tab.
        """
        # Update window title
        self.setWindowIcon(QIcon(RESOURCE_PATH + '/icons/matter_icon.jpg'))
        self.setWindowTitle(
            "Matter IoT Emulator v{}".format(
                self.tab.get_app_version()))
        # Update window size
        self.setMinimumSize(920, 780)

        settings = QSettings("LGE.HE.TSC", "MatterIoTEmulator")
        w = settings.value("width")
        if not w:
            w = 920
        h = settings.value("height")
        if not h:
            h = 780
        self.resize(int(w), int(h))

    def resizeEvent(self, event):
        """
        Handle resize event.

        Arguments:
            event {Object} -- the event object
        """
        super().resizeEvent(event)
        self.update_settings()
        self.update_ui_tab()
        self.adjust_tab_widget_size()
        self.overlay_widget.updateWidgetSize()

    def update_settings(self):
        settings = QSettings("LGE.HE.TSC", "MatterIoTEmulator")
        settings.setValue("width", self.width())
        settings.setValue("height", self.height())

    def adjust_tab_widget_size(self):
        tabWidgetWidth = self.width() - 100
        tabWidgetHeight = self.height() - 20
        self.tabWidget.setGeometry(50, 10, tabWidgetWidth, tabWidgetHeight)

    def addNewTab(self):
        newTab = QWidget()
        layout = QVBoxLayout(newTab)
        layout.setSizeConstraint(
            QLayout.SetDefaultConstraint)
        tab = MainWindow()
        tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(tab)
        self.max_number_of_device = tab.get_limit_devices_number()
        if self.number_tab < self.max_number_of_device:
            self.tabWidget.addTab(
                newTab,
                tab.ui.cbb_device_selection.currentText()[
                    :-8])

            tab.device_changed.connect(self.handle_update_name_tab)
            tab.device_started.connect(self.handle_device_started)
            tab.device_stopped.connect(
                self.handle_remove_targetId_when_stopped)
            tab.device_recover_done.connect(self.close_message_box)
            self.listTab.append(tab)

            # Set the current index for the newly added tab
            self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)
            self.number_tab += 1
            self.overlay_widget.hide()
        else:
            QMessageBox.question(
                self, "Warning", "We only support {} devices work at the same time".format(
                    tab.get_limit_devices_number()), QMessageBox.Ok)

    def handle_update_name_tab(self, device_changed):
        self.tabWidget.setTabText(
            self.tabWidget.currentIndex(),
            device_changed)

    def clear_file(self):
        file = open(DEVICE_LIST_PATH, 'w')
        file.close()

    def save_device_list_file(self):
        deviceList = ":".join(self.listDevice)
        fileListDevice = open(DEVICE_LIST_PATH, "w+")
        fileListDevice.write(deviceList)
        fileListDevice.close()

    def remove_targetId_when_close_tab(self, index):
        value = self.listTab[index].targetId
        if (value in self.listDevice):
            self.listDevice.remove(value)
            self.save_device_list_file()

    def handle_update_name_tab(self, device_changed):
        self.tabWidget.setTabText(
            self.tabWidget.currentIndex(),
            device_changed)

    def handle_remove_targetId_when_stopped(self, deviceID):
        if (deviceID in self.listDevice):
            self.listDevice.remove(deviceID)

    def handle_device_started(self, deviceID):
        if ((deviceID != "") and (deviceID not in self.listDevice)):
            self.listDevice.append(deviceID)
            self.save_device_list_file()

    def closeTab(self, index):
        reply = QMessageBox.question(
            self,
            "Close Tab",
            "Do You Want To Close The Tab?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.tabWidget.count() >= 1:
                if (self.listTab[index].ui.btn_start_device.text()
                        == "Stop Device"):
                    if len(list_status_device) > 0:
                        list_status_device.remove(1)
                    self.listTab[index].ip_value.removeIpAfterStopDevice()
                    self.listTab[index].ip_value.releaseRpcPort(
                        self.listTab[index].rpcPort)
                    self.remove_targetId_when_close_tab(index)
                    HandleRecoverDevices.remove_recover_devices(
                        self.listTab[index].targetId)
                    self.listTab[index].stop_thread()

                if (self.listTab[index].connected_device):
                    self.listTab[index].remove_info_list(
                        self.listTab[index].ui.cbb_device_selection.currentText())

                # Delete device when close tab
                self.listTab[index].handle_recover_devices.remove_storage_folder(
                    self.listTab[index].targetId)

                if 1 == self.tabWidget.count():
                    self.addNewTab()

                self.listTab.remove(self.listTab[index])
                self.tabWidget.removeTab(index)
                self.number_tab -= 1
                self.overlay_widget.hide()
                
        elif reply == QMessageBox.No:
            pass

    def closeTcpDump(self):
        """
        Close TCP dump file.
        """
        try:
            if self.tcpDump is not None:
                self.tcpDump.stop()
                self.tcpDump = None
        except PermissionError:
            logging.info('Command is already done')

    def closeEvent(self, event):
        """
        Close event.
        """
        list_device_connect.clear()
        for tab in self.listTab:
            if ((not tab.connected_device) and (not tab.is_recover)):
                tab.handle_recover_devices.remove_storage_folder(tab.targetId)
            if (tab.ui.btn_start_device.text() == "Stop Device"):
                logging.info(f"Device connected: {tab.connected_device}")
                tab.ip_value.removeIpAfterStopDevice()
                tab.ip_value.releaseRpcPort(tab.rpcPort)
                tab.stop_thread()

        self.tab.load_network_config()
        self.clear_file()
        self.closeTcpDump()

        logging.info("Wait a second for closing current works...")
        logging.info(
            "-------------Matter Emulator closed completely!---------------")
        os._exit(0)


if __name__ == "__main__":
    app = QApplication([])
    mainWindow = Main()
    mainWindow.show()
    if mainWindow.is_recover_device:
        mainWindow.show_message_box()
    sysExit(app.exec_())
