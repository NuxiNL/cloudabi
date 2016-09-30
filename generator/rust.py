# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

from .abi import *
from .generator import *


class RustNaming:

    def __init__(self):
        pass

    def typename(self, type):
        if isinstance(type, VoidType):
            return '()'
        elif isinstance(type, IntType):
            if type.name == 'char':
                return 'u8'
            elif type.name == 'size':
                return 'usize'
            elif type.name[0:3] == 'int':
                return 'i' + type.name[3:]
            elif type.name[0:4] == 'uint':
                return 'u' + type.name[4:]
            else:
                raise Exception('Unknown int type: {}'.format(type.name))
        elif isinstance(type, UserDefinedType):
            return '{}_t'.format(type.name)
        elif isinstance(type, AtomicType):
            return self.typename(type.target_type)
            #TODO
            #return 'atomic!({})'.format(
            #    self.typename(type.target_type))
        elif isinstance(type, PointerType):
            mut = 'mut'
            if type.const or isinstance(type.target_type, FunctionType):
                mut = ''
            if isinstance(type.target_type, VoidType):
                return '*{} c_void'.format(mut)
            else:
                return '*{} {}'.format(mut, self.typename(type.target_type))
        elif isinstance(type, ArrayType):
            return '[{}; {}]'.format(
                self.typename(type.element_type),
                type.count)
        else:
            raise Exception('Unable to generate Rust declaration '
                            'for type: {}'.format(type))

    def valname(self, type, value):
        return '{}{}'.format(type.cprefix, value.name).upper()

    def syscallname(self, syscall):
        return syscall.name

    def vardecl(self, type, name, array_need_parens=False):
        return '{}: {}'.format(name, self.typename(type))


class RustGenerator(Generator):

    def __init__(self, naming):
        super().__init__(comment_prefix='// ')
        self.naming = naming

    def syscall_params(self, syscall):
        params = []
        for p in syscall.input.raw_members:
            params.append(self.naming.vardecl(p.type, p.name))
        for p in syscall.output.raw_members:
            params.append(self.naming.vardecl(OutputPointerType(p.type),
                                              p.name))
        return params


class RustSyscalldefsGenerator(RustGenerator):

    def generate_struct_members(self, abi, type, indent=''):
        for m in type.raw_members:
            if isinstance(m, SimpleStructMember):
                print(indent + '{}: {},'.format(
                    m.name, self.naming.typename(m.type)))
            elif isinstance(m, VariantStructMember):
                print(indent + 'union {')
                for x in m.members:
                    if x.name is None:
                        self.generate_struct_members(
                            abi, x.type, indent + '  ')
                    else:
                        print(indent + '  struct {} {{'.format(x.name))
                        self.generate_struct_members(
                            abi, x.type, indent + '    ')
                        print(indent + '  },')
                print(indent + '},')
            else:
                raise Exception('Unknown struct member: {}'.format(m))

    def generate_type(self, abi, type):

        if isinstance(type, IntLikeType):
            print('pub type {} = {};'.format(
                self.naming.typename(type),
                self.naming.typename(type.int_type)))
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
                    print('pub const {name:{width}}: {type} '
                          '= {val:{val_format}};'.format(
                              name=self.naming.valname(type, v),
                              width=width,
                              type=self.naming.typename(type),
                              val=v.value,
                              val_format=val_format))

        elif isinstance(type, FunctionType):
            # TODO
            pass

        elif isinstance(type, StructType):
            print('pub struct {} {{'.format(self.naming.typename(type)))
            self.generate_struct_members(abi, type, '  ')
            print('}')

        else:
            raise Exception('Unknown class of type: {}'.format(type))

        print()

