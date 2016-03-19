#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from contextlib import redirect_stdout

from src.abi import *
from src.generators.c import *

abi = Abi('cloudabi.txt')

with open('syscalldefs-mi.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            prefix='cloudabi_',
            header_guard='CLOUDABI_SYSCALLDEFS_MI_H',
            machine_dep=False
        ).generate_abi(abi)

with open('syscalldefs-md.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            prefix='cloudabi_',
            header_guard='CLOUDABI_SYSCALLDEFS_MD_H',
            machine_dep=True
        ).generate_abi(abi)

with open('syscalls.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsGenerator(
            prefix='cloudabi_',
            header_guard='CLOUDABI_SYSCALLS_H',
        ).generate_abi(abi)
