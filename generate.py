#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

from contextlib import redirect_stdout
import subprocess
import os

from generator.abi import *
from generator.c import *
from generator.markdown import *
from generator.parser import *
from generator.syscalls_master import *

abi = AbiParser().parse_abi_file(
    os.path.join(os.path.dirname(__file__), 'cloudabi.txt'))

with open('headers/cloudabi_types_common.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_TYPES_COMMON_H',
            machine_dep=False,
            preamble='#if defined(__FreeBSD__) && defined(_KERNEL)\n'
                     '#include <sys/stdint.h>\n'
                     '#elif defined(__linux__) && defined(__KERNEL__)\n'
                     '#include <linux/types.h>\n'
                     '#else\n'
                     '#include <stddef.h>\n'
                     '#include <stdint.h>\n'
                     '#endif\n'
        ).generate_abi(abi)

with open('headers/cloudabi_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_TYPES_H',
            machine_dep=True,
            preamble='#include "cloudabi_types_common.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi32_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi32_'),
            header_guard='CLOUDABI32_TYPES_H',
            machine_dep=True,
            md_type=int_types['uint32'],
            preamble='#include "cloudabi_types_common.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi64_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_'),
            header_guard='CLOUDABI64_TYPES_H',
            machine_dep=True,
            md_type=int_types['uint64'],
            preamble='#include "cloudabi_types_common.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi_syscalls_struct.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallStructGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALL_STRUCT_H',
            preamble='#include "cloudabi_types.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi_syscalls.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallWrappersGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_H',
            preamble='#include "cloudabi_syscalls_struct.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi_syscalls_info.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsInfoGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_INFO_H',
        ).generate_abi(abi)

with open('headers/cloudabi_syscalls_native_x86_64.h', 'w') as f:
    with redirect_stdout(f):
        CNativeSyscallsX86_64Generator(
            naming=CNaming('cloudabi_', syscall_prefix='cloudabi_native_sys_'),
            header_guard='CLOUDABI_SYSCALLS_NATIVE_X86_64_H',
            preamble='#include "cloudabi_types.h"\n'
        ).generate_abi(abi)

with open('headers/cloudabi_syscalls_native_aarch64.h', 'w') as f:
    with redirect_stdout(f):
        CNativeSyscallsAarch64Generator(
            naming=CNaming('cloudabi_', syscall_prefix='cloudabi_native_sys_'),
            header_guard='CLOUDABI_SYSCALLS_NATIVE_AARCH64_H',
            preamble='#include "cloudabi_types.h"\n'
        ).generate_abi(abi)

with open('freebsd/syscalls.master', 'w') as f:
    with redirect_stdout(f):
        SyscallsMasterGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_', c11=False),
        ).generate_abi(abi)

with open('linux/cloudabi_syscalls.h', 'w') as f:
    with redirect_stdout(f):
        CLinuxSyscallsGenerator(
            naming=CNaming('cloudabi_', c11=False, pointer_prefix='__user '),
            header_guard='CLOUDABI_SYSCALLS_H',
            machine_dep=False,
            preamble='#include "cloudabi_types_common.h"\n'
        ).generate_abi(abi)

with open('linux/cloudabi64_syscalls.h', 'w') as f:
    with redirect_stdout(f):
        CLinuxSyscallsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_', c11=False,
                           pointer_prefix='__user '),
            header_guard='CLOUDABI64_SYSCALLS_H',
            machine_dep=True,
            preamble='#include "cloudabi64_types.h"\n'
        ).generate_abi(abi)

with open('linux/cloudabi64_syscalls.c', 'w') as f:
    with redirect_stdout(f):
        CLinuxSyscallTableGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_', c11=False,
                           pointer_prefix='__user '),
            md_type=int_types['uint64'],
            preamble='#include <linux/kernel.h>\n'
                     '\n'
                     '#include <asm/byteorder.h>\n'
                     '#include <asm/ptrace.h>\n'
                     '\n'
                     '#include "cloudabi_syscalls.h"\n'
                     '#include "cloudabi64_syscalls.h"\n'
                     '#include "cloudabi64_util.h"\n'
        ).generate_abi(abi)

with open('docs/cloudabi.md', 'w') as f:
    with redirect_stdout(f):
        MarkdownGenerator(
            naming=MarkdownCNaming('cloudabi_'),
        ).generate_abi(abi)

html = subprocess.check_output('markdown docs/cloudabi.md', shell=True)
with open('docs/cloudabi.html', 'wb') as f:
    with open('parts/head.html', 'rb') as p:
        f.write(p.read())
    f.write(html)
    with open('parts/foot.html', 'rb') as p:
        f.write(p.read())
