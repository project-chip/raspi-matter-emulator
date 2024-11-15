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


import psutil
import sys
import os

WIFI_INTERFACE = "wlan0"
ETHERNET_INTERFACE = "eth0"


def check_interface_up(interface_check):
    """
    Check an interface is on up state.

    Arguments:
        interface_check {str} -- the interface name
    Return:
        True: if the interface is on up state
        False: if the interface is on down state
    """
    # Get network interfaces and their statuses
    network_interfaces = psutil.net_if_stats()
    list_if_name = network_interfaces.items()
    for interface, stats in list_if_name:
        if (interface_check == interface):
            print(f"Interface: {interface}, isUp: {stats.isup}")
            os.environ['NETWORK_IF_NAME'] = interface
            return stats.isup
    return False


def get_network_interface():
    """
    Return the network interface.
    """
    # Ethernet has priority higher than wifi
    try:
        if (check_interface_up(ETHERNET_INTERFACE)):
            return ETHERNET_INTERFACE

        if (check_interface_up(WIFI_INTERFACE)):
            return WIFI_INTERFACE
    except Exception as e:
        print("Can not get interface ", str(e))
        return ETHERNET_INTERFACE
    print("Network Down")
    sys.exit()


NETWORK_IF_NAME = get_network_interface()
