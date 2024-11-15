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


import os
import signal
import subprocess
import time
from threading import Thread


class DeviceRunner:
    """
    DeviceRunner client class for creating a device.
    """

    def __init__(self, cmd) -> None:
        """
        Initialize a DeviceRunner instance.

        Arguments:
            cmd {str} -- the command string
        """
        self._cmd = cmd
        self._process = None

    def get_process(self):
        """
        Return the current process executing the string command.
        """
        return self._process

    def execute(self):
        """
        Execute the string command.
        """
        self._process = subprocess.Popen(
            self._cmd,
            stdout=subprocess.PIPE,
            shell=True,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid)

    def get_log(self):
        """
        Return the output string after executing the string command.
        """
        for line in self._process.stdout:
            try:
                yield line.decode('utf-8').strip()
            except BaseException:
                pass

    def stop(self, is_qr_process=False):
        """
        Stop the process executing the string command.

        Arguments:
            is_qr_process {boolean} -- check if qr process
        Raises:
            Exception: if there is an error while killing the current process
        """
        try:
            process_id = self._process.pid
            is_process_existed = self.is_process(process_id)
            if is_process_existed:
                os.killpg(os.getpgid(process_id), signal.SIGTERM)
                os.waitpid(process_id, 0)
                print("--> Killed process: " + str(process_id))

        except Exception as e:
            print("Error when killing process:" + str(e))

    def run_cmd(self, cmd):
        """
        Return the result after executing the string command.

        Arguments:
            cmd {str} -- the string command
        """
        self._process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        err, out = self._process.communicate()
        out_utf8 = out.decode('utf-8').strip()
        err_utf8 = err.decode('utf-8').strip()
        return out_utf8, err_utf8

    def generate_dac(self, path_cmd):
        """
        Generate the DAC file after executing the string command
        and return the result.

        Arguments:
            path_cmd {str} -- the string command
        Return:
            True -- if DAC files were successfully created
            False -- if DAC files were not created
        """
        out, err = self.run_cmd("python3 " + path_cmd)
        if "The DAC files were successfully created" in out:
            return True
        else:
            return False

    def is_process(self, pid):
        """
        Return the status of the process.

        Arguments:
            pid {str} -- the process id
        Return:
            True -- if the process has pid is running
            False -- if the process has pid is not running
        """
        if os.path.exists(f"/proc/{pid}"):
            # print(f"Process with PID {pid} exists.")
            return True
        else:
            # print(f"Process with PID {pid} does not exist.")
            return False

    def delete_chip_factory_file(self, cmd="rm -rf /tmp/chip_*"):
        """
        Delete the chip_* file inside /id-app-folder/tmp folder.

        Arguments:
            cmd {str} -- the string command (default = "rm -rf /tmp/chip_*")
        """
        out, err = self.run_cmd(cmd)
        if err != "":
            print("[ERR] : " + err)
        if out != "":
            print("[OUT] : " + out)

    # Handle factory config file
    def update_SN_config_file(
            self,
            file_path,
            serial_value,
            product_id_value,
            discriminator,
            pin_code,
            device_type,
            create_time,
            ipv4="",
            ipv6="",
            rpc_port="",
            interface_index="",
            is_recover="",
            vendor_id="",
            unique_id=""):
        """
        Update the device informations to config file.

        Arguments:
            file_path {str} -- the config file path
            serial_value {str} -- the serial number of device
            product_id_value {str} -- thge product id of device
            discriminator {str} -- the discriminator of device
            pin_code {str} -- the pin code of device
            device_type {str} -- the type of device
            create_time {str} -- the created time of device
            ipv4 {str} -- the ipv4 address of device (default = "")
            ipv6 {str} -- the ipv6 address of device (default = "")
            rpc_port {str} -- the rpc port of device (default = "")
            interface_index {str} -- the vritual interface index of device (default = "")
            is_recover {str} -- flag marked a new created or recover device
            vendor_id {str} -- the vendor id of device (default = "")
            unique_id {str} -- the unique id of device (default = "")
        Raises:
            Exception: if there is an error while writing to config file
        """
        try:
            with open(file_path, 'w') as file:
                line_1 = "[DEFAULT]\n"
                line_2 = "product-id=" + str(product_id_value)
                line_3 = "\nserial-num=" + str(serial_value)
                line_4 = "\ndiscriminator=" + str(discriminator)
                line_5 = "\npin-code=" + str(pin_code)
                line_6 = "\ndevice-type=" + str(device_type)
                line_7 = "\ncreate-time=" + str(create_time)
                line_8 = "\nipv4=" + str(ipv4)
                line_9 = "\nipv6=" + str(ipv6)
                line_10 = "\nrpc-port=" + str(rpc_port)
                line_11 = "\ninterface_index=" + str(interface_index)
                line_12 = "\nis_recover=" + str(is_recover)
                line_13 = "\nvendor-id=" + str(vendor_id)
                if (not unique_id):
                    file.writelines([line_1,
                                     line_2,
                                     line_3,
                                     line_4,
                                     line_5,
                                     line_6,
                                     line_7,
                                     line_8,
                                     line_9,
                                     line_10,
                                     line_11,
                                     line_12,
                                     line_13])
                    file.close()
                    return
                line_14 = "\nunique-id=" + str(unique_id)
                file.writelines([line_1,
                                 line_2,
                                 line_3,
                                 line_4,
                                 line_5,
                                 line_6,
                                 line_7,
                                 line_8,
                                 line_9,
                                 line_10,
                                 line_11,
                                 line_12,
                                 line_13,
                                 line_14])
                file.close()
        except Exception as e:
            print("Failed to create SN config file: error-->" + str(e))
