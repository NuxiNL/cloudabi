#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from contextlib import redirect_stdout
import os

from src.abi import *
from src.generators.c import *
from src.generators.syscalls_master import *
from src.parser import *

abi = AbiParser().parse_abi_file(
    os.path.join(os.path.dirname(__file__), 'cloudabi.txt'))

with open('syscalls.master', 'w') as f:
    with redirect_stdout(f):
        SyscallsMasterGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_', c11=False),
        ).generate_abi(abi)
