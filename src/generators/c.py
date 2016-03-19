# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from ..abi import *
from ..generator import *


class CGenerator(Generator):

    def __init__(self, prefix, header_guard=None, machine_dep=None):
        super().__init__(comment_start='//')
        self.prefix = prefix
        self.header_guard = header_guard
        self.machine_dep = machine_dep

    def generate_head(self):
        super().generate_head()
        if self.header_guard is not None:
            print('#ifndef {}'.format(self.header_guard))
            print('#define {}'.format(self.header_guard))
            print()

    def generate_foot(self):
        if self.header_guard is not None:
            print('#endif')
        super().generate_foot()

    def ctypename(self, type):
        if isinstance(type, VoidType):
            return 'void'
        elif isinstance(type, IntType):
            if type.name == 'char':
                return 'char'
            return '{}_t'.format(type.name)
        elif (isinstance(type, IntLikeType) or
              isinstance(type, FunctionPointerType) or
              isinstance(type, StructType)):
            return '{}{}_t'.format(self.prefix, type.name)

        else:
            raise Exception(
                'Unable to generate C type name for type: {}'.format(type))

    def cdecl(self, type, name=''):
        if (isinstance(type, VoidType) or
                isinstance(type, IntType) or
                isinstance(type, IntLikeType) or
                isinstance(type, StructType) or
                isinstance(type, FunctionPointerType)):
            return '{} {}'.format(self.ctypename(type), name).rstrip()

        elif isinstance(type, PointerType):
            decl = self.cdecl(type.target_type, '*{}'.format(name))
            if type.const:
                decl = 'const ' + decl
            return decl

        elif isinstance(type, ArrayType):
            if name.startswith('*'):
                name = '({})'.format(name)
            return self.cdecl(
                type.element_type, '{}[{}]'.format(
                    name, type.count))

        elif isinstance(type, AtomicType):
            return '_Atomic({}) {}'.format(
                self.cdecl(type.target_type), name).rstrip()

        else:
            raise Exception(
                'Unable to generate C type declaration for type: {}'.format(type))

    def syscall_params(self, syscall):
        params = []
        for p in syscall.input.raw_members:
            params.append(self.cdecl(p.type, p.name))
        for p in syscall.output.raw_members:
            params.append(self.cdecl(PointerType(False, p.type), p.name))
        if params == []:
            params = ['void']
        return params


class CSyscalldefsGenerator(CGenerator):

    def generate_struct_members(self, type, indent=''):
        for m in type.raw_members:
            if isinstance(m, SimpleStructMember):
                if m.type.layout.align[0] == m.type.layout.align[1]:
                    alignas = '_Alignas({}) '.format(m.type.layout.align[0])
                else:
                    alignas = ''
                print('{}{}{};'.format(
                    indent, alignas, self.cdecl(m.type, m.name)))
            elif isinstance(m, VariantStructMember):
                print('{}union {{'.format(indent))
                for x in m.members:
                    if x.name is None:
                        self.generate_struct_members(x.type, indent + '\t')
                    else:
                        print('{}\tstruct {{'.format(indent))
                        self.generate_struct_members(x.type, indent + '\t\t')
                        print('{}\t}} {};'.format(indent, x.name))
                print('{}}};'.format(indent))
            else:
                raise Exception('Unknown struct member: {}'.format(m))

    def generate_type(self, type):

        if self.machine_dep != None:
            if type.layout.machine_dep != self.machine_dep:
                return

        if isinstance(type, IntLikeType):
            print('typedef {};'.format(self.cdecl(type.int_type,
                                                  self.ctypename(type))))
            if len(type.values) > 0:
                width = max(len(name) for val, name in type.values)
                if (isinstance(type, FlagsType) or
                        isinstance(type, OpaqueType)):
                    if len(type.values) == 1 and type.values[0][0] == 0:
                        val_format = 'd'
                    else:
                        val_format = '#0{}x'.format(
                            type.layout.size[0] * 2 + 2)
                else:
                    val_width = max(len(str(val)) for val, name in type.values)
                    val_format = '{}d'.format(val_width)

                for val, name in type.values:
                    print('#define {prefix}{cprefix}{name:{width}} '
                          '{val:{val_format}}'.format(
                              prefix=self.prefix.upper(),
                              cprefix=type.cprefix,
                              name=name.upper(),
                              width=width,
                              val=val,
                              val_format=val_format))

        elif isinstance(type, FunctionPointerType):
            parameters = []
            for p in type.parameters.raw_members:
                parameters.append(self.cdecl(p.type, p.name))
            print('typedef {} (*{})({});'.format(
                self.cdecl(type.return_type),
                self.cdecl(type), ', '.join(parameters)))
            pass

        elif isinstance(type, StructType):
            typename = self.ctypename(type)

            print('typedef struct {')
            self.generate_struct_members(type, '\t')
            print('}} {};'.format(typename))

            self.generate_offset_asserts(typename, type.raw_members)

            if type.layout is not None:
                self.generate_size_assert(typename, type.layout.size)

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
        offsetof = 'offsetof({}, {})'.format(type_name, member_name)
        static_assert = '_Static_assert({}, "Offset incorrect");'
        if offset[0] == offset[1]:
            print(static_assert.format('{} == {}'.format(offsetof, offset[0])))
        else:
            print(static_assert.format('sizeof(void*) != 4 || {} == {}'.format(
                offsetof, offset[0])))
            print(static_assert.format('sizeof(void*) != 8 || {} == {}'.format(
                offsetof, offset[1])))

    def generate_size_assert(self, type_name, size):
        sizeof = 'sizeof({})'.format(type_name)
        static_assert = '_Static_assert({}, "Size incorrect");'
        if size[0] == size[1]:
            print(static_assert.format('{} == {}'.format(sizeof, size[0])))
        else:
            print(static_assert.format('sizeof(void*) != 4 || {} == {}'.format(
                sizeof, size[0])))
            print(static_assert.format('sizeof(void*) != 8 || {} == {}'.format(
                sizeof, size[1])))

    def generate_syscalls(self, syscalls):
        pass


class CSyscallsGenerator(CGenerator):

    def generate_syscall(self, syscall):
        print('inline static {}errno_t'.format(self.prefix))
        print('{}sys_{}('.format(self.prefix, syscall.name), end='')
        params = self.syscall_params(syscall)
        if params == ['void']:
            print('void', end='')
        else:
            print()
            for p in params[:-1]:
                print('\t{},'.format(p))
            print('\t{}'.format(params[-1]))
        print(') {')
        print('\t// TODO')
        print('}')
        print()

    def generate_types(self, types):
        pass
