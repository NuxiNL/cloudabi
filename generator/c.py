# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

from .abi import *
from .generator import *


class CNaming:

    def __init__(self, prefix, md_prefix=None, c11=True, syscall_prefix=None, pointer_prefix='', function_keywords=''):
        self.prefix = prefix
        self.md_prefix = md_prefix
        self.c11 = c11
        self.syscall_prefix = syscall_prefix
        self.pointer_prefix = pointer_prefix
        self.function_keywords = function_keywords

    def typename(self, type):
        if isinstance(type, VoidType):
            return 'void'
        elif isinstance(type, IntType):
            if type.name == 'char':
                return 'char'
            return '{}_t'.format(type.name)
        elif isinstance(type, UserDefinedType):
            prefix = self.prefix
            if self.md_prefix is not None and type.layout.machine_dep:
                prefix = self.md_prefix
            return '{}{}_t'.format(prefix, type.name)
        elif isinstance(type, AtomicType):
            if self.c11:
                return '_Atomic({})'.format(
                    self.typename(type.target_type))
            else:
                return self.typename(type.target_type)
        elif isinstance(type, PointerType) or isinstance(type, ArrayType):
            return self.vardecl(type, '')
        else:
            raise Exception('Unable to generate C declaration '
                            'for type: {}'.format(type))

    def valname(self, type, value):
        return '{}{}{}'.format(self.prefix, type.cprefix, value.name).upper()

    def syscallname(self, syscall):
        if self.syscall_prefix is not None:
            prefix = self.syscall_prefix
        else:
            prefix = self.prefix
            if self.md_prefix is not None and syscall.machine_dep:
                prefix = self.md_prefix
            prefix += 'sys_'
        return '{}{}'.format(prefix, syscall.name)

    def vardecl(self, type, name, array_need_parens=False):
        if isinstance(type, OutputPointerType):
            return self.vardecl(type.target_type, '*{}'.format(name),
                                array_need_parens=True)
        elif isinstance(type, PointerType):
            decl = self.vardecl(type.target_type,
                                '{}*{}'.format(self.pointer_prefix, name),
                                array_need_parens=True)
            if type.const:
                decl = 'const ' + decl
            return decl
        elif isinstance(type, ArrayType):
            if array_need_parens:
                name = '({})'.format(name)
            return self.vardecl(
                type.element_type, '{}[{}]'.format(
                    name, type.count))
        else:
            return '{} {}'.format(self.typename(type), name)


class CGenerator(Generator):

    def __init__(self, naming, header_guard=None, machine_dep=None,
                 md_type=None, preamble=''):
        super().__init__(comment_prefix='// ')
        self.naming = naming
        self.header_guard = header_guard
        self.machine_dep = machine_dep
        self.md_type = md_type
        self.preamble = preamble

    def generate_head(self, abi):
        super().generate_head(abi)
        if self.header_guard is not None:
            print('#ifndef {}'.format(self.header_guard))
            print('#define {}'.format(self.header_guard))
            print()
        if self.preamble != '':
            print(self.preamble)

    def generate_foot(self, abi):
        if self.header_guard is not None:
            print('#endif')
        super().generate_foot(abi)

    def mi_type(self, mtype):
        if self.md_type is not None:
            if isinstance(mtype, PointerType) or mtype.name == 'size':
                return self.md_type
            elif isinstance(mtype, ArrayType):
                return ArrayType(mtype.count, self.mi_type(mtype.element_type))
            elif isinstance(mtype, AtomicType):
                return AtomicType(self.mi_type(mtype.target_type))
        return mtype

    def syscall_params(self, syscall):
        params = []
        for p in syscall.input.raw_members:
            params.append(self.naming.vardecl(p.type, p.name))
        for p in syscall.output.raw_members:
            params.append(self.naming.vardecl(OutputPointerType(p.type),
                                              p.name))
        return params


