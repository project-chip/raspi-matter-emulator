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
import subprocess
import shlex
import re

# SonNH64
CALL_RPC_NAME = "/pw_rpc/callback_client/call.py"


class TurnOffLogRpc:
    """
    TurnOffLogRpc class definition.
    """

    def __init__(self):
        """
        Initialize a TurnOffLogRpc instance.
        """
        pass

    def turnOffLogRpc(self):
        """
        Turn off the Rpc logging on console screen.

        Raises:
            Exception: if opening or closing log file error
        """
        path = self.getPython3LibPath()
        allContentLines = [""]
        space = "        "
        logInfo = "def _default_completion(self, status: Status) -> None:\n"
        if (len(path) > 1):
            try:
                fileR = open((path + CALL_RPC_NAME), 'r')
                allContentLines = fileR.readlines()
                for i in range(int(len(allContentLines) / 2)):
                    if ((logInfo in allContentLines[i]) & (
                            "pass" not in allContentLines[i + 1]) & ("pass" not in allContentLines[i + 2])):
                        allContentLines[i + 1] = space + \
                            '#' + allContentLines[i + 1]
                        allContentLines.insert((i + 2), space + "pass \n")
                        fileR.close()
                        break
            except Exception as e:
                print("Failed to read call.py file: " + str(e))
        else:
            print("Does not has site-packages of python3")
        try:
            fileW = open((path + CALL_RPC_NAME), 'w')
            for line in allContentLines:
                fileW.write(line)
            fileW.close()
        except Exception as e:
            print("Failed to write call.py file: " + str(e))

    def getPython3LibPath(self):
        """
        Return python3 library path.
        """
        python3Site = "python3 -m site"
        proc = subprocess.Popen(
            python3Site,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        out, err = proc.communicate()
        proc.stdout.close()
        out_utf8 = out.decode('utf-8').strip()
        err_utf8 = err.decode('utf-8').strip()

        if err_utf8 != "":
            print(err_utf8)
        if out_utf8 != "":
            pathSiteRe = re.findall('USER_SITE: \'(.*)\'.*', out_utf8)
            if (len(pathSiteRe) > 0):
                pathSite = str(pathSiteRe[0])
                print("getPython3LibPath: ", pathSite)
                return pathSite
            else:
                print("Can not get path site-packages python3")
        else:
            print("site-packages python3 does not exits")
        return ""


if __name__ == "__main__":
    turnOffLogInstance = TurnOffLogRpc()
    turnOffLogInstance.turnOffLogRpc()
