# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from ..abi import *
from ..generator import *


class CHeaderGenerator(Generator):

    def __init__(self, prefix):
        super().__init__(comment_start='//')
        self.prefix = prefix

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

    def generate_struct_members(self, type, indent=''):
        for m in type.raw_members:
            if isinstance(m, SimpleStructMember):
                print('{}{};'.format(indent, self.cdecl(m.type, m.name)))
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

        if isinstance(type, IntLikeType):
            print('typedef {};'.format(self.cdecl(type.int_type,
                                                  self.ctypename(type))))
            use_hex = (isinstance(type, FlagsType) or
                       isinstance(type, OpaqueType))
            for val, name in type.values:
                if use_hex:
                    val = hex(val)
                print('#define {}{}{} {}'.format(
                    self.prefix.upper(),
                    type.cprefix,
                    name.upper(),
                    val))

        elif isinstance(type, FunctionPointerType):
            parameters = []
            for p in type.parameters.raw_members:
                parameters.append(self.cdecl(p.type, p.name))
            print('typedef {} (*{})({});'.format(
                self.cdecl(type.return_type),
                self.cdecl(type), ', '.join(parameters)))
            pass

        elif isinstance(type, StructType):
            print('typedef struct {')
            self.generate_struct_members(type, '\t')
            print('}} {};'.format(self.ctypename(type)))

        else:
            raise Exception('Unknown class of type: {}'.format(type))

        print()

    def generate_syscall(self, syscall):
        params = []
        for p in syscall.input.raw_members:
            params.append(self.cdecl(p.type, p.name))
        for p in syscall.output.raw_members:
            params.append(self.cdecl(PointerType(False, p.type), p.name))
        if params == []:
            params = ['void']

        print('{}errno_t {}sys_{}({});'.format(
            self.prefix, self.prefix,
            syscall.name, ', '.join(params)))