class CSyscalldefsGenerator(CGenerator):

    def generate_struct_members(self, abi, type, indent=''):
        for m in type.raw_members:
            if isinstance(m, SimpleStructMember):
                mtype = self.mi_type(m.type)
                if mtype.layout.align[0] == mtype.layout.align[1]:
                    alignas = '_Alignas({}) '.format(mtype.layout.align[0])
                else:
                    alignas = ''
                print('{}{}{};'.format(
                    indent, alignas, self.naming.vardecl(mtype, m.name)))
            elif isinstance(m, VariantStructMember):
                print('{}union {{'.format(indent))
                for x in m.members:
                    if x.name is None:
                        self.generate_struct_members(
                            abi, x.type, indent + '  ')
                    else:
                        print('{}  struct {{'.format(indent))
                        self.generate_struct_members(
                            abi, x.type, indent + '    ')
                        print('{}  }} {};'.format(indent, x.name))
                print('{}}};'.format(indent))
            else:
                raise Exception('Unknown struct member: {}'.format(m))

    def generate_type(self, abi, type):

        if self.machine_dep is not None:
            if type.layout.machine_dep != self.machine_dep:
                return

        if isinstance(type, IntLikeType):
            print('typedef {};'.format(self.naming.vardecl(
                type.int_type, self.naming.typename(type))))
            if len(type.values) > 0:
                width = max(
                    len(self.naming.valname(type, v)) for v in type.values)
                if (isinstance(type, FlagsType) or
                        isinstance(type, OpaqueType)):
                    if len(type.values) == 1 and type.values[0].value == 0:
                        val_format = 'd'
                    else:
                        val_format = '#0{}x'.format(
                            type.layout.size[0] * 2 + 2)
                else:
                    val_width = max(len(str(v.value)) for v in type.values)
                    val_format = '{}d'.format(val_width)

                for v in type.values:
                    print('#define {name:{width}} '
                          '{val:{val_format}}'.format(
                              name=self.naming.valname(type, v),
                              width=width,
                              val=v.value,
                              val_format=val_format))

        elif isinstance(type, FunctionType):
            parameters = []
            for p in type.parameters.raw_members:
                parameters.append(self.naming.vardecl(
                    self.mi_type(p.type), p.name))
            print('typedef {};'.format(
                self.naming.vardecl(
                    self.mi_type(type.return_type),
                    '{}({})'.format(self.naming.typename(type),
                                    ', '.join(parameters)),
                    array_need_parens=True)))

        elif isinstance(type, StructType):
            typename = self.naming.typename(type)

            print('typedef struct {')
            self.generate_struct_members(abi, type, '  ')
            print('}} {};'.format(typename))

            self.generate_offset_asserts(typename, type.raw_members)
            self.generate_size_assert(typename, type.layout.size)
            self.generate_align_assert(typename, type.layout.align)

        else:
            raise Exception('Unknown class of type: {}'.format(type))

        print()

    def generate_offset_asserts(
            self, type_name, members, prefix='', offset=(0, 0)):
        for m in members:
            if isinstance(m, VariantMember):
                mprefix = prefix
                if m.name is not None:
                    mprefix += m.name + '.'
                self.generate_offset_asserts(
                    type_name, m.type.members, mprefix, offset)
            elif m.offset is not None:
                moffset = (offset[0] + m.offset[0], offset[1] + m.offset[1])
                if isinstance(m, VariantStructMember):
                    self.generate_offset_asserts(
                        type_name, m.members, prefix, moffset)
                else:
                    self.generate_offset_assert(
                        type_name, prefix + m.name, moffset)

    def generate_offset_assert(self, type_name, member_name, offset):
        self.generate_layout_assert(
            'offsetof({}, {})'.format(type_name, member_name), offset)

    def generate_size_assert(self, type_name, size):
        self.generate_layout_assert('sizeof({})'.format(type_name), size)

    def generate_align_assert(self, type_name, align):
        self.generate_layout_assert('_Alignof({})'.format(type_name), align)

    def generate_layout_assert(self, expression, value):
        static_assert = '_Static_assert({}, "Incorrect layout");'
        if value[0] == value[1] or (
                self.md_type is not None and
                self.md_type.layout.size in ((4, 4), (8, 8))):
            v = value[1]
            if self.md_type is not None and self.md_type.layout.size == (4, 4):
                v = value[0]
            print(static_assert.format('{} == {}'.format(expression, v)))
        else:
            voidptr = self.naming.typename(PointerType())
            print(static_assert.format('sizeof({}) != 4 || {} == {}'.format(
                voidptr, expression, value[0])))
            print(static_assert.format('sizeof({}) != 8 || {} == {}'.format(
                voidptr, expression, value[1])))

    def generate_syscalls(self, abi, syscalls):
        pass


class CSyscallStructGenerator(CGenerator):

    def generate_syscalls(self, abi, syscalls):
        print('typedef struct {')
        for s in sorted(abi.syscalls):
            self.generate_syscall(abi, abi.syscalls[s])
        print('}} {}syscalls_t;'.format(self.naming.prefix))
        print()

    def generate_syscall(self, abi, syscall):
        if syscall.noreturn:
            return_type = VoidType()
        else:
            return_type = abi.types['errno']
        print('  {} (*{})('.format(
            self.naming.typename(return_type), syscall.name), end='')
        params = self.syscall_params(syscall)
        if params == []:
            print('void', end='')
        else:
            print()
            for p in params[:-1]:
                print('    {},'.format(p))
            print('    {}'.format(params[-1]), end='')
        print(');')

    def generate_types(self, abi, types):
        pass


