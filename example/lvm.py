"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import subprocess  # nosec
from .config import config
from .log import logger
from .error import SofaStorageControlExampleException

VG = config['VG']


def listVolumes():
    volumes = []
    cmd = subprocess.run(['lvs', '-o', 'lv_name,lv_size', '--units', 'B'], capture_output=True, check=False)  # nosec
    if cmd.returncode == 0:
        lines = cmd.stdout.splitlines()
        for line in lines[1:]:
            parts = line.strip().split()
            lv_name = parts[0].decode('utf-8')
            lv_size = int(parts[1][0:-1])
            volumes.append({'lv_name': lv_name, 'lv_size': lv_size})
    else:
        logger.error('Listing volumes failed: %s', cmd.stderr)
        raise SofaStorageControlExampleException
    return volumes


def createVolume(name, size):
    size_str = str(size) + 'B'
    cmd = subprocess.run(['lvcreate', '-L', size_str, '-n', name, VG], capture_output=True, check=False)  # nosec
    if cmd.returncode != 0:
        logger.error('Creating volume failed: %s', cmd.stderr)
        raise SofaStorageControlExampleException


def deleteVolume(name):
    cmd = subprocess.run(['lvremove', '-y', f'/dev/{VG}/{name}'], capture_output=True, check=False)  # nosec
    if cmd.returncode != 0:
        logger.error('Deleting volume failed: %s', cmd.stderr)
        raise SofaStorageControlExampleException


def populateVolume(name, src_name):
    if_path = f'if=/dev/{VG}/{src_name}'
    of_path = f'of=/dev/{VG}/{name}'
    cmd = subprocess.run(['dd', if_path, of_path], capture_output=True, check=False)  # nosec
    if cmd.returncode != 0:
        logger.error('Populating volume failed: %s', cmd.stderr)
        raise SofaStorageControlExampleException
