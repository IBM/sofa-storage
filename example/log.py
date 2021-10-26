"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import logging

logger = logging.getLogger('sofa-storage-ctrl-logger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

fh = logging.FileHandler('sofa-storage-ctrl.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
