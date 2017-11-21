# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .abi import *
from .generator import *


class SyscallsMasterGenerator(Generator):
    def __init__(self, naming):
        super().__init__(comment_prefix='; ')
        self.naming = naming

    def generate_abi(self, abi):
        self.generate_head(abi)
        self.generate_includes(abi)
        self.generate_types(abi, abi.types)
        self.generate_syscalls(abi, abi.syscalls)
        self.generate_foot(abi)

    def generate_head(self, abi):
        print(' $FreeBSD$\n')
        super().generate_head(abi)

    def generate_includes(self, abi):
        print('#include <sys/sysent.h>')
        print('#include <sys/sysproto.h>')
        print()
        print('#include <contrib/cloudabi/cloudabi64_types.h>')
        print()
        print('#include <compat/cloudabi64/cloudabi64_proto.h>')

    def generate_types(self, abi, types):
        pass

    def generate_syscall(self, abi, syscall):
        line_break = ' \\\n\t\t\t\t\t'

        params = [
            line_break + self.naming.vardecl(p.type, p.name)
            for p in syscall.input.raw_members
        ]

        return_type = VoidType()
        if len(syscall.output.raw_members) == 1:
            t = syscall.output.raw_members[0].type
            if not isinstance(t, PointerType):
                return_type = t

        return_type_name = self.naming.typename(return_type)
        print('\n{}\t{}\t{}\t{{ {}{}{}({}); }}'.format(
            abi.syscall_number(syscall), 'AUE_NULL', 'STD', return_type_name,
            ' ' if len(return_type_name) < 16 else line_break,
            self.naming.syscallname(syscall), ','.join(params)))
