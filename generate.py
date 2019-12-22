#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from contextlib import redirect_stdout
import io
import os
import subprocess

from generator.abi import *
from generator.asm import *
from generator.c import *
from generator.markdown import *
from generator.parser import *
from generator.rust import *
from generator.syscalls_master import *

abi = AbiParser().parse_abi_file(
    os.path.join(os.path.dirname(__file__), 'cloudabi.txt'))

procs = []


# Pipes output through clang-format to format the C code.
def open_and_format(filename):
    proc = subprocess.Popen([
        'clang-format', '''-style={
               BasedOnStyle: Google,
               AllowShortIfStatementsOnASingleLine: false,
               AllowShortLoopsOnASingleLine: false,
               AllowShortFunctionsOnASingleLine: None,
               DerivePointerBinding: false,
               PointerAlignment: Right,
         }'''
    ],
                            stdin=subprocess.PIPE,
                            stdout=open(filename, 'w'))
    procs.append(proc)
    return io.TextIOWrapper(proc.stdin, encoding='UTF-8')


with open('headers/cloudabi_types_common.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_TYPES_COMMON_H',
            machine_dep=False,
            preamble='#if defined(__FreeBSD__) && defined(_KERNEL)\n'
            '#include <sys/types.h>\n'
            '#elif defined(__linux__) && defined(__KERNEL__)\n'
            '#include <linux/types.h>\n'
            '#else\n'
            '#include <stddef.h>\n'
            '#include <stdint.h>\n'
            '#endif\n'
            '\n'
            '// Make this code build with g++.\n'
            '#if defined(__cplusplus) && defined(__GNUC__) && !defined(__clang__)\n'
            '#define _Alignas alignas\n'
            '#define _Alignof alignof\n'
            '#define _Atomic(x) x\n'
            '#define _Static_assert static_assert\n'
            '#endif\n').generate_abi(abi)

with open('headers/cloudabi_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_TYPES_H',
            machine_dep=True,
            preamble='#include "cloudabi_types_common.h"\n').generate_abi(abi)

with open('headers/cloudabi32_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi32_'),
            header_guard='CLOUDABI32_TYPES_H',
            machine_dep=True,
            md_type=int_types['uint32'],
            preamble='#include "cloudabi_types_common.h"\n').generate_abi(abi)

with open('headers/cloudabi64_types.h', 'w') as f:
    with redirect_stdout(f):
        CSyscalldefsGenerator(
            naming=CNaming('cloudabi_', 'cloudabi64_'),
            header_guard='CLOUDABI64_TYPES_H',
            machine_dep=True,
            md_type=int_types['uint64'],
            preamble='#include "cloudabi_types_common.h"\n').generate_abi(abi)

with open_and_format('headers/cloudabi_syscalls.h') as f:
    with redirect_stdout(f):
        CSyscallsGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_H',
            preamble='#include "cloudabi_types.h"\n').generate_abi(abi)

with open('headers/cloudabi_syscalls_info.h', 'w') as f:
    with redirect_stdout(f):
        CSyscallsInfoGenerator(
            naming=CNaming('cloudabi_'),
            header_guard='CLOUDABI_SYSCALLS_INFO_H',
        ).generate_abi(abi)

with open('rust/cloudabi.rs', 'w') as f:
    with redirect_stdout(f):
        RustGenerator(naming=RustNaming()).generate_abi(abi)

with open('vdsos/cloudabi_vdso_aarch64.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoAarch64Generator().generate_abi(abi)

with open('vdsos/cloudabi_vdso_armv6.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoArmv6Generator().generate_abi(abi)

with open('vdsos/cloudabi_vdso_armv6_on_64bit.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoArmv6On64bitGenerator().generate_abi(abi)

with open('vdsos/cloudabi_vdso_i686.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoI686Generator().generate_abi(abi)

with open('vdsos/cloudabi_vdso_i686_on_64bit.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoI686On64bitGenerator().generate_abi(abi)

with open('vdsos/cloudabi_vdso_x86_64.S', 'w') as f:
    with redirect_stdout(f):
        AsmVdsoX86_64Generator().generate_abi(abi)

with open('freebsd/syscalls32.master', 'w') as f:
    with redirect_stdout(f):
        SyscallsMasterGenerator(naming=CNaming('cloudabi_',
                                               'cloudabi32_',
                                               c11=False), ).generate_abi(abi)

with open('freebsd/syscalls64.master', 'w') as f:
    with redirect_stdout(f):
        SyscallsMasterGenerator(naming=CNaming('cloudabi_',
                                               'cloudabi64_',
                                               c11=False), ).generate_abi(abi)

with open_and_format('linux/cloudabi_syscalls.h') as f:
    with redirect_stdout(f):
        CLinuxSyscallsGenerator(
            naming=CNaming('cloudabi_', c11=False, pointer_prefix='__user '),
            header_guard='CLOUDABI_SYSCALLS_H',
            machine_dep=False,
            preamble='#include "cloudabi_types_common.h"\n').generate_abi(abi)

with open_and_format('linux/cloudabi64_syscalls.h') as f:
    with redirect_stdout(f):
        CLinuxSyscallsGenerator(
            naming=CNaming('cloudabi_',
                           'cloudabi64_',
                           c11=False,
                           pointer_prefix='__user '),
            header_guard='CLOUDABI64_SYSCALLS_H',
            machine_dep=True,
            preamble='#include "cloudabi64_types.h"\n').generate_abi(abi)

with open_and_format('linux/cloudabi64_syscalls_table.h') as f:
    with redirect_stdout(f):
        CLinuxSyscallTableGenerator(
            naming=CNaming('cloudabi_',
                           'cloudabi64_',
                           c11=False,
                           pointer_prefix='__user '),
            md_type=int_types['uint64'],
            preamble='#include <asm/byteorder.h>\n'
            '\n'
            '#include "cloudabi_syscalls.h"\n'
            '#include "cloudabi64_syscalls.h"\n').generate_abi(abi)

with open('docs/cloudabi.md', 'w') as f:
    with redirect_stdout(f):
        MarkdownGenerator(
            naming=MarkdownCNaming('cloudabi_'), ).generate_abi(abi)

with open('docs/cloudabi-rust.md', 'w') as f:
    with redirect_stdout(f):
        MarkdownGenerator(naming=MarkdownRustNaming(), ).generate_abi(abi)

html = subprocess.check_output('markdown docs/cloudabi.md', shell=True)
with open('docs/cloudabi.html', 'wb') as f:
    with open('parts/head.html', 'rb') as p:
        f.write(p.read())
    f.write(html)
    with open('parts/foot.html', 'rb') as p:
        f.write(p.read())

html = subprocess.check_output('markdown docs/cloudabi-rust.md', shell=True)
with open('docs/cloudabi-rust.html', 'wb') as f:
    with open('parts/head.html', 'rb') as p:
        f.write(p.read())
    f.write(html)
    with open('parts/foot.html', 'rb') as p:
        f.write(p.read())

for proc in procs:
    proc.wait()
