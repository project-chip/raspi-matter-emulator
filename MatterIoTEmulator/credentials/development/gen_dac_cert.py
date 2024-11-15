#!/usr/bin/env python3
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
import sys
import os
import shutil
import logging
import logging.handlers
import configparser
import time
import glob
from constants import CHIP_FACTORY_FILE

# Last Update
SCRIPT_VERSION_INFO = "2024/05/06"

# Log attribute
Log = logging.getLogger("gen-dac-cert")
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = logging.Formatter(
    '[%(asctime)s][PID:%(process)d][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
LOG_MAX_BYTES = 1 * 1024 * 1024
LOG_BACKUP_COUNT = 1
LOG_FILE_NAME = 'gen-dac-cert.log'
LOG_DASH_COUNT = 30

# CONFIG
current_dir = os.getcwd()
vid = "FFF1"
CERT_TOOL_FILE_NAME = "chip-cert-sn"
CHIP_CERT_TOOL = current_dir + "/tool/" + CERT_TOOL_FILE_NAME

# DAC attribute
cert_valid_from = "2022-02-05 00:00:00"
cert_lifetime = 4294967295
pai_key_file = "Matter-Development-PAI-noPID-Key.pem"
pai_cert_file = "Matter-Development-PAI-noPID-Cert.pem"

# DIR, PATH
PAI_SRC_DIR = '/attestation/'
DAC_WORK_DIR = '/dac-temp/'

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
WORK_PATH = CURRENT_SCRIPT_DIR + DAC_WORK_DIR

pai_key_path = CURRENT_SCRIPT_DIR + PAI_SRC_DIR + pai_key_file
pai_cert_path = CURRENT_SCRIPT_DIR + PAI_SRC_DIR + pai_cert_file


class GenDacTool():
    """Class for generating device attestation certificate(DAC) from PAI certificate"""

    def __init__(self, targetid):
        """Create a new `GenDacTool`.
        :param targetid: A target id of device combine between vid, pid and serial number.
        """
        self.targetId = targetid
        self.CHIP_CONFIG_PATH = current_dir + "/temp/" + self.targetId + "/"
        Log.info("GenDacTool  %s", self.CHIP_CONFIG_PATH)

    def delete_path(self, path):
        """
        Use for delete generated DAC folder
        :param path: A path to generated DAC.
        """
        if os.path.exists(path):
            Log.info("Deleting Directory...")
            try:
                shutil.rmtree(path)
            except Exception as e:
                Log.error('Error while deleting directory')

    def add_loghandler(self):
        """Add log handler for print log"""
        log_file_path = os.path.dirname(os.path.realpath(__file__)) + "/"

        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path + LOG_FILE_NAME, maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT, mode="w")
        file_handler.setFormatter(LOG_FORMAT)

        # Console
        # console_handler = logging.StreamHandler()
        # console_handler.setFormatter(LOG_FORMAT)

        Log.setLevel(LOG_LEVEL)
        # Log.addHandler(console_handler)
        Log.addHandler(file_handler)
        Log.propagate = False

        Log.info(
            '%s Start logging %s',
            '-' * LOG_DASH_COUNT,
            '-' * LOG_DASH_COUNT)
        Log.info('Script Version : %s', SCRIPT_VERSION_INFO)
        Log.info('Current Directory : %s', os.getcwd())
        Log.info('Script Path : %s', os.path.abspath(__file__))
        Log.info('Log File Path : %s%s', log_file_path, LOG_FILE_NAME)
        Log.info(
            'Cert-Tool : %s [%s]',
            CERT_TOOL_FILE_NAME,
            time.ctime(
                os.path.getctime(CHIP_CERT_TOOL)))
        # Log.info('PATH : %s', os.environ['PATH'])

    def read_config(self):
        """Read factory config file to get product id and serial number"""
        config_file = self.CHIP_CONFIG_PATH + CHIP_FACTORY_FILE
        Log.info("Read Config File : %s", config_file)

        self.execute_cmd("cat " + config_file)

        try:
            with open(config_file) as file:
                config = configparser.ConfigParser()
                config.read(config_file)
                config.sections()

                try:
                    pid = config['DEFAULT']['product-id']
                    sn = config['DEFAULT']['serial-num']

                    pid_hex = f'{int(pid):x}'
                    Log.info("Get PID : [%s][0x%s]", pid, pid_hex)
                    Log.info("Get SN : [%s]", sn)

                    return pid_hex, sn
                except KeyError as e:
                    Log.error("section [%s] not found in config file", e)
                    sys.exit(1)
        except IOError:
            Log.error("Could not open file.")
            sys.exit(1)

    def execute_cmd(self, cmd):
        """
        Excute shell command
        :param cmd: Shell command need to run
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
            Log.warning(err_utf8)
            sys.exit(1)
        if out_utf8 != "":
            pass
            # Log.info(out_utf8)

    def check_file_isExist(self, path):
        """
        Check file path is exist or not
        :param path: Path file
        :return: True if path exist and inverse
        """
        if os.path.isfile(path):
            return True
        return False

    def generate_DAC(self, pid, sn):
        """
        Generate device attestation certificate operation
        :param pid: Product ID, sn: Serial number
        :return: List of no need to next step(bool), dac key path (path str), dac cert path (path str)
        """
        Log.info("Generating DAC...")

        # WORK_PATH = CURRENT_SCRIPT_DIR + DAC_WORK_DIR
        if os.path.exists(WORK_PATH):
            # Log.info("Directory Exist : %s", WORK_PATH)
            # self.delete_path(WORK_PATH)
            pass
        else:
            os.makedirs(WORK_PATH)

        dac_key_file = "DAC-{}-{}-{}-Key".format(vid, pid, sn)
        dac_cert_file = "DAC-{}-{}-{}-Cert".format(vid, pid, sn)
        dac_key_path = WORK_PATH + dac_key_file
        dac_cert_path = WORK_PATH + dac_cert_file

        no_need_to_next_step = False
        if (self.check_file_isExist("{}.pem".format(dac_cert_path))):
            no_need_to_next_step = True
            return no_need_to_next_step, dac_key_path, dac_cert_path
        # Log.info("pid : %s", pid)
        gen_cmd = CHIP_CERT_TOOL + " gen-att-cert" + " --type d " + \
            " --subject-cn \"Matter Dev DAC 0xFFF1/0x8000\"" + \
            " --subject-vid \"{}\"".format(vid) + \
            " --subject-pid \"{}\"".format(pid) + \
            " --valid-from  \"{}\"".format(cert_valid_from) + \
            " --lifetime    \"{}\"".format(cert_lifetime) + \
            " --ca-key      \"{}\"".format(pai_key_path) + \
            " --ca-cert     \"{}\"".format(pai_cert_path) + \
            " --out-key     \"{}.pem\"".format(dac_key_path) + \
            " --out         \"{}.pem\"".format(dac_cert_path)
        self.execute_cmd(gen_cmd)

        display_cmd = "openssl x509 -noout -text -in " + \
            "{}.pem".format(dac_cert_path)

        self.execute_cmd(display_cmd)

        return no_need_to_next_step, dac_key_path, dac_cert_path

    def convert_DAC(self, dac_cert_path):
        """
        Convert device attestation certificate to .pem and .der file
        :param dac_cert_path: Path to device attestation certificate
        """
        Log.info("Converting DAC...")

        convert_cmd = CHIP_CERT_TOOL + " convert-cert" +  \
            " \"{}.pem\"".format(dac_cert_path) + \
            " \"{}.der\"".format(dac_cert_path) + \
            " --x509-der"

        self.execute_cmd(convert_cmd)

    def generate_txt(self, pid, sn, dac_key_path, dac_cert_path):
        """
        Generate device attestation certificate to .txt file
        :param dac_cert_path: Path to device attestation certificate
        dac_key_path: Path to device attestation certificate key
        """
        Log.info("Generating TXT...")

        dac_cert_txt = WORK_PATH + \
            "kDevelopmentDAC-Cert-{}-{}-{}.txt".format(vid, pid, sn)
        # Log.info("dac_cert : %s", dac_cert_txt)

        dac_cert_cmd = "less -f " + \
            " \"{}.der\"".format(dac_cert_path) + \
            " | od -t x1 -An | sed 's/\\</0x/g' | sed 's/\\>/,/g' | sed 's/^/   /g' >> " +\
            dac_cert_txt

        self.execute_cmd(dac_cert_cmd)

        dac_publickey_txt = WORK_PATH + \
            "kDevelopmentDAC-PublicKey-{}-{}-{}.txt".format(vid, pid, sn)
        # Log.info("dac_publickey : %s", dac_publickey_txt)

        dac_publickey_cmd = "openssl ec -text -noout -in " + \
                            " \"{}.pem\"".format(dac_key_path) + \
                            " 2>/dev/null | sed '/ASN1 OID/d' | sed '/NIST CURVE/d' | sed -n '/pub:/,$p' | sed '/pub:/d' | sed 's/\\([0-9a-fA-F][0-9a-fA-F]\\)/0x\\1/g' | sed 's/:/, /g' >>" + \
                            dac_publickey_txt
        self.execute_cmd(dac_publickey_cmd)

        dac_privatekey_txt = WORK_PATH + \
            "kDevelopmentDAC-PrivateKey-{}-{}-{}.txt".format(vid, pid, sn)
        # Log.info("dac_privatekey : %s", dac_privatekey_txt)

        dac_privatekey_cmd = "openssl ec -text -noout -in " + \
            " \"{}.pem\"".format(dac_key_path) + \
            " 2>/dev/null | sed '/read EC key/d' | sed '/Private-Key/d' | sed '/priv:/d' | sed '/pub:/,$d' | sed 's/\\([0-9a-fA-F][0-9a-fA-F]\\)/0x\\1/g' | sed 's/:/, /g' >> " + \
            dac_privatekey_txt
        self.execute_cmd(dac_privatekey_cmd)

    def display_filelist(self, work_path):
        """
        Display list files in current directory
        :param work_path: Path to current directory of this module
        """
        Log.info(work_path)

        for file_name in sorted(os.listdir(work_path)):
            Log.info(
                "%s : %s",
                file_name,
                os.path.getsize(
                    work_path +
                    file_name))

    def gen_dac_cert(self):
        """Start generating operation device attestation certificate"""
        try:
            # step 1) Log Handler
            # self.add_loghandler()

            # step 2) Read config from KVS
            pid, sn = self.read_config()

            # step 3) Generate DAC
            no_need_to_next_step, dac_key_path, dac_cert_path = self.generate_DAC(
                pid, sn)

            if not no_need_to_next_step:
                # step 4) Convert DAC
                self.convert_DAC(dac_cert_path)

                # step 5) Generate TXT
                self.generate_txt(pid, sn, dac_key_path, dac_cert_path)

                # step 6) Display file list
                self.display_filelist(WORK_PATH)
            # step 7) Result message
            Log.info("The DAC files were successfully created.")
            return True
        except Exception as e:
            Log.error(f"Error occurred when gen DAC files: {str(e)}.")
            return False
