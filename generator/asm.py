# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .abi import *
from .generator import *


def howmany(a, b):
    return (a + b - 1) // b


def roundup(a, b):
    return howmany(a, b) * b


class AsmVdsoGenerator(Generator):
    def __init__(self, function_alignment, type_character):
        super().__init__(comment_prefix='// ')
        self._function_alignment = function_alignment
        self._type_character = type_character

    def generate_head(self, abi):
        super().generate_head(abi)

        # Macros for opening/closing function bodies.
        print('#define ENTRY(name)      \\')
        print('  .text;                 \\')
        print('  .p2align %-13s \\' % (self._function_alignment + ';'))
        print('  .global name;          \\')
        print('  .type name, %cfunction; \\' % self._type_character)
        print('name:')
        print()
        print('#define END(name) .size name, . - name')

    def generate_syscalls(self, abi, syscalls):
        for s in sorted(abi.syscalls):
            self.generate_syscall(abi, abi.syscalls[s])

    def generate_syscall(self, abi, syscall):
        print()
        print('ENTRY(cloudabi_sys_{})'.format(syscall.name))
        self.generate_syscall_body(abi.syscall_number(syscall),
                                   syscall.input.raw_members,
                                   syscall.output.raw_members,
                                   syscall.noreturn)
        print('END(cloudabi_sys_{})'.format(syscall.name))

    def generate_foot(self, abi):
        super().generate_foot(abi)


class AsmVdsoCommonGenerator(AsmVdsoGenerator):
    def generate_syscall_body(self, number, args_input, args_output, noreturn):
        # Compute the number of registers/stack slots consumed by all of
        # the input and output arguments. We assume that a pointer
        # always fits in a single slot.
        slots_input = 0
        for m in args_input:
            slots_input = (roundup(slots_input, self.register_align(m)) +
                           self.register_count(m))
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
        if regs_output:
            self.print_push_addresses([reg[0] for reg in regs_output])

        # Execute system call.
        self.print_syscall(number)

        if not noreturn:
            if args_output:
                # Pop the output addresses that we previously pushed on
                # the stack into spare registers.
                regs_spare = list(self.REGISTERS_SPARE)
                regs_output_popped = [regs_spare.pop(0) for _ in regs_output]
                if regs_output_popped:
                    self.print_pop_addresses(regs_output_popped)

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

            self.print_return()


