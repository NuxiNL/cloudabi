#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from contextlib import redirect_stdout
import os

from src.abi import *
from src.generators.c import *
from src.parser import *

abi = AbiParser().parse_abi_file(
    os.path.join(os.path.dirname(__file__), 'cloudabi.txt'))

with open('syscalldefs-mi.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLDEFS_MI_H',
            machine_dep=False
        ).generate_abi(abi)

with open('syscalldefs-md.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLDEFS_MD_H',
            machine_dep=True
        ).generate_abi(abi)

with open('syscalldefs-md-32.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi32_'),
            header_guard='CLOUDABI_SYSCALLDEFS_MD_32_H',
            machine_dep=True,
            md_type=int_types['uint32']
        ).generate_abi(abi)

with open('syscalldefs-md-64.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_'),
            header_guard='CLOUDABI_SYSCALLDEFS_MD_64_H',
            machine_dep=True,
            md_type=int_types['uint64']
        ).generate_abi(abi)

with open('syscalls.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_H',
        ).generate_abi(abi)

with open('syscalls-x86_64.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsX86_64Generator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_X86_64_H',
        ).generate_abi(abi)

with open('syscalls-aarch64.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsAarch64Generator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_AARCH64_H',
        ).generate_abi(abi)
