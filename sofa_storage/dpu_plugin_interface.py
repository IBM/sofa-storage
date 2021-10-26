"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""


class DPUInterface():

    def __init__(self):
        self.dpu_type = None

    def publishVolume(self, volume_id, volume_context, controller_id, target_path, secrets):  # pylint: disable=R0201
        pass

    def unpublishVolume(self, volume_id, target_path):  # pylint: disable=R0201
        pass

    def getInfo(self):
        pass
