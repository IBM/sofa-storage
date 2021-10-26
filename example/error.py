"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
from builtins import Exception


class SofaStorageControlExampleException(Exception):
    def __str__(self):
        return 'SOFA Storage Control Example Exception'
