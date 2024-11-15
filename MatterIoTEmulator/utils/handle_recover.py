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


import subprocess
import shlex
import re
import sys
import os
import shutil
import configparser
import time
import datetime
from datetime import date
from constants import CHIP_FACTORY_FILE, TEMP_PATH, NUMBER_STORAGE_FILE

SOURCE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CURRENT_TEMP_DIR = SOURCE_PATH + TEMP_PATH


class HandleRecoverDevices():
    """
    HandleRecoverDevices class for handling recover devices.
    """
    list_recover_devices = []
    can_click_start_new_tab = True
    is_click_from_callback = False
    list_recover_ipv6 = []
    list_recover_ipv4 = []
    list_recover_interface_index = []
    list_recover_rpc_port = []
    is_recover = False

    def __init__(self):
        """
        Initialize a HandleRecoverDevices instance.
        """
        if (not (os.path.exists(CURRENT_TEMP_DIR))):
            os.makedirs(CURRENT_TEMP_DIR)

    def create_storage_folder(self, work_dir, folder_name):
        """
        Create a folder for each device when starting.

        Arguments:
            work_dir {str} -- the working directory
            folder_name {str} -- the folder name
        Raise:
            Exception: if the folder creation failed
        Return:
            Absolute path: if a new device created successfully
            "": if a new device creation failed
        """
        path = work_dir + "/temp/" + folder_name
        try:
            if (not os.path.exists(path)):
                cmd = "mkdir -p {}/temp/{}".format(work_dir, folder_name)
                run = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                output = str(run.communicate())
                return path
        except Exception as e:
            print("Can not create storage folder, ", e)
        return ""

    def remove_all_storage_folders(self):
        """
        Remove all storage folder when stopping emulator application.
        """
        for subdir in os.listdir(CURRENT_TEMP_DIR):
            if (os.path.isdir(subdir)):
                path = CURRENT_TEMP_DIR + subdir
                shutil.rmtree(path)
                print("Remove temp folder {}".format(path))

    def remove_storage_folder(self, folder_name):
        """
        Remove all storage folder when stopping emulator application.

        Arguments:
            folder_name {str} -- the working directory of a device
        """
        if (folder_name != ""):
            path = CURRENT_TEMP_DIR + folder_name
            if (os.path.exists(path)):
                shutil.rmtree(path)
                print("Remove temp folder {}".format(path))

    def get_folder_name_from_file_path(self, filepath):
        """
        Return the folder name of a file.

        Arguments:
            filepath {str} -- the absolute file path
        """
        dirname = os.path.basename(os.path.dirname(filepath))
        return dirname

    def get_targetid_device_recover(self):
        """
        Return a list device recover.
        """
        return HandleRecoverDevices.list_recover_devices

    @staticmethod
    def add_recover_devices(targetid):
        """
        Add a device to the recovery list.

        Arguments:
            targetid {str} -- the target id of a device
        """
        if (targetid not in HandleRecoverDevices.list_recover_devices):
            HandleRecoverDevices.list_recover_devices.append(targetid)
            print(
                "add_recover_devices",
                HandleRecoverDevices.list_recover_devices)

    @staticmethod
    def remove_recover_devices(targetid):
        """
        Remove a device from the recovery list.

        Arguments:
            targetid {str} -- the target id of a device
        """
        if (targetid in HandleRecoverDevices.list_recover_devices):
            HandleRecoverDevices.list_recover_devices.remove(targetid)
            print("remove_recover_devices",
                  HandleRecoverDevices.list_recover_devices)

    @staticmethod
    def get_all_storage_folders():
        """
        Return all the devices working directory.

        Raise:
            Exception: if can not get storage path
        """
        path_storage = CURRENT_TEMP_DIR
        try:
            list_dir = os.listdir(path_storage)
        except OSError as err:
            print("Fail to get path of storage folder: {}".format(err))
        dict_dir_time = {}
        for dir in list_dir:
            fullPath = path_storage + str(dir)
            if (not os.path.isdir(fullPath)):
                continue
            tmp_time = HandleRecoverDevices.get_order_created_folder(fullPath)
            create_time = int(tmp_time) if tmp_time is not None else 0
            if (create_time != 0):
                dict_dir_time[str(dir)] = create_time

        list_folder_names = HandleRecoverDevices.sort_all_dirs(dict_dir_time)
        return list_folder_names

    @staticmethod
    def get_order_created_folder(path):
        """
        Return the created time of a folder path.

        Arguments:
            path {str} -- the path folder
        """
        config_file = path + "/" + CHIP_FACTORY_FILE
        dict_config = HandleRecoverDevices.read_config_file(config_file, "")
        if (len(dict_config) == 0):
            return 0
        if (dict_config.get('device-type') != "" and dict_config.get('ipv4') !=
                "" and dict_config.get('ipv6') != "" and dict_config.get('create-time') != ""):
            return dict_config.get('create-time', 0)
        elif (os.path.exists(path)):
            shutil.rmtree(path)
        return 0

    @staticmethod
    def sort_all_dirs(dict_dir_time):
        """
        Return the sorted list directory.

        Arguments:
            dict_dir_time {str} -- the dict of folder with time
        """
        list_folder_names = []
        list_time_value = list(dict_dir_time.values())
        if (len(list_time_value) > 0):
            list_time_value.sort(reverse=False)
            for val in list_time_value:
                key = HandleRecoverDevices.get_key_dic(val, dict_dir_time)
                if ("None" not in key):
                    list_folder_names.append(str(key))
        return list_folder_names

    @staticmethod
    def get_key_dic(val, dict):
        """
        Return the key with value in a dict.

        Arguments:
            val {str} -- the value of a dict
            dict {dict} -- the dict
        Return:
            Key: if the key is found
            "None": if the key is not found
        """
        for key, value in dict.items():
            if val == value:
                return key
        return "None"
    
    @staticmethod
    def remove_storage_folder_lack_file():
        """
        Remove storage folder of device which 
        has lack config file.
        """
        path_storage = CURRENT_TEMP_DIR
        try: 
            list_dir = os.listdir(path_storage)
        except OSError as err:
            print("Fail to get path of storage folder: {}".format(err))    
        for dir in list_dir:
            fullPath = path_storage + str(dir)
            entries = os.listdir(fullPath)
            # Count the files in storage folder
            file_count = sum(os.path.isfile(os.path.join(fullPath, entry)) for entry in entries)
            if((file_count < NUMBER_STORAGE_FILE) and (os.path.exists(fullPath))):
                shutil.rmtree(fullPath)
                print("Remove temp folder {}, reason lack file".format(fullPath)) 

    @staticmethod
    def remove_un_commissioned_storage_folder():
        """
        Remove storage folder of device which 
        has not commissioned yet.
        """
        try:
            HandleRecoverDevices.remove_storage_folder_lack_file()
            HandleRecoverDevices.list_recover_devices = HandleRecoverDevices.get_all_storage_folders()
            for i, subdir in enumerate(HandleRecoverDevices.list_recover_devices):
                path = CURRENT_TEMP_DIR + subdir
                if(os.path.isdir(path)):
                    config_file = path + "/" + CHIP_FACTORY_FILE
                    dict_config = HandleRecoverDevices.read_config_file(config_file, subdir)
                    is_recover = (dict_config.get('is_recover') is not None) and (int(dict_config.get('is_recover')))
                    if(not is_recover):
                        print(f"Remove un-commissioned device: {path}")
                        shutil.rmtree(path)
        except Exception as err:
            print("Fail to remove uncommissioned storage folder: {}".format(err))  


    @staticmethod
    def execute_cmd(cmd):
        """
        Execute the specific command.

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
            print(err_utf8)
            sys.exit(1)
        if out_utf8 != "":
            print(out_utf8)

    @staticmethod
    def check_config_file_has_all_options(config):
        """
        Check the configuration has all option.

        Arguments:
            config {ConfigParser} -- the configpaser object
        Return:
            True: if ConfigParser has all options
            False: if ConfigParser has not all options
        """
        result = config.has_option('DEFAULT', 'product-id') and \
            config.has_option('DEFAULT', 'device-type') and \
            config.has_option('DEFAULT', 'serial-num') and \
            config.has_option('DEFAULT', 'discriminator') and \
            config.has_option('DEFAULT', 'ipv4') and \
            config.has_option('DEFAULT', 'ipv6') and \
            config.has_option('DEFAULT', 'pin-code') and \
            config.has_option('DEFAULT', 'rpc-port') and \
            config.has_option('DEFAULT', 'vendor-id')
        return result

    @staticmethod
    def get_is_click_from_callback():
        """
        Check a flag for user clicked from callback.

        Return:
            True: if the user clicked
            False: if the user did not click
        """
        return HandleRecoverDevices.is_click_from_callback

    @staticmethod
    def set_is_click_from_callback(value):
        """
        Set a flag for user clicked from callback.

        Arguments:
            value {boolean} -- the flag
        """
        HandleRecoverDevices.is_click_from_callback = value

    @staticmethod
    def check_recover():
        """
        Check is recover situation or not.

        Return:
            True: if is recover situation
            False: if is not recover situation
        """
        return HandleRecoverDevices.is_recover

    @staticmethod
    def get_list_recover_ipv4():
        """
        Return the recover list ipv4 address.
        """
        return HandleRecoverDevices.list_recover_ipv4

    @staticmethod
    def get_list_recover_ipv6():
        """
        Return the recover list ipv6 address.
        """
        return HandleRecoverDevices.list_recover_ipv6

    @staticmethod
    def read_config_file(config_file, targetid):
        """
        Read the config information of a specific targetid of a device.

        Arguments:
            config_file {str} -- the configuration file
            targetid {str} -- the configuration file
        Raise:
            Exception: if config_file can not be opened
        Return:
            A dictionary includes configuration information
        """
        dict_config = {}
        try:
            # read chip_factory of each device from folder temp/targetid/
            with open(config_file) as file:
                HandleRecoverDevices.can_click_start_new_tab = False
                config = configparser.ConfigParser()
                config.read(config_file)
                config.sections()
                if (not HandleRecoverDevices.check_config_file_has_all_options(config)):
                    if (targetid in HandleRecoverDevices.list_recover_devices):
                        HandleRecoverDevices.list_recover_devices.remove(
                            targetid)
                    path = os.path.dirname(config_file)
                    shutil.rmtree(path)
                    return dict_config
                try:
                    dict_config['product-id'] = config.get(
                        'DEFAULT', 'product-id')
                    dict_config['serial-num'] = config.get(
                        'DEFAULT', 'serial-num')
                    dict_config['device-type'] = config.get(
                        'DEFAULT', 'device-type')
                    dict_config['discriminator'] = config.get(
                        'DEFAULT', 'discriminator')
                    dict_config['ipv4'] = config.get('DEFAULT', 'ipv4')
                    dict_config['ipv6'] = config.get('DEFAULT', 'ipv6')
                    dict_config['pin-code'] = config.get('DEFAULT', 'pin-code')
                    dict_config['rpc-port'] = config.get('DEFAULT', 'rpc-port')
                    dict_config['vendor-id'] = config.get(
                        'DEFAULT', 'vendor-id')
                    dict_config['interface_index'] = config.get(
                        'DEFAULT', 'interface_index')
                    dict_config['create-time'] = config.get(
                        'DEFAULT', 'create-time')
                    dict_config['is_recover'] = config.get(
                        'DEFAULT', 'is_recover')
                    dict_config['unique-id'] = config.get(
                        'DEFAULT', 'unique-id')
                    HandleRecoverDevices.can_click_start_new_tab = True
                    return dict_config

                except KeyError as e:
                    print("section [%s] not found in config file", e)
                    sys.exit(1)
        except IOError:
            print("Could not open file.")
            sys.exit(1)

    @staticmethod
    def handle_recover_devices(add_new_tab_callback, list_tab):
        """
        Handle recover devices.

        Arguments:
            add_new_tab_callback {str} -- the addNewTab callback function
            list_tab {str} -- the list tab on emulator
        Raise:
            Exception: if the application can not recover devices
        Return:
            A dictionary includes configuration information
        """
        HandleRecoverDevices.list_recover_ipv4.clear()
        HandleRecoverDevices.list_recover_ipv6.clear()
        HandleRecoverDevices.list_recover_devices.clear()
        HandleRecoverDevices.list_recover_interface_index.clear()
        HandleRecoverDevices.list_recover_rpc_port.clear()
        try:
            HandleRecoverDevices.list_recover_devices = HandleRecoverDevices.get_all_storage_folders()
            if (len(HandleRecoverDevices.list_recover_devices) > 0):
                HandleRecoverDevices.is_recover = True
            else:
                HandleRecoverDevices.is_recover = False

            for i, subdir in enumerate(
                    HandleRecoverDevices.list_recover_devices):
                path = CURRENT_TEMP_DIR + subdir + "/"
                if (os.path.isdir(path)):
                    # list_recover_devices.append(subdir)
                    config_file = path + CHIP_FACTORY_FILE
                    # HandleRecoverDevices.execute_cmd("cat " + config_file)
                    dict_config = HandleRecoverDevices.read_config_file(
                        config_file, subdir)
                    if ((len(dict_config) != 0) and dict_config.get(
                            'ipv4') != "" and dict_config.get('ipv6') != ""):
                        HandleRecoverDevices.list_recover_ipv4.append(
                            dict_config.get('ipv4'))
                        HandleRecoverDevices.list_recover_ipv6.append(
                            dict_config.get('ipv6'))
                        list_tab[i].ipv4 = dict_config.get('ipv4')
                        list_tab[i].ipv6 = dict_config.get('ipv6')

                    # handle recover
                    list_tab[i].ui.cbb_device_selection.setCurrentText(
                        dict_config.get('device-type'))
                    list_tab[i].ui.txt_serial_number.setText(
                        dict_config.get('serial-num'))
                    list_tab[i].ui.txt_vendorid.setText(
                        dict_config.get('vendor-id'))
                    list_tab[i].ui.txt_productid.setText(
                        dict_config.get('product-id'))
                    list_tab[i].ui.txt_discriminator.setText(
                        dict_config.get('discriminator'))
                    list_tab[i].ui.txt_pincode.setText(
                        dict_config.get('pin-code'))
                    list_tab[i].rpcPort = int(dict_config.get('rpc-port'))
                    if (int(dict_config.get('rpc-port'))
                            not in HandleRecoverDevices.list_recover_rpc_port):
                        HandleRecoverDevices.list_recover_rpc_port.append(
                            int(dict_config.get('rpc-port')))
                    list_tab[i].is_recover = int(dict_config.get('is_recover'))
                    list_tab[i].unique_id = dict_config.get('unique-id')
                    list_tab[i].create_time = dict_config.get('create-time')
                    list_tab[i].interface_index = dict_config.get(
                        'interface_index')
                    if (int(dict_config.get('interface_index'))
                            not in HandleRecoverDevices.list_recover_interface_index):
                        HandleRecoverDevices.list_recover_interface_index.append(
                            int(dict_config.get('interface_index')))

                    HandleRecoverDevices.is_click_from_callback = True
                    list_tab[i].on_click_start_device()

                    if (len(HandleRecoverDevices.list_recover_devices) > i + 1):
                        add_new_tab_callback()

        except Exception as e:
            print("Can not get recover device: ", str(e))

    @staticmethod
    def get_recover_device_when_add_tab(targetid, device_instance):
        """
        Handle recover device when adding new tab.

        Arguments:
            targetid {str} -- the addNewTab callback function
            device_instance {Object} -- the instance of a device
        Raise:
            Exception: if the application can not recover devices
        Return:
            True: if the recovery success
            False: if the recovery failed
        """
        HandleRecoverDevices.list_recover_devices.clear()
        try:
            HandleRecoverDevices.list_recover_devices = HandleRecoverDevices.get_all_storage_folders()
            print("list: ", HandleRecoverDevices.list_recover_devices, targetid)
            if (targetid in HandleRecoverDevices.list_recover_devices):
                path = CURRENT_TEMP_DIR + targetid + "/"
                if (os.path.isdir(path)):
                    config_file = path + CHIP_FACTORY_FILE
                    print("Read Config File : %s", config_file)
                    dict_config = HandleRecoverDevices.read_config_file(
                        config_file, targetid)
                    if ((len(dict_config) != 0) and dict_config.get(
                            'ipv4') != "" and dict_config.get('ipv6') != ""):
                        device_instance.ipv4 = dict_config.get('ipv4')
                        device_instance.ipv6 = dict_config.get('ipv6')
                    else:
                        return False
                    # handle recover
                    device_instance.rpcPort = int(dict_config.get('rpc-port'))
                    device_instance.interface_index = dict_config.get(
                        'interface_index')
                    device_instance.is_recover = dict_config.get('is_recover')
                    device_instance.unique_id = dict_config.get('unique-id')
                    device_instance.create_time = dict_config.get(
                        'create-time')
        except Exception as e:
            print("Can not get recover device: ", str(e))
            return False
        return True

    @staticmethod
    def handle_start_devices(tab):
        """
        Handle start device.

        Arguments:
            tab {Object} -- the Tab instance
        Raise:
            Exception: if the application can not recover devices
        Return:
            True: if the device starting successed
            False: if the device starting failed
        """
        if (tab.generateTargetId(
        ) in HandleRecoverDevices.list_recover_devices and HandleRecoverDevices.can_click_start_new_tab):
            HandleRecoverDevices.is_click_from_callback = True
            tab.on_click_start_device()
            return True
        return False
