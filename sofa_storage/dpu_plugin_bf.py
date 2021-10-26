"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import json
import subprocess  # nosec
import re
from itertools import product
from math import copysign
from .config import config
from .log import logger
from .dpu_plugin_interface import DPUInterface

CTRL_SERVER_URL = config['CTRL_SERVER_URL']

NUMBER_OF_PF = 2
NUMBER_OF_VF_PER_PF = 127
DEFAULT_SERIAL_NUMBER = "NVMe_01234"
DEFAULT_MODEL_NUMBER = "NVMe Controller"

MLNX_SNAP_CONFIG_FILE = '/etc/mlnx_snap/mlnx_snap.json'
MLNX_SNAP_RPC_INIT_FILE = '/etc/mlnx_snap/snap_rpc_init.conf'


class DPU(DPUInterface):

    def __init__(self):
        super().__init__()
        self.dpu_type = 'bf'
        self._config = None

    def _readConfig(self):
        with open(MLNX_SNAP_CONFIG_FILE, 'r', encoding='utf-8') as json_file:
            self._config = json.load(json_file)

    def _writeConfig(self):
        if self._config is not None:
            with open(MLNX_SNAP_CONFIG_FILE, 'w', encoding='utf-8') as outfile:
                json.dump(self._config, outfile, indent=4)

    def publishVolume(self, volume_id, volume_context, controller_id, target_path, secrets):  # pylint: disable=R0201
        # sudo snap_rpc.py controller_nvme_create nqn.2020-12.mlnx.snap mlx5_0 --pf_id 0 -c /etc/mlnx_snap/mlnx_snap.json -r mlx5_2
        """
        target_addr = volume_context['addr_traddr']
        target_port = int(volume_context['addr_trsvcid'])
        self._readConfig()
        add_backend = True
        for backend in self._config['backends']:
            for path in backend['paths']:
                if (path['addr'] == target_addr) and (path['port'] == target_port):
                    add_backend = False
        # All checks passed
        if add_backend:
            self._config['backends'].append(
                {
                    'type': 'nvmf_rdma',
                    'name': volume_id,
                    'paths': [{
                        'addr': target_addr,
                        'port': target_port,
                        'hostnqn': 'host1'  # TODO: NQN on host or on target (host)
                    }]
                }
            )

        # self._writeConfig()
        # TODO: Restart mlnx_snap daemon
        """

        # HERE THE RPC CALLS TO SNAP ARE HAPPENING
        cmd_parts = ['spdk_rpc.py', 'bdev_nvme_attach_controller',
                     '-b', volume_id,
                     '-t', config['TRANSPORT_TYPE'],
                     '-a', volume_context['addr_traddr'],
                     '-f', 'ipv4',
                     '-s', volume_context['addr_trsvcid'],
                     '-n', volume_id
                     ]
        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('spdk_rpc.py bdev_nvme_attach_controller failed\n%s\n%s', cmd.stdout, cmd.stderr)

        bdev_name = volume_id + 'n' + config['NAMESPACE']  # FIXME: Needs to be a parameter

        if secrets:
            cmd_parts = ['spdk_rpc.py', 'bdev_crypto_create',
                         bdev_name, bdev_name + '_encrypted',
                         'crypto_armv8', secrets['encryption_key']
                         ]
            cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
            if cmd.returncode != 0:
                logger.error('spdk_rpc.py bdev_crypto_create failed\n%s\n%s', cmd.stdout, cmd.stderr)

            bdev_name += '_encrypted'

        pf_index = int(controller_id[0])
        vf_index = int(controller_id[1:])

        controller = 'NvmeEmu0pf' + str(pf_index)

        if vf_index >= 0:
            controller = controller + 'vf' + str(vf_index)

        match = re.search(r'\d+$', target_path)  # i.e. /dev/nvme0n2  --> 2
        nsid = target_path[match.start():match.end()]
        # was NvmeEmu0pf0
        cmd_parts = ['snap_rpc.py', 'controller_nvme_namespace_attach',
                     '-c', controller,
                     'spdk', bdev_name, nsid
                     ]

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py controller_nvme_namespace_attach failed\n%s\n%s', cmd.stdout, cmd.stderr)

    def unpublishVolume(self, volume_id, target_path):  # pylint: disable=R0201
        # sudo snap_rpc.py controller_nvme_delete -c NvmeEmu0pf0
        """
        target_addr = '10.100.0.24'
        target_port = 4420
        self._readConfig()
        new_backends = []
        for backend in self._config['backends']:
            keep_backend = True
            for path in backend['paths']:
                if (path['addr'] == target_addr) and (path['port'] == target_port):
                    keep_backend = False
            if keep_backend:
                new_backends.append(backend)
        self._config['backends'] = new_backends

        # self._writeConfig()
        # TODO: Restart mlnx_snap daemon
        """
        # HERE THE RPC CALLS TO SNAP ARE HAPPENING
        match = re.search(r'\d+$', target_path)  # i.e. /dev/nvme0n2  --> 2
        nsid = target_path[match.start():match.end()]
        cmd_parts = ['snap_rpc.py', 'controller_nvme_namespace_detach',
                     '-c', 'NvmeEmu0pf0',
                     nsid
                     ]

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py controller_nvme_namespace_detach failed\n%s\n%s', cmd.stdout, cmd.stderr)

        bdev_name = volume_id  # FIXME: Needs to be a parameter
        cmd_parts = ['spdk_rpc.py', 'bdev_nvme_detach_controller',
                     bdev_name
                     ]
        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('spdk_rpc.py bdev_nvme_detach_controller failed\n%s\n%s', cmd.stdout, cmd.stderr)

    def getInfo(self):
        info = {
            'dpu_type': self.dpu_type
        }
        return info

    @staticmethod
    def getAvailableFunctions(pf_index, vf_index):
        cmd_parts = ['snap_rpc.py', 'controller_list']

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py controller_list failed\n%s\n%s', cmd.stdout, cmd.stderr)

        controllers = json.loads(cmd.stdout)

        controller_fs = set()
        all_fs = set()

        pf = vf_index is None  # If there is no VF index provided, then we want PFs
        vf = vf_index is not None or pf_index is None  # If there is a vf_index provided, or nothing is provided, we want VFs

        # If a PF index was not provided, we would accept any PF
        if pf_index is None:
            pf_index = -1

        if vf_index is None:
            vf_index = -1

        pf_indexes = range(max(pf_index, 0), abs(int(min(copysign(NUMBER_OF_PF, pf_index), pf_index + 1))))

        if vf:
            vf_indexes = range(max(vf_index, 0), abs(int(min(copysign(NUMBER_OF_VF_PER_PF, vf_index), vf_index + 1))))
            all_fs.update(product(pf_indexes, vf_indexes))

        if pf:
            all_fs.update(product(pf_indexes, [-1]))

        for controller in controllers:
            digits = list(map(int, re.findall(r'\d+', controller['name'])))

            if len(digits) == 2:
                controller_fs.add((digits[1], -1))  # This is a PF
            elif len(digits) == 3:
                controller_fs.add((digits[1], digits[2]))  # This is a VF

        available_fs = all_fs - controller_fs

        to_return = min(available_fs, default=(-1, -1))
        return to_return[0], to_return[1]

    def createController(self, subsystem_nqn, pf_index, vf_index, serial_number, model_number):
        if not serial_number:
            serial_number = DEFAULT_SERIAL_NUMBER

        if not model_number:
            model_number = DEFAULT_MODEL_NUMBER

        pf_index, vf_index = self.getAvailableFunctions(pf_index, vf_index)

        if pf_index == -1:
            return str(-1)

        cmd_parts = ['snap_rpc.py', 'subsystem_nvme_create',
                     subsystem_nqn,
                     serial_number,
                     model_number
                     ]

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py subsystem_nvme_create failed\n%s\n%s', cmd.stdout, cmd.stderr)

            return str(-1)

        if vf_index == -1:
            cmd_parts = ['snap_rpc.py', 'controller_nvme_create',
                         subsystem_nqn, 'mlx5_0',
                         '--pf_id', str(pf_index),
                         '-c', '/etc/mlnx_snap/mlnx_snap.json'
                         ]
        else:
            cmd_parts = ['snap_rpc.py', 'controller_nvme_create',
                         subsystem_nqn, 'mlx5_0',
                         '--pf_id', str(pf_index),
                         '--vf_id', str(vf_index),
                         '-c', '/etc/mlnx_snap/mlnx_snap.json'
                         ]

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py controller_nvme_create failed\n%s\n%s', cmd.stdout, cmd.stderr)

            return str(-1)

        if vf_index == -1:
            return str(pf_index)

        return str(pf_index) + str(vf_index)

    @staticmethod
    def deleteController(controller_id):
        pf_index = int(controller_id[0])
        controller = 'NvmeEmu0pf' + str(pf_index)

        if len(str(controller_id)) > 1:
            vf_index = int(controller_id[1:])
            controller = controller + 'vf' + str(vf_index)

        cmd_parts = ['snap_rpc.py', 'controller_nvme_delete',
                     '-c', controller
                     ]

        cmd = subprocess.run(cmd_parts, capture_output=True, check=False)  # nosec
        if cmd.returncode != 0:
            logger.error('snap_rpc.py controller_nvme_delete failed\n%s\n%s', cmd.stdout, cmd.stderr)
