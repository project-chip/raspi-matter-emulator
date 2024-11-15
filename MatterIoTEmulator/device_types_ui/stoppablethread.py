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


from threading import Thread


class UpdateStatusThread(Thread):
    """
    Class UpdateStatusThread is a thread is used for updating status of iot matter device
    """

    def __init__(
            self,
            target=None,
            name=None,
            args=(),
            kwargs={},
            daemon=None):
        """
        This function is used for initializing UpdateStatusThread
        """
        Thread.__init__(
            self,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon)
        self.stop_flag = False

    def stop(self):
        """
        This function sets a flag which is used for stopping thread
        """
        self.stop_flag = True

    def run(self):
        """
        This function is used for running task
        """
        self._target(*self._args, **self._kwargs)