class CSyscallsInfoGenerator(CGenerator):

    def print_with_line_continuation(self, text):
        lines = str.splitlines(text)
        width = max(len(line) for line in lines)
        for line in lines[:-1]:
            print('{}{} \\'.format(line, ' ' * (width - len(line))))
        print(lines[-1])

    def generate_syscalls(self, abi, syscalls):
        prefix = self.naming.prefix.upper()
        self.print_with_line_continuation(
            '#define {}SYSCALL_NAMES(SYSCALL)\n'.format(prefix) +
            '\n'.join('  SYSCALL({})'.format(s) for s in sorted(abi.syscalls))
        )
        print()
        for s in sorted(abi.syscalls):
            params = self.syscall_params(abi.syscalls[s])
            self.print_with_line_continuation(
                '#define {}SYSCALL_PARAMETERS_{}\n'.format(prefix, s) +
                ',\n'.join('  {}'.format(p) for p in params)
            )
            print()
        for s in sorted(abi.syscalls):
            syscall = abi.syscalls[s]
            params = (
                [p.name for p in syscall.input.raw_members] +
                [p.name for p in syscall.output.raw_members])
            print('#define {}SYSCALL_PARAMETER_NAMES_{}'.format(prefix, s), end='')
            if params == []:
                print()
            else:
                print(' \\\n  ' + ', '.join(params))
            print()
        for s in sorted(abi.syscalls):
            print('#define {}SYSCALL_HAS_PARAMETERS_{}(yes, no) {}'.format(
                self.naming.prefix.upper(), s,
                ('no' if self.syscall_params(abi.syscalls[s]) == []
                     else 'yes')))
        print()
        for s in sorted(abi.syscalls):
            print('#define {}SYSCALL_RETURNS_{}(yes, no) {}'.format(
                self.naming.prefix.upper(), s,
                'no' if abi.syscalls[s].noreturn else 'yes'))
        print()

    def generate_types(self, abi, types):
        pass


class CSyscallsGenerator(CGenerator):

    def generate_syscall(self, abi, syscall):
        if self.machine_dep is not None:
            if syscall.machine_dep != self.machine_dep:
                return

        self.generate_syscall_keywords(syscall)
        if syscall.noreturn:
            return_type = VoidType()
        else:
            return_type = abi.types['errno']
        print(self.naming.typename(return_type))
        print('{}('.format(self.naming.syscallname(syscall)), end='')
        params = self.syscall_params(syscall)
        if params == []:
            print('void', end='')
        else:
            print()
            for p in params[:-1]:
                print('\t{},'.format(p))
            print('\t{}'.format(params[-1]))
        print(')', end='')
        self.generate_syscall_body(abi, syscall)
        print()

    def generate_syscall_keywords(self, syscall):
        print(self.naming.function_keywords, end='')
        if syscall.noreturn:
            print('_Noreturn ', end='')

    def generate_syscall_body(self, abi, syscall):
        print(';')

    def generate_types(self, abi, types):
        pass


class CSyscallWrappersGenerator(CSyscallsGenerator):

    def generate_syscalls(self, abi, syscalls):
        print('extern {prefix}syscalls_t {prefix}syscalls;\n'.format(
            prefix=self.naming.prefix))
        for s in sorted(abi.syscalls):
            self.generate_syscall(abi, abi.syscalls[s])

    def generate_syscall_body(self, abi, syscall):
        print(' {')

        print('\t', end='')

        if not syscall.noreturn:
            print('return ', end='')

        print('{}syscalls.{}('.format(
            self.naming.prefix, syscall.name), end='')

        params = []
        for p in syscall.input.raw_members:
            params.append(p.name)
        for p in syscall.output.raw_members:
            params.append(p.name)

        if len(params) > 0:
            for p in params[:-1]:
                print('{}, '.format(p), end='')
            print('{}'.format(params[-1]), end='')
        print(');')

        if syscall.noreturn:
            print('\tfor (;;);')

        print('}')


class CLinuxSyscallsGenerator(CSyscallsGenerator):

    def generate_syscall_keywords(self, syscall):
        pass


