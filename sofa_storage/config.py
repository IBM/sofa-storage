"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import yaml
from .log import logger

CONFIG_FILE_PATH = 'sofa_storage.yaml'

config = {}

try:
    with open(CONFIG_FILE_PATH, "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    logger.error('ERROR: Error in configuration file: %s', e)
except FileNotFoundError:
    logger.warning('WARN: No configuration file found: %s', CONFIG_FILE_PATH)

if 'DPU_SERVER_URL' not in config:
    config['DPU_SERVER_URL'] = '[::]:50050'

if 'DPU_SERVER_MAX_WORKERS' not in config:
    config['DPU_SERVER_MAX_WORKERS'] = 10
