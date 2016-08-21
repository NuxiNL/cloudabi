# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

from .abi import *
from .generator import *

class AsmNativeSyscallsI686Generator(Generator):

    def __init__(self):
        super().__init__(comment_prefix='// ')

    def generate_head(self, abi):
        super().generate_head(abi)

        # Macros for opening/closing function bodies.
        print('#define ENTRY(name)      \\')
        print('  .text;                 \\')
        print('  .p2align 2, 0x90;      \\')
        print('  .global name;          \\')
        print('  .type name, @function; \\')
        print('name:')
        print()
        print('#define END(name) .size name, . - name')

    def generate_syscalls(self, abi, syscalls):
        for s in sorted(abi.syscalls):
            self.generate_syscall(abi, abi.syscalls[s])

    def generate_syscall(self, abi, syscall):
        print()
        print('ENTRY(cloudabi_sys_{})'.format(syscall.name))

        # Execute system call.
        print('  mov ${}, %eax'.format(abi.syscall_number(syscall)))
        print('  int $0x80')

        if not syscall.noreturn:
            if syscall.output.raw_members:
                # Carry bit set means the system call failed.
                print('  jc 1f')

                # Compute stack offset where function return value
                # pointers are stored.
                offset = 4
                for i in syscall.input.raw_members:
                    offset += (i.type.layout.size[0] + 3) // 4 * 4

                # Store return value.
                print('  mov %d(%%esp), %%ecx' % offset)
                if len(syscall.output.raw_members) > 1:
                    # Two 32-bit return values.
                    print('  mov %eax, (%ecx)')
                    print('  mov %d(%%esp), %%ecx' % (offset + 4))
                    print('  mov %edx, (%ecx)')
                elif syscall.output.raw_members[0].type.layout.size[0] > 4:
                    # Single 64-bit return value, spread out across
                    # multiple registers.
                    print('  mov %eax, 0(%ecx)')
                    print('  mov %edx, 4(%ecx)')
                else:
                    # Single 32-bit return value.
                    print('  mov %eax, (%ecx)')

                print('  xor %eax, %eax')
                print('1:')

            print('  ret')

        print('END(cloudabi_sys_{})'.format(syscall.name))

    def generate_foot(self, abi):
        super().generate_foot(abi)
