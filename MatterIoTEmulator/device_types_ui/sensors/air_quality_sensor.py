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
import os
import time
from rpc.airqualitysensor_client import AirqualityClient
from ..stoppablethread import UpdateStatusThread
from ..constants_device import *
from constants import *
from ..device_base_ui import *

SOURCE_PATH = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))
DEVICE_RESOURCE_PATH = os.path.join(SOURCE_PATH, "res/sensors/")


UNKNOWN = 0
GOOD = 1
FAIR = 2
MODERATE = 3
POOR = 4
VERY_POOR = 5
EXTREMELY_POOR = 6


class AirQualitySensor(BaseDeviceUI):
    """
    AirQualitySensor device UI controller represent some attribues, clusters
    and endpoints corresspoding to Matter Specification v1.2
    """

    def __init__(self, parent) -> None:
        """
        Create a new `AirQualitySensor` UI.
        :param parent: An UI object load AirQualitySensor device UI controller.
        """
        super().__init__(parent)
        self.temperature = 0
        self.humidity = 0
        self.concentration = 0
        self.airquality = UNKNOWN
        self.time_repeat = 0
        self.time_sleep = 0
        self.remaining_time_interval = 0
        self.is_stop_clicked = False

        self.is_edit_temp = True
        self.is_edit_hum = True
        self.is_edit_pm25 = True
        self.is_edit_co = True
        self.is_edit_co2 = True
        self.is_edit_no2 = True
        self.is_edit_o3 = True
        self.is_edit_ch2o = True
        self.is_edit_pm1 = True
        self.is_edit_pm10 = True
        self.is_edit_tvoc = True
        self.is_edit_rn = True

        # Show icon
        self.lbl_main_icon = QLabel()
        pix = QPixmap(DEVICE_RESOURCE_PATH + 'air-quality-sensor.png')
        self.lbl_main_icon.setFixedSize(70, 70)
        pix = pix.scaled(
            self.lbl_main_icon.size(),
            aspectMode=Qt.KeepAspectRatio)
        self.lbl_main_icon.setPixmap(pix)
        self.lbl_main_icon.setAlignment(Qt.AlignCenter)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.lbl_main_icon)
        self.parent.ui.lo_controller.addLayout(h_layout)

        # Label air quality
        self.lbl_air_quality_status = QLabel()
        self.lbl_air_quality_status.setText('Air quality :')
        self.lbl_air_quality_status.setAlignment(Qt.AlignCenter)

        self.bt_air = QPushButton()
        self.bt_air.setMaximumSize(QSize(120, 20))
        self.bt_air.setEnabled(False)

        self.grid_layout = QHBoxLayout()
        self.grid_layout.addWidget(
            self.lbl_air_quality_status,
            alignment=Qt.AlignRight)
        self.grid_layout.addWidget(self.bt_air, alignment=Qt.AlignLeft)
        self.parent.ui.lo_controller.addLayout(self.grid_layout)

        # Local temperature
        self.lbl_temperature_status = QLabel()
        self.lbl_temperature_status.setText('Local Temperature :')
        self.lbl_temperature_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_temperature_status)

        # Line edit for temperature
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
            self.lbl_temperature_status,
            alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.line_edit_temp, alignment=Qt.AlignRight)
        self.grid_layout_temp.addWidget(
            self.lbl_measure, alignment=Qt.AlignRight)

        self.line_edit_temp.textEdited.connect(self.on_text_edited_temp)
        self.line_edit_temp.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_temp)

        # Humidity
        self.lbl_hum_status = QLabel()
        self.lbl_hum_status.setText('Local Humidity :')
        self.lbl_hum_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_hum_status)

        # Line edit for Humidity
        self.line_edit_hum = QLineEdit()
        self.line_edit_hum.setValidator(self.validator)
        self.line_edit_hum.setValidator(self.double_validator)
        self.line_edit_hum.setMaximumSize(QSize(65, 20))
        self.lbl_measure_hum = QLabel()
        self.lbl_measure_hum.setText('%')
        self.grid_layout_hum = QHBoxLayout()
        self.grid_layout_hum.setAlignment(Qt.AlignCenter)
        self.grid_layout_hum.addWidget(
            self.lbl_hum_status, alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.line_edit_hum, alignment=Qt.AlignRight)
        self.grid_layout_hum.addWidget(
            self.lbl_measure_hum, alignment=Qt.AlignRight)

        self.line_edit_hum.textEdited.connect(self.on_text_edited_hum)
        self.line_edit_hum.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_hum)

        # PM2.5 Concentration
        self.lbl_concentration_status = QLabel()
        self.lbl_concentration_status.setText('PM2.5 Concentration :')
        self.lbl_concentration_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_concentration_status)

        self.line_edit_pm25 = QLineEdit()
        self.line_edit_pm25.setValidator(self.validator)
        self.line_edit_pm25.setValidator(self.double_validator)
        self.line_edit_pm25.setMaximumSize(QSize(65, 20))
        self.lbl_measure_pm25 = QLabel()
        self.lbl_measure_pm25.setText('PPM')
        self.grid_layout_pm25 = QHBoxLayout()
        self.grid_layout_pm25.setAlignment(Qt.AlignCenter)
        self.grid_layout_pm25.addWidget(
            self.lbl_concentration_status,
            alignment=Qt.AlignRight)
        self.grid_layout_pm25.addWidget(
            self.line_edit_pm25, alignment=Qt.AlignRight)
        self.grid_layout_pm25.addWidget(
            self.lbl_measure_pm25, alignment=Qt.AlignRight)

        self.line_edit_pm25.textEdited.connect(self.on_text_edited_pm25)
        self.line_edit_pm25.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_pm25)

        # Carbon Monoxide
        self.lbl_co_status = QLabel()
        self.lbl_co_status.setText('Carbon Monoxide :')
        self.lbl_co_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_co_status)

        # Line edit for Carbon Monoxide
        self.line_edit_co = QLineEdit()
        self.line_edit_co.setValidator(self.validator)
        self.line_edit_co.setValidator(self.double_validator)
        self.line_edit_co.setMaximumSize(QSize(65, 20))
        self.lbl_measure_co = QLabel()
        self.lbl_measure_co.setText('UGM3')
        self.grid_layout_co = QHBoxLayout()
        self.grid_layout_co.setAlignment(Qt.AlignCenter)
        self.grid_layout_co.addWidget(
            self.lbl_co_status, alignment=Qt.AlignRight)
        self.grid_layout_co.addWidget(
            self.line_edit_co, alignment=Qt.AlignRight)
        self.grid_layout_co.addWidget(
            self.lbl_measure_co, alignment=Qt.AlignRight)

        self.line_edit_co.textEdited.connect(self.on_text_edited_co)
        self.line_edit_co.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_co)

        # Carbon dioxide
        self.lbl_co2_status = QLabel()
        self.lbl_co2_status.setText('Carbon Dioxide:')
        self.lbl_co2_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_co2_status)

        # Line edit for Carbon dioxide
        self.line_edit_co2 = QLineEdit()
        self.line_edit_co2.setValidator(self.validator)
        self.line_edit_co2.setValidator(self.double_validator)
        self.line_edit_co2.setMaximumSize(QSize(65, 20))
        self.lbl_measure_co2 = QLabel()
        self.lbl_measure_co2.setText('UGM3')
        self.grid_layout_co2 = QHBoxLayout()
        self.grid_layout_co2.setAlignment(Qt.AlignCenter)
        self.grid_layout_co2.addWidget(
            self.lbl_co2_status, alignment=Qt.AlignRight)
        self.grid_layout_co2.addWidget(
            self.line_edit_co2, alignment=Qt.AlignRight)
        self.grid_layout_co2.addWidget(
            self.lbl_measure_co2, alignment=Qt.AlignRight)

        self.line_edit_co2.textEdited.connect(self.on_text_edited_co2)
        self.line_edit_co2.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_co2)

        # Nitrogen dioxide
        self.lbl_no2_status = QLabel()
        self.lbl_no2_status.setText('Nitrogen Dioxide :')
        self.lbl_no2_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_no2_status)

        # Line edit for Nitrogen dioxide
        self.line_edit_no2 = QLineEdit()
        self.line_edit_no2.setValidator(self.validator)
        self.line_edit_no2.setValidator(self.double_validator)
        self.line_edit_no2.setMaximumSize(QSize(65, 20))
        self.lbl_measure_no2 = QLabel()
        self.lbl_measure_no2.setText('UGM3')
        self.grid_layout_no2 = QHBoxLayout()
        self.grid_layout_no2.setAlignment(Qt.AlignCenter)
        self.grid_layout_no2.addWidget(
            self.lbl_no2_status, alignment=Qt.AlignRight)
        self.grid_layout_no2.addWidget(
            self.line_edit_no2, alignment=Qt.AlignRight)
        self.grid_layout_no2.addWidget(
            self.lbl_measure_no2, alignment=Qt.AlignRight)

        self.line_edit_no2.textEdited.connect(self.on_text_edited_no2)
        self.line_edit_no2.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_no2)

        # Ozone Cencentration
        self.lbl_o3_status = QLabel()
        self.lbl_o3_status.setText('Ozone Cencentration :')
        self.lbl_o3_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_o3_status)

        # Line edit for Nitrogen dioxide
        self.line_edit_o3 = QLineEdit()
        self.line_edit_o3.setValidator(self.validator)
        self.line_edit_o3.setValidator(self.double_validator)
        self.line_edit_o3.setMaximumSize(QSize(65, 20))
        self.lbl_measure_o3 = QLabel()
        self.lbl_measure_o3.setText('UGM3')
        self.grid_layout_o3 = QHBoxLayout()
        self.grid_layout_o3.setAlignment(Qt.AlignCenter)
        self.grid_layout_o3.addWidget(
            self.lbl_o3_status, alignment=Qt.AlignRight)
        self.grid_layout_o3.addWidget(
            self.line_edit_o3, alignment=Qt.AlignRight)
        self.grid_layout_o3.addWidget(
            self.lbl_measure_o3, alignment=Qt.AlignRight)

        self.line_edit_o3.textEdited.connect(self.on_text_edited_o3)
        self.line_edit_o3.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_o3)

        # Formaldehyde Concentration
        self.lbl_ch2o_status = QLabel()
        self.lbl_ch2o_status.setText('Formaldehyde Concentration :')
        self.lbl_ch2o_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_ch2o_status)

        # Line edit for Nitrogen dioxide
        self.line_edit_ch2o = QLineEdit()
        self.line_edit_ch2o.setValidator(self.validator)
        self.line_edit_ch2o.setValidator(self.double_validator)
        self.line_edit_ch2o.setMaximumSize(QSize(65, 20))
        self.lbl_measure_ch2o = QLabel()
        self.lbl_measure_ch2o.setText('UGM3')
        self.grid_layout_ch2o = QHBoxLayout()
        self.grid_layout_ch2o.setAlignment(Qt.AlignCenter)
        self.grid_layout_ch2o.addWidget(
            self.lbl_ch2o_status, alignment=Qt.AlignRight)
        self.grid_layout_ch2o.addWidget(
            self.line_edit_ch2o, alignment=Qt.AlignRight)
        self.grid_layout_ch2o.addWidget(
            self.lbl_measure_ch2o, alignment=Qt.AlignRight)

        self.line_edit_ch2o.textEdited.connect(self.on_text_edited_ch2o)
        self.line_edit_ch2o.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_ch2o)

        # PM1 Concentration
        self.lbl_pm1_status = QLabel()
        self.lbl_pm1_status.setText('PM1 Concentration :')
        self.lbl_pm1_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_pm1_status)
        # Line edit for PM1 Concentration
        self.line_edit_pm1 = QLineEdit()
        self.line_edit_pm1.setValidator(self.validator)
        self.line_edit_pm1.setValidator(self.double_validator)
        self.line_edit_pm1.setMaximumSize(QSize(65, 20))
        self.lbl_measure_pm1 = QLabel()
        self.lbl_measure_pm1.setText('PPM')
        self.grid_layout_pm1 = QHBoxLayout()
        self.grid_layout_pm1.setAlignment(Qt.AlignCenter)
        self.grid_layout_pm1.addWidget(
            self.lbl_pm1_status, alignment=Qt.AlignRight)
        self.grid_layout_pm1.addWidget(
            self.line_edit_pm1, alignment=Qt.AlignRight)
        self.grid_layout_pm1.addWidget(
            self.lbl_measure_pm1, alignment=Qt.AlignRight)

        self.line_edit_pm1.textEdited.connect(self.on_text_edited_pm1)
        self.line_edit_pm1.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_pm1)

        # PM10 Concentration
        self.lbl_pm10_status = QLabel()
        self.lbl_pm10_status.setText('PM10 Concentration :')
        self.lbl_pm10_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_pm10_status)
        # Line edit for PM1 Concentration
        self.line_edit_pm10 = QLineEdit()
        self.line_edit_pm10.setValidator(self.validator)
        self.line_edit_pm10.setValidator(self.double_validator)
        self.line_edit_pm10.setMaximumSize(QSize(65, 20))
        self.lbl_measure_pm10 = QLabel()
        self.lbl_measure_pm10.setText('PPM')
        self.grid_layout_pm10 = QHBoxLayout()
        self.grid_layout_pm10.setAlignment(Qt.AlignCenter)
        self.grid_layout_pm10.addWidget(
            self.lbl_pm10_status, alignment=Qt.AlignRight)
        self.grid_layout_pm10.addWidget(
            self.line_edit_pm10, alignment=Qt.AlignRight)
        self.grid_layout_pm10.addWidget(
            self.lbl_measure_pm10, alignment=Qt.AlignRight)

        self.line_edit_pm10.textEdited.connect(self.on_text_edited_pm10)
        self.line_edit_pm10.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_pm10)

        # Total Volatile Organic Compounds Concentration
        self.lbl_tvoc_status = QLabel()
        self.lbl_tvoc_status.setText('Total Volatile Organic Compounds :')
        self.lbl_tvoc_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_tvoc_status)

        # Line edit for PM1 Concentration
        self.line_edit_tvoc = QLineEdit()
        self.line_edit_tvoc.setValidator(self.validator)
        self.line_edit_tvoc.setValidator(self.double_validator)
        self.line_edit_tvoc.setMaximumSize(QSize(65, 20))
        self.lbl_measure_tvoc = QLabel()
        self.lbl_measure_tvoc.setText('PPM')
        self.grid_layout_tvoc = QHBoxLayout()
        self.grid_layout_tvoc.setAlignment(Qt.AlignCenter)
        self.grid_layout_tvoc.addWidget(
            self.lbl_tvoc_status, alignment=Qt.AlignRight)
        self.grid_layout_tvoc.addWidget(
            self.line_edit_tvoc, alignment=Qt.AlignRight)
        self.grid_layout_tvoc.addWidget(
            self.lbl_measure_tvoc, alignment=Qt.AlignRight)

        self.line_edit_tvoc.textEdited.connect(self.on_text_edited_tvoc)
        self.line_edit_tvoc.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_tvoc)

        # Radon Concentration Measurement
        self.lbl_rn_status = QLabel()
        self.lbl_rn_status.setText('Radon Concentration :')
        self.lbl_rn_status.setAlignment(Qt.AlignCenter)
        self.parent.ui.lo_controller.addWidget(self.lbl_rn_status)

        # Line edit for PM1 Concentration
        self.line_edit_rn = QLineEdit()
        self.line_edit_rn.setValidator(self.validator)
        self.line_edit_rn.setValidator(self.double_validator)
        self.line_edit_rn.setMaximumSize(QSize(65, 20))
        self.lbl_measure_rn = QLabel()
        self.lbl_measure_rn.setText('UGM3')
        self.grid_layout_rn = QHBoxLayout()
        self.grid_layout_rn.setAlignment(Qt.AlignCenter)
        self.grid_layout_rn.addWidget(
            self.lbl_rn_status, alignment=Qt.AlignRight)
        self.grid_layout_rn.addWidget(
            self.line_edit_rn, alignment=Qt.AlignRight)
        self.grid_layout_rn.addWidget(
            self.lbl_measure_rn, alignment=Qt.AlignRight)

        self.line_edit_rn.textEdited.connect(self.on_text_edited_rn)
        self.line_edit_rn.returnPressed.connect(self.on_return_pressed)
        self.parent.ui.lo_controller.addLayout(self.grid_layout_rn)

        # Init rpc
        self.client = AirqualityClient(self.config)
        self.contact_value = True
        self.set_initial_value()
        self.start_update_device_status_thread()

        logging.debug("Init contact sensor done")

    def on_text_edited_temp(self):
        """Enable 'is_edit_temp' attribute
        when line edit temperature is editting"""
        self.is_edit_temp = False

    def on_text_edited_hum(self):
        """Enable 'is_edit_hum' attribute
        when line edit humidity is editting"""
        self.is_edit_hum = False

    def on_text_edited_pm25(self):
        """Enable 'is_edit_pm25' attribute
        when line edit pm25 is editting"""
        self.is_edit_pm25 = False

    def on_text_edited_co(self):
        """Enable 'is_edit_co' attribute
        when line edit co is editting"""
        self.is_edit_co = False

    def on_text_edited_co2(self):
        """Enable 'is_edit_co2' attribute
        when line edit co2 is editting"""
        self.is_edit_co2 = False

    def on_text_edited_no2(self):
        """Enable 'is_edit_no2' attribute
        when line edit no2 is editting"""
        self.is_edit_no2 = False

    def on_text_edited_o3(self):
        """Enable 'is_edit_o3' attribute
        when line edit o3 is editting"""
        self.is_edit_o3 = False

    def on_text_edited_ch2o(self):
        """Enable 'is_edit_ch2o' attribute
        when line edit ch2o is editting"""
        self.is_edit_ch2o = False

    def on_text_edited_pm1(self):
        """Enable 'is_edit_pm1' attribute
        when line edit pm1 is editting"""
        self.is_edit_pm1 = False

    def on_text_edited_pm10(self):
        """Enable 'is_edit_pm10' attribute
        when line edit pm10 is editting"""
        self.is_edit_pm10 = False

    def on_text_edited_tvoc(self):
        """Enable 'is_edit_tvoc' attribute
        when line edit tvoc is editting"""
        self.is_edit_tvoc = False

    def on_text_edited_rn(self):
        """
        Enable 'is_edit_rn' attribute when line edit
        randon measurement is editting
        """
        self.is_edit_rn = False

    def on_return_pressed(self):
        """
        Handle update all concentrance measurement attributes
        to matter device(backend) through rpc service
        after enter value to line edit done
        """
        try:
            value_temp = round(float(self.line_edit_temp.text()) * 100)
            value_hum = round(float(self.line_edit_hum.text()) * 100)
            value_pm25 = round(float(self.line_edit_pm25.text()), 2)
            value_co = round(float(self.line_edit_co.text()), 2)
            value_co2 = round(float(self.line_edit_co2.text()), 2)
            value_no2 = round(float(self.line_edit_no2.text()), 2)
            value_o3 = round(float(self.line_edit_o3.text()), 2)
            value_ch2o = round(float(self.line_edit_ch2o.text()), 2)
            value_pm1 = round(float(self.line_edit_pm1.text()), 2)
            value_pm10 = round(float(self.line_edit_pm10.text()), 2)
            value_tvoc = round(float(self.line_edit_tvoc.text()), 2)
            value_rn = round(float(self.line_edit_rn.text()), 2)

            if 0 <= value_temp <= 10000:
                data = {
                    'temperatureMeasurement': {
                        'measuredValue': value_temp}}
                self.client.set(data)
                self.is_edit_temp = True
            else:
                self.message_box(ER_TEMP)
                self.line_edit_temp.setText(str(self.temperature))

            if 0 <= value_hum <= 10000:
                data = {
                    'relativeHumidityMeasurement': {
                        'measuredValue': value_hum}}
                self.client.set(data)
                self.is_edit_hum = True
            else:
                self.message_box(ER_HUM)
                self.line_edit_hum.setText(str(self.humidity))

            if 0 <= value_pm25 <= 300:
                data = {
                    'pm25ConcentrationMeasurement': {
                        'measuredValue': value_pm25}}
                self.client.set(data)
                self.is_edit_pm25 = True
            else:
                self.message_box(ER_PM25)
                self.line_edit_pm25.setText(str(self.pm25))

            if 0 <= value_co <= 300:
                data = {'carbonMonoxideConcentrationMeasurement':
                            {'measuredValue': value_co}}
                self.client.set(data)
                self.is_edit_co = True
            else:
                self.message_box(ER_CO)
                self.line_edit_co.setText(str(self.co))

            if 0 <= value_co2 <= 300:
                data = {'carbonDioxideConcentrationMeasurement':
                            {'measuredValue': value_co2}}
                self.client.set(data)
                self.is_edit_co2 = True
            else:
                self.message_box(ER_CO2)
                self.line_edit_co2.setText(str(self.co2))

            if 0 <= value_no2 <= 300:
                data = {'nitrogenDioxideConcentrationMeasurement':
                            {'measuredValue': value_no2}}
                self.client.set(data)
                self.is_edit_no2 = True
            else:
                self.message_box(ER_NO2)
                self.line_edit_no2.setText(str(self.no2))
            if 0 <= value_o3 <= 300:
                data = {'ozoneConcentrationMeasurement':
                            {'measuredValue': value_o3}}
                self.client.set(data)
                self.is_edit_o3 = True
            else:
                self.message_box(ER_O3)
                self.line_edit_o3.setText(str(self.o3))
            if 0 <= value_ch2o <= 300:
                data = {
                    'formaldehydeConcentrationMeasurement': {
                        'measuredValue': value_ch2o}}
                self.client.set(data)
                self.is_edit_ch2o = True
            else:
                self.message_box(ER_CH2O)
                self.line_edit_ch2o.setText(str(self.ch2o))
            if 0 <= value_pm1 <= 300:
                data = {
                    'pm1ConcentrationMeasurement': {
                        'measuredValue': value_pm1}}
                self.client.set(data)
                self.is_edit_pm1 = True
            else:
                self.message_box(ER_PM1)
                self.line_edit_pm1.setText(str(self.pm1))
            if 0 <= value_pm10 <= 300:
                data = {
                    'pm10ConcentrationMeasurement': {
                        'measuredValue': value_pm10}}
                self.client.set(data)
                self.is_edit_pm10 = True
            else:
                self.message_box(ER_PM10)
                self.line_edit_pm10.setText(str(self.pm10))
            if 0 <= value_rn <= 300:
                data = {
                    'radonConcentrationMeasurement': {
                        'measuredValue': value_rn}}
                self.client.set(data)
                self.is_edit_rn = True
            else:
                self.message_box(ER_RN)
                self.line_edit_rn.setText(str(self.rn))

            if 0 <= value_tvoc <= 300:
                data = {
                    'totalVolatileOrganicCompoundsConcentrationMeasurement': {
                        'measuredValue': value_tvoc}}
                self.client.set(data)
                self.is_edit_tvoc = True
            else:
                self.message_box(ER_TVOC)
                self.line_edit_tvoc.setText(str(self.tvoc))

        except Exception as e:
            logging.error("Error: " + str(e))

    def message_box(self, message):
        """
        Message box to notify value out of range when set value to line edit
        :param message: The notify message to user
        """
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle("Air Quality SenSor")
        msgBox.setText("Value out of range")
        msgBox.setInformativeText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def set_initial_value(self):
        """
        Handle set initial value of all supported attributes
        to matter device(backend) through rpc service
        """
        try:
            data = {
                'airQuality': {'airQuality': GOOD},
                'relativeHumidityMeasurement': {'measuredValue': 4000},
                'temperatureMeasurement': {'measuredValue': 2800},
                'pm25ConcentrationMeasurement': {'measuredValue': 20},
                'carbonMonoxideConcentrationMeasurement': {'measuredValue': 5.0},
                'carbonDioxideConcentrationMeasurement': {'measuredValue': 5.0},
                'nitrogenDioxideConcentrationMeasurement': {'measuredValue': 5.0},
                'ozoneConcentrationMeasurement': {'measuredValue': 5.0},
                'formaldehydeConcentrationMeasurement': {'measuredValue': 5.0},
                'pm1ConcentrationMeasurement': {'measuredValue': 5.0},
                'pm10ConcentrationMeasurement': {'measuredValue': 5.0},
                'radonConcentrationMeasurement': {'measuredValue': 5.0},
                'totalVolatileOrganicCompoundsConcentrationMeasurement': {
                    'measuredValue': 5.0}
                }
            self.client.set(data)
        except Exception as e:
            self.parent.wkr.connect_status.emit(STT_RPC_INIT_FAIL)
            logging.error("Can not set initial value: " + str(e))

    def check_pm25(self, pm25):
        """
        Check value of pm2.5 measurement to set air quality attribute
        :param pm25: Value of pm2.5 measurement
        """
        if 0 < self.pm25 <= 50:
            data_air = {'airQuality': {'airQuality': GOOD}}
            self.client.set(data_air)
        elif 50 < self.pm25 <= 100:
            data_air = {'airQuality': {'airQuality': FAIR}}
            self.client.set(data_air)
        elif 100 < self.pm25 <= 150:
            data_air = {'airQuality': {'airQuality': MODERATE}}
            self.client.set(data_air)
        elif 150 < self.pm25 <= 200:
            data_air = {'airQuality': {'airQuality': POOR}}
            self.client.set(data_air)
        elif 200 < self.pm25 <= 250:
            data_air = {'airQuality': {'airQuality': VERY_POOR}}
            self.client.set(data_air)
        elif 250 < self.pm25 <= 300:
            data_air = {'airQuality': {'airQuality': EXTREMELY_POOR}}
            self.client.set(data_air)
        else:
            data_air = {'airQuality': {'airQuality': UNKNOWN}}
            self.client.set(data_air)

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
            self.pm25 = round(
                float(
                    device_status['reply']['pm25ConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_pm25:
                self.line_edit_pm25.setText(str(self.pm25))
            self.check_pm25(self.pm25)
            if device_status['status'] == 'OK':
                self.airquality = device_status['reply']['airQuality']['airQuality']
                if self.airquality == UNKNOWN:
                    self.bt_air.setText('Unknown')
                    self.bt_air.setStyleSheet("background-color: green")
                elif self.airquality == GOOD:
                    self.bt_air.setText('Good')
                    self.bt_air.setStyleSheet(
                        "background-color: #66FF00; color: black")
                elif self.airquality == FAIR:
                    self.bt_air.setText('Fair')
                    self.bt_air.setStyleSheet(
                        "background-color: #FFFF33; color: black")
                elif self.airquality == MODERATE:
                    self.bt_air.setText('Moderate')
                    self.bt_air.setStyleSheet(
                        "background-color: #FF9900; color: black")
                elif self.airquality == POOR:
                    self.bt_air.setText('Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #FF6699; color: black")
                elif self.airquality == VERY_POOR:
                    self.bt_air.setText('Very Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #CC66CC; color: black")
                elif self.airquality == EXTREMELY_POOR:
                    self.bt_air.setText('Extremely Poor')
                    self.bt_air.setStyleSheet(
                        "background-color: #996699; color: black")
                self.bt_air.adjustSize()
            self.temperature = round(
                (device_status['reply']['temperatureMeasurement']['measuredValue']) / 100.0, 2)
            if self.is_edit_temp:
                self.line_edit_temp.setText(str(self.temperature))

            self.humidity = round(
                (device_status['reply']['relativeHumidityMeasurement']['measuredValue']) / 100.0, 2)
            if self.is_edit_hum:
                self.line_edit_hum.setText(str(self.humidity))

            self.co = round(
                float(
                    device_status['reply']['carbonMonoxideConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_co:
                self.line_edit_co.setText(str(self.co))
            self.co2 = round(
                float(
                    device_status['reply']['carbonDioxideConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_co2:
                self.line_edit_co2.setText(str(self.co2))
            self.no2 = round(
                float(
                    device_status['reply']['nitrogenDioxideConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_no2:
                self.line_edit_no2.setText(str(self.no2))
            self.o3 = round(
                float(
                    device_status['reply']['ozoneConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_o3:
                self.line_edit_o3.setText(str(self.o3))
            self.ch2o = round(
                float(
                    device_status['reply']['formaldehydeConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_ch2o:
                self.line_edit_ch2o.setText(str(self.ch2o))
            self.pm1 = round(
                float(
                    device_status['reply']['pm1ConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_pm1:
                self.line_edit_pm1.setText(str(self.pm1))
            self.pm10 = round(
                float(
                    device_status['reply']['pm10ConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_pm10:
                self.line_edit_pm10.setText(str(self.pm10))
            self.rn = round(
                float(
                    device_status['reply']['radonConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_rn:
                self.line_edit_rn.setText(str(self.rn))
            self.tvoc = round(
                float(
                    device_status['reply']['totalVolatileOrganicCompoundsConcentrationMeasurement']['measuredValue']), 2)
            if self.is_edit_tvoc:
                self.line_edit_tvoc.setText(str(self.tvoc))

            # self.lbl_remain_repeat_time.setText('Remaining count: ' + str(self.time_repeat))
            # self.lbl_remaining_time_interval.setText('Remaining time of interval: ' + str(self.remaining_time_interval) + " sec")
        except Exception as e:
            logging.error("Error: " + str(e))

    def stop(self):
        """
        Stop thread update device status
        Stop rpc client
        """
        self.stop_update_state_thread()
        self.stop_client_rpc()
