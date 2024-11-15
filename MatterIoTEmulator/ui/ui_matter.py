# -*- coding: utf-8 -*-

##########################################################################
# Form generated from reading UI file 'matterkPoNox.ui'
##
# Created by: Qt User Interface Compiler version 5.15.2
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
##########################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Matter(object):
    def setupUi(self, Matter):
        if not Matter.objectName():
            Matter.setObjectName(u"Matter")
        Matter.resize(640, 480)
        self.centralwidget = QWidget(Matter)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_app_name = QLabel(self.centralwidget)
        self.lbl_app_name.setObjectName(u"lbl_app_name")
        self.lbl_app_name.setMaximumSize(QSize(16777215, 30))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.lbl_app_name.setFont(font)
        self.lbl_app_name.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.lbl_app_name)

        self.lo_all = QHBoxLayout()
        self.lo_all.setObjectName(u"lo_all")
        self.lo_device_selection_2 = QGroupBox(self.centralwidget)
        self.lo_device_selection_2.setObjectName(u"lo_device_selection_2")
        self.lo_device_selection = QVBoxLayout(self.lo_device_selection_2)
        self.lo_device_selection.setObjectName(u"lo_device_selection")
        self.cbb_device_selection = QComboBox(self.lo_device_selection_2)
        self.cbb_device_selection.setObjectName(u"cbb_device_selection")
        self.cbb_device_selection.setMinimumSize(QSize(0, 30))

        self.lo_device_selection.addWidget(self.cbb_device_selection)
        self.groupBox = QGroupBox(self.lo_device_selection_2)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")

        # Add Serial Number combobox
        self.txt_serial_number = QLineEdit(self.groupBox)
        self.txt_serial_number.setObjectName(u"txt_serial_number")
        self.formLayout.setWidget(
            0, QFormLayout.FieldRole, self.txt_serial_number)

        self.lb_serial_number = QLabel(self.groupBox)
        self.lb_serial_number.setObjectName(u"serial_number")
        self.formLayout.setWidget(
            0, QFormLayout.LabelRole, self.lb_serial_number)

        self.lb_serial_number_constraint = QLabel(self.groupBox)
        self.lb_serial_number_constraint .setObjectName(
            u"lb_serial_number_constraint")
        self.lb_serial_number_constraint .setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(
            1,
            QFormLayout.FieldRole,
            self.lb_serial_number_constraint)

        # Add Vendor ID
        self.lbl_vendorid = QLabel(self.groupBox)
        self.lbl_vendorid.setObjectName(u"lbl_vendorid")
        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_vendorid)
        self.txt_vendorid = QLineEdit(self.groupBox)
        self.txt_vendorid.setObjectName(u"txt_vendorid")
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.txt_vendorid)

        self.lb_vendor = QLabel(self.groupBox)
        self.lb_vendor.setObjectName(u"lb_vendor")
        self.lb_vendor.setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.lb_vendor)

        # Add Product ID
        self.lbl_productid = QLabel(self.groupBox)
        self.lbl_productid.setObjectName(u"lbl_productid")
        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.lbl_productid)
        self.txt_productid = QLineEdit(self.groupBox)
        self.txt_productid.setObjectName(u"txt_productid")
        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.txt_productid)

        self.lb_product = QLabel(self.groupBox)
        self.lb_product.setObjectName(u"lb_product")
        self.lb_product.setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.lb_product)

        # Add discriminator
        self.txt_discriminator = QLineEdit(self.groupBox)
        self.txt_discriminator.setObjectName(u"txt_discriminator")
        self.formLayout.setWidget(
            6, QFormLayout.FieldRole, self.txt_discriminator)
        self.lbl_discriminator = QLabel(self.groupBox)
        self.lbl_discriminator.setObjectName(u"lbl_discriminator")
        self.formLayout.setWidget(
            6, QFormLayout.LabelRole, self.lbl_discriminator)

        self.lb_dicriminator = QLabel(self.groupBox)
        self.lb_dicriminator.setObjectName(u"lb_dicriminator")
        self.lb_dicriminator.setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(
            7, QFormLayout.FieldRole, self.lb_dicriminator)

        # Add Pin Code
        self.lbl_pincode = QLabel(self.groupBox)
        self.lbl_pincode.setObjectName(u"lbl_pincode")
        self.formLayout.setWidget(8, QFormLayout.LabelRole, self.lbl_pincode)
        self.txt_pincode = QLineEdit(self.groupBox)
        self.txt_pincode.setObjectName(u"txt_pincode")
        self.formLayout.setWidget(8, QFormLayout.FieldRole, self.txt_pincode)

        self.lb_pincode = QLabel(self.groupBox)
        self.lb_pincode.setObjectName(u"lb_pincode")
        self.lb_pincode.setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(9, QFormLayout.FieldRole, self.lb_pincode)

        # Layout
        self.horizontalLayout.addLayout(self.formLayout)

        self.lo_device_selection.addWidget(self.groupBox)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.lo_device_selection.addItem(self.verticalSpacer)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.lo_device_selection.addItem(self.horizontalSpacer)

        self.lo_all.addWidget(self.lo_device_selection_2)

        self.lo_device_control_2 = QGroupBox(self.centralwidget)
        self.lo_device_control_2.setObjectName(u"lo_device_control_2")
        self.lo_device_control = QVBoxLayout(self.lo_device_control_2)
        self.lo_device_control.setObjectName(u"lo_device_control")
        self.btn_start_device = QPushButton(self.lo_device_control_2)
        self.btn_start_device.setObjectName(u"btn_start_device")
        self.btn_start_device.setMinimumSize(QSize(0, 30))
        self.lo_device_control.addWidget(self.btn_start_device)
        self.lbl_qr_image = QLabel(self.lo_device_control_2)
        self.lbl_qr_image.setObjectName(u"lbl_qr_image")
        self.lbl_qr_image.setAlignment(Qt.AlignCenter)
        self.lo_device_control.addWidget(self.lbl_qr_image)
        self.lbl_qr_code = QLabel(self.lo_device_control_2)
        self.lbl_qr_code.setObjectName(u"lbl_qr_code")
        font1 = QFont()
        font1.setFamily(u"Arial")
        font1.setPointSize(12)
        font1.setBold(False)
        font1.setWeight(50)
        self.lbl_qr_code.setFont(font1)
        self.lbl_qr_code.setAlignment(Qt.AlignCenter)
        self.lbl_qr_code.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.TextSelectableByMouse)
        self.lo_device_control.addWidget(self.lbl_qr_code)

        self.lo_controller = QVBoxLayout()
        self.lo_controller.setObjectName(u"lo_controller")
        self.lo_device_control.addLayout(self.lo_controller)
        self.spc_device_control = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.lo_device_control.addItem(self.spc_device_control)
        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.lo_device_control.addItem(self.horizontalSpacer_2)

        self.lo_all.addWidget(self.lo_device_control_2)
        self.verticalLayout.addLayout(self.lo_all)
        self.lbl_status_1 = QLabel(self.centralwidget)
        self.lbl_status_1.setObjectName(u"lbl_status_1")
        font2 = QFont()
        font2.setPointSize(12)
        self.lbl_status_1.setFont(font2)
        self.lbl_status_1.setStyleSheet(u"")
        self.lbl_status_1.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_status_1)
        self.lbl_status_2 = QLabel(self.centralwidget)
        self.lbl_status_2.setObjectName(u"lbl_status_2")
        self.lbl_status_2.setFont(font2)
        self.lbl_status_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_status_2)
        Matter.setCentralWidget(self.centralwidget)
        self.retranslateUi(Matter)
        QMetaObject.connectSlotsByName(Matter)
    # setupUi

    def retranslateUi(self, Matter):
        Matter.setWindowTitle(
            QCoreApplication.translate(
                "Matter", u"MainWindow", None))
        self.lbl_app_name.setText(
            QCoreApplication.translate(
                "Matter", u"Matter IoT Emulator", None))
        self.lo_device_selection_2.setTitle(
            QCoreApplication.translate(
                "Matter", u"Device Type", None))
        self.groupBox.setTitle(
            QCoreApplication.translate(
                "Matter", u"Device Configuration", None))
        self.lb_serial_number.setText(
            QCoreApplication.translate(
                "Matter", u"Serial Number", None))
        self.lbl_vendorid.setText(
            QCoreApplication.translate(
                "Matter", u"Vendor ID", None))
        self.lbl_productid.setText(
            QCoreApplication.translate(
                "Matter", u"Product ID", None))
        self.lbl_pincode.setText(
            QCoreApplication.translate(
                "Matter", u"Pin Code", None))
        self.lbl_discriminator.setText(
            QCoreApplication.translate(
                "Matter", u"Discriminator", None))
        self.lb_vendor.setText(
            QCoreApplication.translate(
                "Matter", u"(65521)", None))
        self.lb_product.setText(
            QCoreApplication.translate(
                "Matter", u"(32768-32867)", None))
        self.lb_dicriminator.setText(
            QCoreApplication.translate(
                "Matter", u"(0-4095)", None))
        self.lb_pincode.setText(
            QCoreApplication.translate(
                "Matter", u"(1-99999998)", None))
        self.lo_device_control_2.setTitle(
            QCoreApplication.translate(
                "Matter", u"Device Control", None))
        self.btn_start_device.setText(
            QCoreApplication.translate(
                "Matter", u"Start Device", None))
        self.lbl_qr_image.setText(
            QCoreApplication.translate(
                "Matter", u"QR image", None))
        self.lbl_qr_code.setText(
            QCoreApplication.translate(
                "Matter", u"QR code", None))
        self.lbl_status_1.setText(
            QCoreApplication.translate(
                "Matter", u"...", None))
        self.lbl_status_2.setText(
            QCoreApplication.translate(
                "Matter", u"...", None))
        self.txt_serial_number.setText(
            QCoreApplication.translate(
                "Matter", u"123456", None))

    # retranslateUi