class CNativeSyscallsGenerator(CSyscallsGenerator):

    def generate_syscall_body(self, abi, syscall):
        print(' {')

        check_okay = len(syscall.output.raw_members) > 0

        defined_regs = set()

        def define_reg(register, value=None):
            if value is None:
                if register in defined_regs:
                    return
                defn = ''
            else:
                assert(register not in defined_regs)
                defn = ' = {}'.format(value)
            print('\tregister {decl} asm("{reg}"){defn};'.format(
                decl=self.naming.vardecl(self.register_t,
                                         'reg_{}'.format(register)),
                reg=register, defn=defn))
            defined_regs.add(register)

        define_reg(self.syscall_num_register, abi.syscall_number(syscall))

        for i, p in enumerate(syscall.input.raw_members):
            define_reg(self.input_registers[i], self._ccast(
                p.type, self.register_t, p.name))

        for i in range(len(syscall.output.raw_members)):
            define_reg(self.output_registers[i])

        define_reg(self.errno_register)

        if check_okay:
            print('\tregister {};'.format(
                self.naming.vardecl(self.okay_t, 'okay')))

        print('\tasm volatile (')
        print(self.asm)
        if check_okay:
            print(self.asm_check)

        first = True
        if check_okay:
            print('\t\t: "=r"(okay)')
            first = False
        for i in range(len(syscall.output.raw_members)):
            print('\t\t{} "=r"(reg_{})'.format(
                ':' if first else ',', self.output_registers[i]))
            first = False
        if not syscall.noreturn:
            if (self.errno_register not in
                    self.output_registers[:len(syscall.output.raw_members)]):
                print('\t\t{} "=r"(reg_{})'.format(
                    ':' if first else ',', self.errno_register))
                first = False
        if first:
            print('\t\t:')

        print('\t\t: "r"(reg_{})'.format(self.syscall_num_register))
        for i in range(len(syscall.input.raw_members)):
            print('\t\t, "r"(reg_{})'.format(self.input_registers[i]))

        # Print clobbered registers. Omit the ones that are already
        # declared previously, as GCC doesn't allow that.
        print('\t\t: {});'.format(', '.join(
            '"%s"' % r
            for r in self.clobbers
            if r not in defined_regs)))
        if check_okay:
            print('\tif (okay) {')
            for i, p in enumerate(syscall.output.raw_members):
                print('\t\t*{} = {};'.format(p.name, self._ccast(
                    self.register_t,
                    p.type,
                    "reg_{}".format(self.output_registers[i]))))
            print('\t\treturn 0;')
            print('\t}')

        if syscall.noreturn:
            print('\tfor (;;);')
        else:
            print('\treturn reg_{};'.format(self.errno_register))

        print('}')

    def _ccast(self, type_from, type_to, name):
        if (isinstance(type_from, StructType) or
                isinstance(type_to, StructType)):
            if type_from.layout.size != type_to.layout.size:
                raise Exception('Can\'t cast {} to {}.'.format(
                    type_from, type_to))
            return '*({})&{}'.format(
                self.naming.typename(PointerType(type_to)), name)
        else:
            return '({}){}'.format(self.naming.typename(type_to), name)


class CNativeSyscallsAarch64Generator(CNativeSyscallsGenerator):

    syscall_num_register = 'x8'
    input_registers = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5']
    output_registers = ['x0', 'x1']
    errno_register = 'x0'

    output_register_start = 1

    clobbers = ['memory',
                'x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9',
                'x10', 'x11', 'x12', 'x13', 'x14', 'x15', 'x16', 'x17', 'x18',
                'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']

    register_t = int_types['uint64']
    okay_t = register_t

    asm = '\t\t"\\tsvc 0\\n"'
    asm_check = '\t\t"\\tcset %0, cc\\n"'