class AsmVdsoAarch64Generator(AsmVdsoCommonGenerator):

    REGISTERS_PARAMS = [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'),
                        ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')]
    REGISTERS_RETURNS = ['0', '1']
    REGISTERS_SPARE = ['2', '3']

    def __init__(self):
        super().__init__(function_alignment='2', type_character='@')

    @staticmethod
    def register_align(member):
        return 1

    @staticmethod
    def register_count(member):
        return howmany(member.type.layout.size[1], 8)

    @staticmethod
    def print_push_addresses(regs):
        if len(regs) == 1:
            print('  str x{}, [sp, #-8]'.format(regs[0]))
        else:
            assert len(regs) == 2
            print('  stp x{}, x{}, [sp, #-16]'.format(regs[0], regs[1]))

    @staticmethod
    def print_syscall(number):
        print('  mov w8, #{}'.format(number))
        print('  svc #0')

    @staticmethod
    def print_pop_addresses(regs):
        if len(regs) == 1:
            print('  ldr x{}, [sp, #-8]'.format(regs[0]))
        else:
            assert len(regs) == 2
            print('  ldp x{}, x{}, [sp, #-16]'.format(regs[0], regs[1]))

    @staticmethod
    def print_jump_syscall_failed(label):
        print('  b.cs ' + label)

    @staticmethod
    def print_store_output(member, reg_from, reg_to, index):
        assert index == 0
        size = member.type.layout.size[1]
        print('  str {}{}, [x{}]'.format({
            4: 'w',
            8: 'x'
        }[size], reg_from, reg_to))

    @staticmethod
    def print_retval_success():
        print('  mov w0, wzr')
        print('1:')

    @staticmethod
    def print_return():
        print('  ret')


class AsmVdsoArmv6Generator(AsmVdsoCommonGenerator):

    REGISTERS_PARAMS = [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')]
    REGISTERS_RETURNS = ['0', '1']
    REGISTERS_SPARE = ['2', '3']

    def __init__(self):
        super().__init__(function_alignment='2', type_character='%')

    @staticmethod
    def register_align(member):
        return howmany(member.type.layout.size[0], 4)

    @staticmethod
    def register_count(member):
        return howmany(member.type.layout.size[0], 4)

    @staticmethod
    def print_push_addresses(regs):
        if len(regs) == 1:
            print('  str r{}, [sp, #-4]'.format(regs[0]))
        else:
            assert len(regs) == 2
            print('  str r{}, [sp, #-4]'.format(regs[0]))
            print('  str r{}, [sp, #-8]'.format(regs[1]))

    @staticmethod
    def print_syscall(number):
        print('  mov ip, #{}'.format(number))
        print('  swi 0')

    @staticmethod
    def print_pop_addresses(regs):
        if len(regs) == 1:
            print('  ldrcc r{}, [sp, #-4]'.format(regs[0]))
        else:
            assert len(regs) == 2
            print('  ldrcc r{}, [sp, #-4]'.format(regs[0]))
            print('  ldrcc r{}, [sp, #-8]'.format(regs[1]))

    @staticmethod
    def print_jump_syscall_failed(label):
        pass

    @staticmethod
    def print_load_address_from_stack(slot, reg):
        print('  ldrcc r{}, [sp, #{}]'.format(reg, slot * 4))

    @staticmethod
    def print_store_output(member, reg_from, reg_to, index):
        size = member.type.layout.size[0]
        print('  strcc {}{}, [r{}{}]'.format({
            4: 'r',
            8: 'r'
        }[size], reg_from, reg_to, ', #{}'.format(index *
                                                  4) if size > 4 else ''))

    @staticmethod
    def print_retval_success():
        print('  movcc r0, #0')

    @staticmethod
    def print_return():
        print('  bx lr')


class AsmVdsoArmv6On64bitGenerator(AsmVdsoGenerator):
    def __init__(self):
        super().__init__(function_alignment='2', type_character='%')

    @staticmethod
    def load_argument(offset):
        if offset < 16:
            return 'r{}'.format(offset // 4)
        print('  ldr r1, [sp, #{}]'.format(offset - 16))
        return 'r1'

    def generate_syscall_body(self, number, args_input, args_output, noreturn):
        # When running on 64-bit operating systems, we need to ensure
        # that the system call arguments are padded to 64 bits words, so
        # that they are passed in properly to the system call handler.
        #
        # Determine the number of 64-bit slots we need to allocate on
        # the stack to be able to store both the input and output
        # arguments.
        #
        # TODO(ed): Unify this with AsmVdsoI686On64bitGenerator.
        slots_input_padded = sum(
            howmany(m.type.layout.size[1], 8) for m in args_input)
        slots_stack = max(slots_input_padded, 2)

        # Copy original arguments into a properly padded buffer.
        offset_in = 0
        offset_out = -8 * slots_stack
        r0_is_zero = False
        for member in args_input:
            offset_in = roundup(offset_in, member.type.layout.size[0])
            if member.type.layout.size[0] == member.type.layout.size[1]:
                # Argument whose size doesn't differ between systems.
                for i in range(0, howmany(member.type.layout.size[0], 4)):
                    register = self.load_argument(offset_in + i * 4)
                    print('  str {}, [sp, #{}]'.format(register,
                                                       offset_out + i * 4))
            else:
                # Pointer or size_t. Zero-extend it to 64 bits.
                assert member.type.layout.size[0] == 4
                assert member.type.layout.size[1] == 8
                register = self.load_argument(offset_in)
                print('  str {}, [sp, #{}]'.format(register, offset_out))
                if not r0_is_zero:
                    print('  mov r0, #0')
                    r0_is_zero = True
                print('  str r0, [sp, #{}]'.format(offset_out + 4))
            offset_in += roundup(member.type.layout.size[0], 4)
            offset_out += roundup(member.type.layout.size[1], 8)
        assert offset_out <= 0

        # Store addresses of return values on the stack.
        slots_out = []
        offset_out = -8 * slots_stack
        for i in range(0, len(args_output)):
            reg_from = offset_in // 4 + i
            if reg_from < 4:
                # Move the value to a register that is retained.
                offset_out -= 4
                print('  str r{}, [sp, #{}]'.format(reg_from, offset_out))
                slots_out.append(offset_out)
            else:
                # Value is stored on the stack. No need to preserve.
                slots_out.append((reg_from - 4) * 4)

        # Invoke system call.
        print('  mov r0, #{}'.format(number))
        print('  sub r2, sp, #{}'.format(slots_stack * 8))
        print('  swi 0')

        if not noreturn:
            if args_output:
                # Extract arguments from the padded buffer.
                offset_in = -8 * slots_stack
                for member, slot in zip(args_output, slots_out):
                    size = member.type.layout.size[0]
                    assert (size == member.type.layout.size[1]
                            or (size == 4 and member.type.layout.size[1] == 8))
                    assert size % 4 == 0
                    print('  ldrcc r1, [sp, #{}]'.format(slot))
                    for i in range(0, howmany(size, 4)):
                        print('  ldrcc r2, [sp, #{}]'.format(offset_in +
                                                             i * 4))
                        print('  strcc r2, [r1, #{}]'.format(i * 4))
                    offset_in += roundup(member.type.layout.size[1], 8)
                    offset_out += 4
            print('  bx lr')


class AsmVdsoI686Generator(AsmVdsoCommonGenerator):

    REGISTERS_PARAMS = []
    REGISTERS_RETURNS = ['ax', 'dx']
    REGISTERS_SPARE = ['cx']

    def __init__(self):
        super().__init__(function_alignment='2, 0x90', type_character='@')

    @staticmethod
    def register_align(member):
        return 1

    @staticmethod
    def register_count(member):
        return howmany(member.type.layout.size[0], 4)

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
        print('  mov {}{}, {}(%e{})'.format({
            4: '%e',
            8: '%e'
        }[size], reg_from, index * 4 if size > 4 else '', reg_to))

    @staticmethod
    def print_retval_success():
        print('  xor %eax, %eax')
        print('1:')

    @staticmethod
    def print_return():
        print('  ret')


class AsmVdsoI686On64bitGenerator(AsmVdsoGenerator):
    def __init__(self):
        super().__init__(function_alignment='2, 0x90', type_character='@')

    def generate_syscall_body(self, number, args_input, args_output, noreturn):
        print('  push %ebp')
        print('  mov %esp, %ebp')

        # When running on 64-bit operating systems, we need to ensure
        # that the system call arguments are padded to 64 bits words, so
        # that they are passed in properly to the system call handler.
        #
        # Determine the number of 64-bit slots we need to allocate on
        # the stack to be able to store both the input and output
        # arguments.
        #
        # TODO(ed): Unify this with AsmVdsoArmv6On64bitGenerator.
        slots_input_padded = sum(
            howmany(m.type.layout.size[1], 8) for m in args_input)
        slots_stack = max(slots_input_padded, 2)

        # Copy original arguments into a properly padded buffer.
        offset_in = 8
        offset_out = -8 * slots_stack
        for member in args_input:
            if member.type.layout.size[0] == member.type.layout.size[1]:
                # Argument whose size doesn't differ between systems.
                for i in range(0, howmany(member.type.layout.size[0], 4)):
                    print('  mov {}(%ebp), %ecx'.format(offset_in + i * 4))
                    print('  mov %ecx, {}(%ebp)'.format(offset_out + i * 4))
            else:
                # Pointer or size_t. Zero-extend it to 64 bits.
                assert member.type.layout.size[0] == 4
                assert member.type.layout.size[1] == 8
                print('  mov {}(%ebp), %ecx'.format(offset_in))
                print('  mov %ecx, {}(%ebp)'.format(offset_out))
                print('  movl $0, {}(%ebp)'.format(offset_out + 4))
            offset_in += roundup(member.type.layout.size[0], 4)
            offset_out += roundup(member.type.layout.size[1], 8)
        assert offset_in == 8 + sum(
            roundup(m.type.layout.size[0], 4) for m in args_input)
        assert offset_out <= 0

        # Invoke system call, setting %ecx to the padded buffer.
        print('  mov ${}, %eax'.format(number))
        print('  mov %ebp, %ecx')
        print('  sub ${}, %ecx'.format(slots_stack * 8))
        print('  int $0x80')

        if not noreturn:
            if args_output:
                print('  test %eax, %eax')
                print('  jnz 1f')

                # Extract arguments from the padded buffer.
                offset_in = -8 * slots_stack
                offset_out = 8 + sum(
                    roundup(m.type.layout.size[0], 4) for m in args_input)
                for member in args_output:
                    size = member.type.layout.size[0]
                    assert (size == member.type.layout.size[1]
                            or (size == 4 and member.type.layout.size[1] == 8))
                    assert size % 4 == 0
                    print('  mov {}(%ebp), %ecx'.format(offset_out))
                    for i in range(0, howmany(size, 4)):
                        print('  mov {}(%ebp), %edx'.format(offset_in + i * 4))
                        print('  mov %edx, {}(%ecx)'.format(i * 4))
                    offset_in += roundup(member.type.layout.size[1], 8)
                    offset_out += 4

                print('1:')

            print('  pop %ebp')
            print('  ret')


class AsmVdsoX86_64Generator(AsmVdsoCommonGenerator):

    REGISTERS_PARAMS = [('di', 'di'), ('si', 'si'), ('dx', 'dx'), ('cx', '10'),
                        ('8', '8'), ('9', '9')]
    REGISTERS_RETURNS = ['ax', 'dx']
    REGISTERS_SPARE = ['cx', 'si', 'di', '8', '9', '10', '11']

    def __init__(self):
        super().__init__(function_alignment='4, 0x90', type_character='@')

    @staticmethod
    def register_align(member):
        return 1

    @staticmethod
    def register_count(member):
        return howmany(member.type.layout.size[1], 8)

    @staticmethod
    def print_remap_register(reg_old, reg_new):
        print('  mov %r{}, %r{}'.format(reg_old, reg_new))

    @staticmethod
    def print_push_addresses(regs):
        for reg in regs:
            print('  push %r{}'.format(reg))

    @staticmethod
    def print_syscall(number):
        print('  mov ${}, %eax'.format(number))
        print('  syscall')

    @staticmethod
    def print_pop_addresses(regs):
        for reg in reversed(regs):
            print('  pop %r{}'.format(reg))

    @staticmethod
    def print_jump_syscall_failed(label):
        print('  jc ' + label)

    @staticmethod
    def print_load_address_from_stack(slot, reg):
        print('  mov {}(%rsp), %r{}'.format(slot * 8 + 8, reg))

    @staticmethod
    def print_store_output(member, reg_from, reg_to, index):
        assert index == 0
        size = member.type.layout.size[1]
        print('  mov {}{}, (%r{})'.format({
            4: '%e',
            8: '%r'
        }[size], reg_from, reg_to))

    @staticmethod
    def print_retval_success():
        print('  xor %eax, %eax')
        print('1:')

    @staticmethod
    def print_return():
        print('  ret')
