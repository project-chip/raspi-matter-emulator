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
from utils.handle_recover import HandleRecoverDevices
from ipaddress import IPv4Address, IPv6Address
from constants import *
from utils.network_interface_priority import *

INDEX_INCREASE = 1


class CreateIpAddress:
    """
    CreateIpAddress class for handling ip address.
    """

    def __init__(self):
        """
        Initialize a CreateIpAddress instance.
        """
        self.Ipv4Address = ""
        self.Ipv6Address = ""
        self.countV6 = 0
        self.countV4 = 0
        self.listIpv6 = []
        self.rpc_port = 33000
        self.interface = ""
        self.is_base_ip = True
        self.interface_index = 0

    def releaseRpcPort(self, rpc_port):
        """
        Release a port which a process is running on.

        Arguments:
            rpc_port {str} -- the port number
        """
        port = "{}/tcp".format(str(rpc_port))
        subprocess.run(["fuser", "-k", str(port)])

    def generateTargetId(self, vendorID, productID, serialNumber):
        """
        Generate an id of a device and return the result.

        Arguments:
            vendorID {str} -- the vendor id of a device
            productID {str} -- the product id of a device
            serialNumber {str} -- the serial number of a device
        Return:
            targetId {str} -- the targetId of a device
        """
        VID_PID_Str = (hex(vendorID)[2:]) + (hex(productID)[2:])
        serialNumberStr = hex(serialNumber)[2:]
        targetId = VID_PID_Str + '-' + serialNumberStr
        return targetId

    def getIpv4Address(self):
        """
        Return ipv4 address.
        """
        return self.Ipv4Address

    def getIpv6Address(self):
        """
        Return ipv6 address.
        """
        return self.Ipv6Address

    def createAllIp(self, Ipv4, Ipv6):
        """
        Create all ip address of a device.

        Arguments:
            Ipv4 {str} -- the ipv4 address of the device
            Ipv6 {str} -- the ipv6 address of the device
        Raises:
            Exception: if ip address creation failed
        """
        try:
            Ipv4Broadcast = '.'.join(Ipv4.split('.')[:-1] + ["255"])
            Ipv6Broadcast = ':'.join(Ipv6.split(':')[:-1] + ["ffff"])
            self.createIPv4(Ipv4, Ipv4Broadcast)
            self.createIPv6(Ipv6, Ipv6Broadcast)
        except BaseException:
            print('Create ip address failed')

    def check_ipv4_duplicate_with_recoverIp(self, new_createIp):
        """
        Check ip address duplication of a device.

        Arguments:
            new_createIp {str} -- the ipv4 address of the device
        Return:
            True: if ipv4 address is duplicated
            False: if ipv6 address is not duplicated
        """
        if (self.is_base_ip and (
                new_createIp in HandleRecoverDevices.get_list_recover_ipv4())):
            return True
        else:
            return False

    def check_ipv6_duplicate_with_recoverIp(self, new_createIp):
        """
        Check ip address duplication of a device.

        Arguments:
            new_createIp {str} -- the ipv6 address of the device
        Return:
            True: if ipv6 address is duplicated
            False: if ipv6 address is not duplicated
        """
        if (self.is_base_ip and (
                new_createIp in HandleRecoverDevices.get_list_recover_ipv6())):
            return True
        else:
            return False

    def create_indeterface_index(self, index):
        """
        Create the virtual interface index of a device.

        Arguments:
            index {str} -- the virtual interafce index of a device
        Return:
            the virtual interface index of a device
        """
        if (index not in HandleRecoverDevices.list_recover_interface_index):
            return index
        else:
            index = index + 1
            return self.create_indeterface_index(index)

    def createIPv4(self, IpAddress, IpBroadcast):
        """
        Create the ipv4 address the a device.

        Arguments:
            IpAddress {str} -- the ipv4 address of the device
            IpBroadcast {str} -- the ipv4 limit address of the device
        Raises:
            Exception: if ipv4 address creation failed
        Return:
            the ipv4 address the a device
        """
        if self.is_base_ip:
            index = INDEX_INCREASE + self.countV4
        else:
            index = self.countV4
        try:
            ModifyAddress = format(IPv4Address(IpAddress) + index)
            print(
                'createIPv4',
                'ModifyAddress:',
                ModifyAddress,
                'IpBroadcast',
                IpBroadcast)
            # Check if ipv4 address over ip address range
            if (IPv4Address(ModifyAddress) >= IPv4Address(IpBroadcast)):
                self.countV4 = 0
            # Only create Ip when IP is available and not duplicate with Ip of
            # recover devices
            print(f'Not Duplicate: {(not self.check_ipv4_duplicate_with_recoverIp(ModifyAddress))}')
            if ((not self.check_ipv4_duplicate_with_recoverIp(ModifyAddress)) and (
                    self.pingOnlyOne(ModifyAddress))):
                print("FPT--> ipv4 address is available: ", ModifyAddress)
                ModifyAddress.strip()
                self.Ipv4Address = ModifyAddress

                if self.is_base_ip:
                    self.interface_index = self.create_indeterface_index(index)

                print("-----------Interface index: ", self.interface_index)

                self.interface = "{}:{}".format(
                    NETWORK_IF_NAME, str(self.interface_index))
                subprocess.run(
                    ["sudo", "ifconfig", self.interface, "inet", self.Ipv4Address, "up"])
                return ModifyAddress
            else:
                self.countV4 = self.countV4 + INDEX_INCREASE
                return self.createIPv4(IpAddress, IpBroadcast)
        except BaseException:
            ModifyAddress = ""
            self.Ipv4Address = ""
            print('createIPv4', 'Ipv4Address is invalid')
            return ModifyAddress

    def checkDuplicateIp(self, ipaddress):
        for ipv6 in self.listIpv6:
            print(
                "FPT--> checkDuplicateIp",
                ipv6,
                ipaddress,
                ipaddress == ipv6)
            if (ipaddress == ipv6):
                return True
        return False

    def createIPv6(self, IpAddress, IpBroadcast):
        """
        Create the ipv6 address the a device.

        Arguments:
            IpAddress {str} -- the ipv6 address of the device
            IpBroadcast {str} -- the ipv6 limit address of the device
        Raises:
            Exception: if ipv6 address creation failed
        Return:
            the ipv6 address the a device
        """
        if self.is_base_ip:
            index = INDEX_INCREASE + self.countV6
        else:
            index = self.countV6
        try:
            ModifyAddress = format(IPv6Address(IpAddress) + index)
            print(
                'createIPv6',
                'ModifyAddress:',
                ModifyAddress,
                'IpBroadcast',
                IpBroadcast)
            # Check if ipv6 address over ip address range
            if (IPv6Address(ModifyAddress) >= IPv6Address(IpBroadcast)):
                self.countV6 = 0
            # Only create Ip when IP is available and not duplicate with Ip of
            # recover devices
            print(f'Not Duplicate: {(not self.check_ipv6_duplicate_with_recoverIp(ModifyAddress))}')
            if ((not self.check_ipv6_duplicate_with_recoverIp(ModifyAddress)) and (
                    self.pingOnlyOne(ModifyAddress))):
                print("FPT--> ipv6 address is available: ", ModifyAddress)
                self.Ipv6Address = str(ModifyAddress).strip()
                subprocess.run(["sudo", "ifconfig", NETWORK_IF_NAME,
                               "inet6", "add", self.Ipv6Address, "up"])
                return ModifyAddress
            else:
                self.countV6 = self.countV6 + INDEX_INCREASE
                return self.createIPv6(IpAddress, IpBroadcast)
        except BaseException:
            ModifyAddress = ""
            self.Ipv6Address = ""
            print('createIPv6', 'Ipv6Address is invalid')
            return ModifyAddress

    def pingAll(self, IpAddresses):
        """
        Ping all ip address for making sure that they are alive

        Arguments:
            IpAddresses {str} -- list ipv4 and ipv6 address
        Return:
            the ping result ouput
        """
        outputlist = []
        # Iterate over all the servers in the list and ping each server
        for server in IpAddresses:
            cmdStr = f'ping -I {NETWORK_IF_NAME} -c 1 '
            cmdStr = cmdStr + server
            cmd = shlex.split(cmdStr)
            temp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            # get the output as a string
            output = str(temp.communicate())
            # store the output in the list
            outputlist.append(output)
        return outputlist

    def pingOnlyOne(self, IpAddress):
        """
        Ping an ip address for making sure that it is alive

        Arguments:
            IpAddresses {str} -- the ip address
        Return:
            True : if the ip address ping is alive
            False : if the ip address ping is dead
        """
        cmdStr = f'ping -I {NETWORK_IF_NAME} -c 1 '
        outputlist = []
        bytesDatas = []
        # Iterate over all the servers in the list and ping each server
        cmdStr = cmdStr + IpAddress
        cmd = shlex.split(cmdStr)
        temp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # get the output as a string
        output = str(temp.communicate())
        bytesDatas = re.findall('([0-9]{1,3}) bytes from', output)
        isIpAvailable = True
        if ((len(bytesDatas) > 0) and (int(bytesDatas[0]) > 0)):
            isIpAvailable = False
        return isIpAvailable

    def removeIpAfterStopDevice(self):
        """
        Remove an ip address after stopping device
        """
        # remove ipv4
        print(
            f"FPT -->Stop device and Remove ip: {self.interface}-->{self.Ipv6Address} || {self.Ipv4Address}")
        subprocess.run(["sudo", "ip", "addr", "del",
                       self.Ipv4Address, "dev", NETWORK_IF_NAME])
        # remove ipv6
        subprocess.run(["sudo", "ip", "addr", "del",
                       self.Ipv6Address, "dev", NETWORK_IF_NAME])

    def scanAndCreateIp(self, list_ip=[]):
        """
        Check an create ip address for the device

        Arguments:
            list_ip {[str]} -- the list ip address
        Return:
            The ipv4 and ipv6 address of the device
        """
        if len(list_ip) == 2:
            print("recover ip ", list_ip[0], list_ip[1])
            self.createAllIp(list_ip[0], list_ip[1])
            return list_ip
        else:
            cmd = f"ifconfig {NETWORK_IF_NAME}"
            argus = shlex.split(cmd)
            temp = subprocess.Popen(argus, stdout=subprocess.PIPE)
            # get the output as a string
            output = str(temp.communicate())
            outputlist = []

            # getIPv4
            outv4 = re.findall(
                'inet ([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}).*', output)

            # getIPv6
            inet6OutputList = output.split('\\n')
            outv6 = []

            # get list ipv6
            for inet6 in inet6OutputList:
                if ("inet6" in inet6):
                    tempstr = re.findall('inet6 (.*)  prefixlen', inet6)
                    if (len(tempstr) > 0):
                        self.listIpv6.append(tempstr[0])

            for inet6Output in inet6OutputList:
                if (("inet6" in inet6Output) and (
                        "link" in inet6Output) and ("64" in inet6Output)):
                    outv6 = re.findall('inet6 (.*)  prefixlen', inet6Output)

            if ((len(outv6) == 0) and (len(inet6OutputList) >= 1)):
                outv6 = re.findall('inet6 (.*)  prefixlen', inet6OutputList[0])

            if (len(outv4) > 0):
                outputlist.append(outv4[0])
                # self.pingOnlyOne(str(outv4[0]))
            if (len(outv6) > 0):
                outputlist.append(outv6[0])
                # self.pingOnlyOne(str(outv6[0]))
            print("FPT--> Choose base IP: ", outputlist)
            if (len(outputlist) > 1):
                self.createAllIp(outputlist[0], outputlist[1])
            return outputlist