class CNativeSyscallsI686OnX86_64Generator(CSyscallsGenerator):

    def generate_syscall_body(self, abi, syscall):
        print(' {')

        # Align all arguments to 64 bits by storing them in a structure.
        if syscall.input.raw_members:
            print('\tstruct arguments {')
            for p in syscall.input.raw_members:
                if isinstance(p.type, PointerType) or p.type.name == 'size':
                    print('\t\t_Alignas(8) uint64_t {};'.format(p.name))
                else:
                    print('\t\t_Alignas(8) {};'.format(self.naming.vardecl(p.type, p.name)))
            print('\t} arguments = {')
            for p in syscall.input.raw_members:
                mi_type = self.mi_type(p.type)
                if isinstance(p.type, PointerType):
                    print('.{} = (uintptr_t){},'.format(p.name, p.name))
                else:
                    print('.{} = {},'.format(p.name, p.name))
            print('\t};')

        # Align return values to 64 bits similarly.
        print('\tstruct returns {')
        for p in syscall.output.raw_members:
            print('\t\t_Alignas(8) {};'.format(self.naming.vardecl(p.type, p.name)))
        for i in range(len(syscall.output.raw_members), 2):
            print('_Alignas(8) char unused{};'.format(i))
        print('\t} returns;')
        print('\t_Static_assert(sizeof(returns) == 16, "Size mismatch");')

        # Set up registers for system call entry.
        print('\tregister uint32_t reg_eax asm("eax") = {};'.format(
                   abi.syscall_number(syscall)))
        if syscall.input.raw_members:
            print('\tregister struct arguments *reg_ebx asm("ebx") = &arguments;')
        print('\tregister struct returns *reg_ecx asm("ecx") = &returns;')

        # Invoke system call.
        print('\tasm volatile("\\tint $0x80\\n"')
        print('\t\t: "=r"(reg_eax)')
        if syscall.input.raw_members:
            print('\t\t: "r"(reg_eax), "r"(reg_ebx), "r"(reg_ecx)')
        else:
            print('\t\t: "r"(reg_eax), "r"(reg_ecx)')
        print('\t\t: "memory");')

        # Set return values.
        if syscall.noreturn:
            print('\tfor (;;);')
        else:
            print('\tif (reg_eax != 0)')
            print('\t\treturn reg_eax;')
            for p in syscall.output.raw_members:
                print('\t*{} = returns.{};'.format(p.name, p.name))
            print('\treturn 0;')

        print('}')


class CNativeSyscallsX86_64Generator(CNativeSyscallsGenerator):

    syscall_num_register = 'rax'
    input_registers = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9']
    output_registers = ['rax', 'rdx']
    errno_register = 'rax'

    clobbers = ['memory', 'rcx', 'rdx', 'r8', 'r9', 'r10', 'r11']

    register_t = int_types['uint64']
    okay_t = int_types['char']

    asm = '\t\t"\\tsyscall\\n"'
    asm_check = '\t\t"\\tsetnc %0\\n"'


class CLinuxSyscallTableGenerator(CGenerator):

    def generate_head(self, abi):
        super().generate_head(abi)

        # Macro for placing the system call argument at the right spot
        # within a register, depending on the system's endianness.
        regalign = self.md_type.layout.align[0]
        regtype = self.naming.typename(self.md_type)
        print(
            '#ifdef __LITTLE_ENDIAN\n'
            '#define MEMBER(type, name) _Alignas({}) type name\n'
            '#else\n'
            '#define PAD(type) \\\n'
            '    ((sizeof({}) - (sizeof(type) % sizeof({}))) % sizeof({}))\n'
            '#define MEMBER(type, name) char name##_pad[PAD(type)]; type name\n'
            '#endif\n'.format(regalign, regtype, regtype, regtype))

    def generate_syscall(self, abi, syscall):
        print('static {} do_{}(const void *in, void *out)\n{{'.format(
             self.naming.typename(abi.types['errno']), syscall.name))

        # Map structures over the system call input and output registers.
        if syscall.input.raw_members:
            print('\tconst struct {')
            for p in syscall.input.raw_members:
                print('\t\tMEMBER({}, {});'.format(
                    self.naming.typename(p.type), p.name))
            print('\t} *vin = in;')
        if syscall.output.raw_members:
            print('\tstruct {')
            for p in syscall.output.raw_members:
                print('\t\tMEMBER({}, {});'.format(
                    self.naming.typename(p.type), p.name))
            print('\t} *vout = out;')

        # Invoke the system call implementation function.
        if syscall.noreturn:
            print('\t{}('.format(self.naming.syscallname(syscall)), end='')
        else:
            print('\treturn {}('.format(self.naming.syscallname(syscall)),
                  end='')
        params = []
        for p in syscall.input.raw_members:
            params.append('vin->' + p.name)
        for p in syscall.output.raw_members:
            params.append('&vout->' + p.name)
        print(', '.join(params), end='')
        print(');')
        if syscall.noreturn:
            print('\treturn 0;')
        print('}\n')

    def generate_foot(self, abi):
        # Emit the actual system call table.
        print('static {} (*syscalls[])(const void *, void *) = {{'.format(
            self.naming.typename(abi.types['errno'])))
        for idx in sorted(abi.syscalls):
            syscall = abi.syscalls[idx]
            print('\tdo_{},'.format(syscall.name))
        print('};')

        super().generate_foot(abi)
