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


class OverlayWidget(QWidget):
    """
    Overlay client class for creating a device.
    """

    def __init__(self, parent):
        """
        Initialize a Overlay widget instance.
        """
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """
        Initialize a List device label.
        """
        self.setGeometry(
            50,
            10,
            self.parent().tabWidget.width(),
            self.parent().tabWidget.height())
        self.widget = QWidget(self)
        self.widget.setGeometry(
            50,
            10,
            self.parent().tabWidget.width(),
            self.parent().tabWidget.height())
        self.widget.setStyleSheet("background-color: aliceblue;")
        self.layout = QVBoxLayout(self.widget)

        #######################
        self.label_tt = QLabel()
        self.label_tt.setObjectName(u"label_tt")
        self.label_tt.setMaximumSize(QSize(16777215, 50))
        self.label_tt.setAlignment(Qt.AlignCenter)
        self.label_tt.setStyleSheet('color: cornflowerblue')
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(50)
        self.label_tt.setFont(font)

        self.pushButton = QPushButton("HIDE", self)
        self.pushButton.setFixedSize(50, 30)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setStyleSheet("background-color: cyan;")
        self.layout.addWidget(self.pushButton)

        self.layout.addWidget(self.label_tt)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_2 = QLabel()
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_2)

        self.label = QLabel()
        self.label.setObjectName(u"label")
        self.label.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label)

        self.label_3 = QLabel()
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_3)

        self.label_4 = QLabel()
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_4)

        self.label_5 = QLabel()
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_5)

        self.label_6 = QLabel()
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_6)

        self.label_7 = QLabel()
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_7)

        self.label_8 = QLabel()
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_8)

        self.label_9 = QLabel()
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_4.addWidget(self.label_9)

        self.horizontalLayout.addLayout(self.verticalLayout_4)
        self.horizontalSpacer = QSpacerItem(
            10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        self.label_11 = QLabel()
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_11)

        self.label_12 = QLabel()
        self.label_12.setObjectName(u"label_12")
        self.label_12.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_12)

        self.label_13 = QLabel()
        self.label_13.setObjectName(u"label_13")
        self.label_13.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_13)

        self.label_14 = QLabel()
        self.label_14.setObjectName(u"label_14")
        self.label_14.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_14)

        self.label_15 = QLabel()
        self.label_15.setObjectName(u"label_15")
        self.label_15.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_15)

        self.label_16 = QLabel()
        self.label_16.setObjectName(u"label_16")
        self.label_16.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_16)

        self.label_17 = QLabel()
        self.label_17.setObjectName(u"label_17")
        self.label_17.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_17)

        self.label_18 = QLabel()
        self.label_18.setObjectName(u"label_18")
        self.label_18.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_18)

        self.label_10 = QLabel()
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_5.addWidget(self.label_10)

        self.horizontalLayout.addLayout(self.verticalLayout_5)
        self.layout.addLayout(self.horizontalLayout)
        self.verticalSpacer = QSpacerItem(
            40, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")

        self.label_19 = QLabel()
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_19)

        self.label_21 = QLabel("", self)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_21)

        self.label_22 = QLabel("", self)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_22)

        self.label_23 = QLabel("", self)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_23)

        self.label_24 = QLabel("", self)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_24)

        self.label_25 = QLabel("", self)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_25)

        self.label_26 = QLabel("", self)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_26)

        self.label_27 = QLabel("", self)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_27)

        self.label_28 = QLabel("", self)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalLayout_6.addWidget(self.label_28)

        self.horizontalLayout.addLayout(self.verticalLayout_6)
        self.layout.addLayout(self.horizontalLayout)
        self.verticalSpacer = QSpacerItem(
            40, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.layout.addItem(self.verticalSpacer)
        self.pushButton.clicked.connect(self.hideOverlay)

    def updateWidgetSize(self):
        """
        Update list widget size.
        """
        self.setGeometry(
            30,
            30,
            self.parent().tabWidget.width() +
            10,
            self.parent().tabWidget.height() -
            35)
        self.widget.setGeometry(
            30,
            30,
            self.parent().tabWidget.width() +
            10,
            self.parent().tabWidget.height() -
            35)

    def hideOverlay(self):
        """
        Hide Overlay widget.
        """
        self.hide()

    def update_lbwidget(self, num_connect, num):
        """
        Update label widget.
        """
        # self.ui.label_tt.setText("Current connected Devices / Open Tabs : 0/{}".format(num))
        self.label_tt.setText(
            "Current connected Devices / Open Tabs : {}/{}".format(num_connect, num))
