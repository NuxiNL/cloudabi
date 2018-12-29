# Copyright (c) 2019 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .abi import *
from .generator import *
from .go_naming import *


class GoGenerator(Generator):
    def __init__(self,
                 naming,
                 machine_dep=None):
        super().__init__(comment_prefix='// ')
        self.naming = naming
        self.machine_dep = machine_dep

    def generate_head(self, abi):
        super().generate_head(abi)
        print('package cloudabi')
        print('import "unsafe"')
        print()

    def generate_type(self, abi, type):

#        if self.machine_dep is not None:
#            if type.layout.machine_dep != self.machine_dep:
#                return

        if (isinstance(type, EnumType) or isinstance(type, FlagsType) or
            isinstance(type, OpaqueType)):
            typename = self.naming.typename(type)
            print('type {} {}'.format(
                typename, self.naming.typename(type.int_type)))
            if type.values:
                print('const (')
                val_format = '#0{}x'.format(type.layout.size[0] * 2 + 2)
                for v in type.values:
                    print('  {name} {typename} = {val:{val_format}}'.format(
                        name=self.naming.valname(type, v),
                        typename=typename,
                        val=v.value,
                        val_format=val_format))
                print(')')
        elif isinstance(type, AliasType):
            print('type {} {}'.format(
                self.naming.typename(type),
                self.naming.typename(type.int_type)))
        elif isinstance(type, FunctionType):
            print('type {} func('.format(self.naming.typename(type)))
            for param in type.parameters.raw_members:
                print('  {} {},'.format(param.name,
                                        self.naming.typename(param.type)))
            print(') {}'.format(self.naming.typename(type.return_type)))
        elif isinstance(type, StructType):
            typename = self.naming.typename(type)
            structs = [(typename, type)]
            unions = []

            while len(structs) > 0 or len(unions) > 0:
                for name, struct in structs:
                    print('type {} struct {{'.format(name))
                    for m in struct.raw_members:
                        if isinstance(m, SimpleStructMember):
                            print('  {} {}'.format(
                                self.naming.fieldname(m.name),
                                self.naming.typename(m.type)))
                        elif isinstance(m, VariantStructMember):
                            unions.append((name + 'Union', m))
                            maximum_size = max(x.type.layout.size for x in m.members)
                            maximum_align = max(x.type.layout.align for x in m.members)
                            # TODO: 32 vs 64 bits.
                            print('  {}Union [{}]uint{}'.format(
                                name,
                                (maximum_size[1] + maximum_align[1] - 1) // maximum_align[1],
                                maximum_align[1] * 8))
                        else:
                            raise Exception(
                                'Unknown struct member: {}'.format(m))
                    print('}')

                    print('const (')
                    for m in struct.raw_members:
                        if isinstance(m, VariantStructMember):
                            self.generate_offset_assert(name, name + 'Union', m.offset)
                        else:
                            self.generate_offset_assert(name, self.naming.fieldname(m.name), m.offset)
                    self.generate_size_assert(name, struct.layout.size)
                    self.generate_align_assert(name, struct.layout.align)
                    print(')')

                structs = []
                for name, union in unions:
                    for x in union.members:
                        if x.name is not None:
                            structname = '{}_{}'.format(
                                typename,
                                self.naming.fieldname(x.name))
                            structs.append((structname, x.type))
                unions = []

        else:
            raise Exception('Unknown class of type: {}'.format(type))

    def generate_offset_assert(self, type_name, member_name, offset):
        self.generate_layout_assert('unsafe.Offsetof({}{{}}.{})'.format(
            type_name, member_name), offset)

    def generate_size_assert(self, type_name, size):
        self.generate_layout_assert('unsafe.Sizeof({}{{}})'.format(type_name), size)

    def generate_align_assert(self, type_name, align):
        self.generate_layout_assert('unsafe.Alignof({}{{}})'.format(type_name), align)

    def generate_layout_assert(self, expression, value):
        print('_ uintptr = {} - {}'.format(expression, value[1]))
        print('_ uintptr = {} - {}'.format(value[1], expression))
