#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from src.abi import *

abi = Abi('cloudabi.txt')

print('Got {} types and {} syscalls.'.format(
    len(abi.types), len(abi.syscalls_by_number)))

# TODO: Do something with the abi.
