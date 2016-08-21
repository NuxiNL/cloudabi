# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

from .abi import *
from .generator import *


class AsmNativeSyscallsGenerator(Generator):

    def __init__(self, function_alignment):
        super().__init__(comment_prefix='// ')
        self._function_alignment = function_alignment

    def generate_head(self, abi):
        super().generate_head(abi)

        # Macros for opening/closing function bodies.
        print('#define ENTRY(name)      \\')
        print('  .text;                 \\')
        print('  .p2align %-13s \\' % (self._function_alignment + ';'))
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
        self.generate_syscall_body(
            abi.syscall_number(syscall), syscall.input.raw_members,
            syscall.output.raw_members, syscall.noreturn)
        print('END(cloudabi_sys_{})'.format(syscall.name))

    def generate_foot(self, abi):
        super().generate_foot(abi)


class AsmNativeSyscallsCommonGenerator(AsmNativeSyscallsGenerator):

    def generate_syscall_body(self, number, args_input, args_output, noreturn):
        # Compute the number of registers/stack slots consumed by all of
        # the input and output arguments. We assume that a pointer
        # always fits in a single slot.
        slots_input = sum(self.register_count(m) for m in args_input)
        slots_output = len(args_output)

        # Determine which registers correspond to these slots. If these
        # lists are shorter than the number of slots, the remainder will
        # be assumed to be on the stack.
        regs_input = self.REGISTERS_PARAMS[:slots_input]
        regs_output = self.REGISTERS_PARAMS[slots_input:][:slots_output]

        # Some hardware architectures use different registers for system
        # calls than for function calls (e.g., %rcx -> %r10 on x86-64).
        for reg_old, reg_new in regs_input:
            if reg_old != reg_new:
                self.print_remap_register(reg_old, reg_new)

        # Push the output registers containing the addresses where the
        # values should be stored to the stack. The system call may
        # clobber them.
        for reg in regs_output:
            self.print_push_address(reg[0])

        # Execute system call.
        self.print_syscall(number)

        if not noreturn:
            if args_output:
                # Pop the output addresses that we previously pushed on
                # the stack into spare registers.
                regs_spare = list(self.REGISTERS_SPARE)
                regs_output_popped = []
                for _ in regs_output:
                    reg = regs_spare.pop(0)
                    regs_output_popped.insert(0, reg)
                    self.print_pop_address(reg)

                # No further processing if the system call failed.
                self.print_jump_syscall_failed('1f')

                # Copy return values that are stored in registers to the
                # outputs.
                regs_returns = list(self.REGISTERS_RETURNS)
                reg_tmp = None
                for i, member in enumerate(args_output):
                    if regs_output_popped:
                        # Output address stored in spare register.
                        reg = regs_output_popped.pop(0)
                    else:
                        # Output address stored on the stack. Load it
                        # into a spare register that we reuse across
                        # iteratations.
                        if reg_tmp is None:
                            reg_tmp = regs_spare.pop(0)
                        reg = reg_tmp
                        slot = slots_input - len(self.REGISTERS_PARAMS) + i
                        self.print_load_address_from_stack(slot, reg)

                    # Copy the value from one or more registers.
                    for j in range(0, self.register_count(member)):
                        self.print_store_output(member, regs_returns.pop(0),
                                                reg, j)

                self.print_retval_success()
                print('1:')

            self.print_return()


class AsmNativeSyscallsI686Generator(AsmNativeSyscallsCommonGenerator):

    REGISTERS_PARAMS = []
    REGISTERS_RETURNS = ['ax', 'dx']
    REGISTERS_SPARE = ['cx']

    def __init__(self):
        super().__init__(function_alignment='2, 0x90')

    @staticmethod
    def register_count(member):
        return (member.type.layout.size[0] + 3) // 4

    @staticmethod
    def print_syscall(number):
        print('  mov ${}, %eax'.format(number))
        print('  int $0x80')

    @staticmethod
    def print_jump_syscall_failed(label):
        print('  jc ' + label)

    @staticmethod
    def print_load_address_from_stack(slot, reg):
        print('  mov {}(%esp), %e{}'.format(slot * 4 + 4, reg))

    @staticmethod
    def print_store_output(member, reg_from, reg_to, index):
        size = member.type.layout.size[0]
        print('  mov {}{}, {}(%e{})'.format(
            {4: '%e', 8: '%e'}[size],
            reg_from,
            index * 4 if size > 4 else '',
            reg_to))

    @staticmethod
    def print_retval_success():
        print('  xor %eax, %eax')

    @staticmethod
    def print_return():
        print('  ret')


class AsmNativeSyscallsX86_64Generator(AsmNativeSyscallsCommonGenerator):

    REGISTERS_PARAMS = [('di', 'di'), ('si', 'si'), ('dx', 'dx'),
                        ('cx', '10'), ('8', '8'), ('9', '9')]
    REGISTERS_RETURNS = ['ax', 'dx']
    REGISTERS_SPARE = ['cx', 'si', 'di', '8', '9', '10', '11']

    def __init__(self):
        super().__init__(function_alignment='4, 0x90')

    @staticmethod
    def register_count(member):
        return (member.type.layout.size[1] + 7) // 8

    @staticmethod
    def print_remap_register(reg_old, reg_new):
        print('  mov %r{}, %r{}'.format(reg_old, reg_new))

    @staticmethod
    def print_push_address(reg):
        print('  push %r{}'.format(reg))

    @staticmethod
    def print_syscall(number):
        print('  mov ${}, %eax'.format(number))
        print('  syscall')

    @staticmethod
    def print_pop_address(reg):
        print('  pop %r{}'.format(reg))

    @staticmethod
    def print_jump_syscall_failed(label):
        print('  jc ' + label)

    @staticmethod
    def print_load_address_from_stack(slot, reg):
        print('  mov {}(%rsp), %r{}'.format(slot * 8 + 8, reg))

    @staticmethod
    def print_store_output(member, reg_from, reg_to, index):
        size = member.type.layout.size[1]
        print('  mov {}{}, {}(%r{})'.format(
            {4: '%e', 8: '%r'}[size],
            reg_from,
            index * 8 if size > 8 else '',
            reg_to))

    @staticmethod
    def print_retval_success():
        print('  xor %eax, %eax')

    @staticmethod
    def print_return():
        print('  ret')
