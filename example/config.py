"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import sys
import yaml
from .log import logger

CONFIG_FILE_PATH = 'sofa_storage_ctrl.yaml'

config = {}

try:
    with open(CONFIG_FILE_PATH, "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    logger.error('ERROR: Error in configuration file: %s', e)
except FileNotFoundError:
    logger.warning('WARN: No configuration file found: %s', CONFIG_FILE_PATH)

if 'CTRL_SERVER_URL' not in config:
    config['CTRL_SERVER_URL'] = '[::]:50050'

if 'CTRL_SERVER_MAX_WORKERS' not in config:
    config['CTRL_SERVER_MAX_WORKERS'] = 10

if 'VG' not in config:
    logger.fatal('%s needs to contain a parameter "VG"', CONFIG_FILE_PATH)
    sys.exit('Bad config')
