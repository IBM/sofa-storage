"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
from .dpu_plugin_interface import DPUInterface


class DPU(DPUInterface):

    def __init__(self):
        super().__init__()
        self.dpu_type = 'linux'

    def publishVolume(self, volume_id, volume_context, controller_id, target_path, secrets):  # pylint: disable=R0201
        # nvme connect -t rdma -n testnqn -a 172.31.0.202 -s 4420
        print(f'Publish Volume: {volume_id}')
        print(f'Target path: {target_path}')

    def unpublishVolume(self, volume_id, target_path):  # pylint: disable=R0201
        # nvme disconnect -n testnqn
        print(f'Unpublish Volume: {volume_id}')
        print(f'Target path: {target_path}')

    def getInfo(self):
        info = {
            'dpu_type': self.dpu_type
        }
        return info
