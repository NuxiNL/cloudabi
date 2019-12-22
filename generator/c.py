# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .abi import *
from .generator import *


class CGenerator(Generator):
    def __init__(self,
                 naming,
                 header_guard=None,
                 machine_dep=None,
                 md_type=None,
                 preamble='',
                 postamble=''):
        super().__init__(comment_prefix='// ')
        self.naming = naming
        self.header_guard = header_guard
        self.machine_dep = machine_dep
        self.md_type = md_type
        self.preamble = preamble
        self.postamble = postamble

    def generate_head(self, abi):
        super().generate_head(abi)
        if self.header_guard is not None:
            print('#ifndef {}'.format(self.header_guard))
            print('#define {}'.format(self.header_guard))
            print()
        if self.preamble != '':
            print(self.preamble)
        print('#ifdef __cplusplus')
        print('extern "C" {')
        print('#endif')
        print()

    def generate_foot(self, abi):
        print('#ifdef __cplusplus')
        print('}  // extern "C"')
        print('#endif')
        print()
        if self.postamble != '':
            print(self.postamble)
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
            params.append(
                self.naming.vardecl(OutputPointerType(p.type), p.name))
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
                print('{}{}{};'.format(indent, alignas,
                                       self.naming.vardecl(mtype, m.name)))
            elif isinstance(m, VariantStructMember):
                print('{}union {{'.format(indent))
                for x in m.members:
                    if x.name is None:
                        self.generate_struct_members(abi, x.type,
                                                     indent + '  ')
                    else:
                        print('{}  struct {{'.format(indent))
                        self.generate_struct_members(abi, x.type,
                                                     indent + '    ')
                        print('{}  }} {};'.format(indent, x.name))
                print('{}}};'.format(indent))
            else:
                raise Exception('Unknown struct member: {}'.format(m))

    def generate_type(self, abi, type):

        if self.machine_dep is not None:
            if type.layout.machine_dep != self.machine_dep:
                return

        if isinstance(type, IntLikeType):
            print('typedef {};'.format(
                self.naming.vardecl(type.int_type,
                                    self.naming.typename(type))))
            if len(type.values) > 0:
                width = max(
                    len(self.naming.valname(type, v)) for v in type.values)
                if (isinstance(type, FlagsType)
                        or isinstance(type, OpaqueType)):
                    if len(type.values) == 1 and type.values[0].value == 0:
                        val_format = 'd'
                    elif type.int_type.name[0] == 'i':  # Signed
                        val_format = 'd'
                    else:
                        val_format = '#0{}x'.format(type.layout.size[0] * 2 +
                                                    2)
                else:
                    val_width = max(len(str(v.value)) for v in type.values)
                    val_format = '{}d'.format(val_width)

                for v in type.values:
                    print('#define {name:{width}} '
                          '{val:{val_format}}'.format(name=self.naming.valname(
                              type, v),
                                                      width=width,
                                                      val=v.value,
                                                      val_format=val_format))

        elif isinstance(type, FunctionType):
            parameters = []
            for p in type.parameters.raw_members:
                parameters.append(
                    self.naming.vardecl(self.mi_type(p.type), p.name))
            print('typedef {};'.format(
                self.naming.vardecl(self.mi_type(type.return_type),
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

    def generate_offset_asserts(self,
                                type_name,
                                members,
                                prefix='',
                                offset=(0, 0)):
        for m in members:
            if isinstance(m, VariantMember):
                mprefix = prefix
                if m.name is not None:
                    mprefix += m.name + '.'
                self.generate_offset_asserts(type_name, m.type.members,
                                             mprefix, offset)
            elif m.offset is not None:
                moffset = (offset[0] + m.offset[0], offset[1] + m.offset[1])
                if isinstance(m, VariantStructMember):
                    self.generate_offset_asserts(type_name, m.members, prefix,
                                                 moffset)
                else:
                    self.generate_offset_assert(type_name, prefix + m.name,
                                                moffset)

    def generate_offset_assert(self, type_name, member_name, offset):
        self.generate_layout_assert(
            'offsetof({}, {})'.format(type_name, member_name), offset)

    def generate_size_assert(self, type_name, size):
        self.generate_layout_assert('sizeof({})'.format(type_name), size)

    def generate_align_assert(self, type_name, align):
        self.generate_layout_assert('_Alignof({})'.format(type_name), align)

    def generate_layout_assert(self, expression, value):
        static_assert = '_Static_assert({}, "Incorrect layout");'
        if value[0] == value[1] or (self.md_type is not None
                                    and self.md_type.layout.size in ((4, 4),
                                                                     (8, 8))):
            v = value[1]
            if self.md_type is not None and self.md_type.layout.size == (4, 4):
                v = value[0]
            print(static_assert.format('{} == {}'.format(expression, v)))
        else:
            voidptr = self.naming.typename(PointerType())
            print(
                static_assert.format('sizeof({}) != 4 || {} == {}'.format(
                    voidptr, expression, value[0])))
            print(
                static_assert.format('sizeof({}) != 8 || {} == {}'.format(
                    voidptr, expression, value[1])))

    def generate_syscalls(self, abi, syscalls):
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
            '\n'.join('  SYSCALL({})'.format(s) for s in sorted(abi.syscalls)))
        print()
        for s in sorted(abi.syscalls):
            params = self.syscall_params(abi.syscalls[s])
            self.print_with_line_continuation(
                '#define {}SYSCALL_PARAMETERS_{}\n'.format(prefix, s) +
                ',\n'.join('  {}'.format(p) for p in params))
            print()
        for s in sorted(abi.syscalls):
            syscall = abi.syscalls[s]
            params = ([p.name for p in syscall.input.raw_members] +
                      [p.name for p in syscall.output.raw_members])
            print('#define {}SYSCALL_PARAMETER_NAMES_{}'.format(prefix, s),
                  end='')
            if params == []:
                print()
            else:
                print(' \\\n  ' + ', '.join(params))
            print()
        for s in sorted(abi.syscalls):
            print('#define {}SYSCALL_HAS_PARAMETERS_{}(yes, no) {}'.format(
                self.naming.prefix.upper(), s, ('no' if self.syscall_params(
                    abi.syscalls[s]) == [] else 'yes')))
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
        print(self.naming.syscallname(syscall))
        print('(')
        params = self.syscall_params(syscall)
        if params == []:
            print('void')
        else:
            print(','.join(params))
        print(')')
        self.generate_syscall_body(abi, syscall)
        print()

    def generate_syscall_keywords(self, syscall):
        if syscall.noreturn:
            print('_Noreturn')

    def generate_syscall_body(self, abi, syscall):
        print(';')

    def generate_types(self, abi, types):
        pass


class CLinuxSyscallsGenerator(CSyscallsGenerator):
    def generate_syscall_keywords(self, syscall):
        pass


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
        print('static {} do_{}(const void *in, void *out) {{'.format(
            self.naming.typename(abi.types['errno']), syscall.name))

        # Map structures over the system call input and output registers.
        if syscall.input.raw_members:
            print('const struct {')
            for p in syscall.input.raw_members:
                print('MEMBER({}, {});'.format(self.naming.typename(p.type),
                                               p.name))
            print('} *vin = in;')
        if syscall.output.raw_members:
            print('struct {')
            for p in syscall.output.raw_members:
                print('MEMBER({}, {});'.format(self.naming.typename(p.type),
                                               p.name))
            print('} *vout = out;')

        # Invoke the system call implementation function.
        if not syscall.noreturn:
            print('return')
        print(self.naming.syscallname(syscall))
        params = []
        for p in syscall.input.raw_members:
            params.append('vin->' + p.name)
        for p in syscall.output.raw_members:
            params.append('&vout->' + p.name)
        print('(', ', '.join(params), ');')
        if syscall.noreturn:
            print('return 0;')
        print('}\n')

    def generate_foot(self, abi):
        # Emit the actual system call table.
        print('static {} (*syscalls[])(const void *, void *) = {{'.format(
            self.naming.typename(abi.types['errno'])))
        for idx in sorted(abi.syscalls):
            syscall = abi.syscalls[idx]
            print('do_{},'.format(syscall.name))
        print('};')

        super().generate_foot(abi)
