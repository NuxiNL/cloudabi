#!/usr/bin/env python3
# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from src.itf import read_itf


class Type:

    def __init__(self, name):
        self.name = name


class IntType(Type):

    def __init__(self, name, width, alignment=None):
        super().__init__(name)
        self.width = width
        self.alignment = alignment if alignment is not None else width


class IntLikeType(Type):

    def __init__(self, name):
        super().__init__(name)
        self.cprefix = name.upper() + '_'


class AliasType(IntLikeType):

    def __init__(self, name, int_type, values):
        super().__init__(name)
        self.int_type = int_type
        self.values = values


class OpaqueType(IntLikeType):

    def __init__(self, name, int_type, values):
        super().__init__(name)
        self.int_type = int_type
        self.values = values


class EnumType(IntLikeType):

    def __init__(self, name, int_type, values):
        super().__init__(name)
        self.int_type = int_type
        self.values = values


class FlagsType(IntLikeType):

    def __init__(self, name, int_type, values):
        super().__init__(name)
        self.int_type = int_type
        self.values = values


class StructType(Type):

    def __init__(self, name, members):
        super().__init__(name)
        self.members = members


class StructMember:

    def __init__(self, name):
        self.name = name


class Syscall:

    def __init__(self, number, name):
        self.number = number
        self.name = name


int_types = {
    'uint8': IntType('uint8', 1),
    'uint16': IntType('uint16', 2),
    'uint32': IntType('uint32', 4),
    'uint64': IntType('uint64', 8),
    'int8': IntType('int8', 1),
    'int16': IntType('int16', 2),
    'int32': IntType('int32', 4),
    'int64': IntType('int64', 8),
    'size': IntType('size', 'dep'),
}

int_like_types = {
    'alias': AliasType,
    'opaque': OpaqueType,
    'enum': EnumType,
    'flags': FlagsType
}

types = {}
types.update(int_types)

syscalls_by_name = {}
syscalls_by_number = {}

spec = read_itf('cloudabi.txt')

for node in spec:
    decl = node.text.split()

    if decl[0] in int_like_types:

        if len(decl) != 3:
            raise Exception('Invalid declaration: {}'.format(node.text))

        name = decl[2]
        if name in types:
            raise Exception('Duplicate definition of {}'.format(name))

        int_type = decl[1]
        if int_type not in int_types:
            raise Exception('Invalid int type: {}'.format(int_type))

        type = int_like_types[decl[0]](name, int_type, [])

        for child in node.children:
            for grandchild in child.children:
                raise Exception('Unexpected node: {}'.format(grandchild.text))
            value_decl = child.text.split()
            if value_decl[0] == '@cprefix' and len(value_decl) <= 2:
                type.cprefix = value_decl[1] if len(value_decl) == 2 else ''
            elif len(value_decl) == 2:
                type.values.append((int(value_decl[0], 0), value_decl[1]))
            else:
                raise Exception('Invalid value: {}'.format(child.text))

        types[name] = type

    elif decl[0] == 'struct':

        if len(decl) != 2:
            raise Exception('Invalid declaration: {}'.format(decl))

        name = decl[1]
        if name in types:
            raise Exception('Duplicate definition of {}'.format(name))

        # TODO: for child in node.children:

        types[name] = StructType(name, [])

    elif decl[0] == 'syscall':

        if len(decl) != 3:
            raise Exception('Invalid declaration: {}'.format(decl))

        num = int(decl[1], 0)
        if num in syscalls_by_number:
            raise Exception('Duplicate syscall number: {}'.format(num))

        name = decl[2]
        if name in syscalls_by_name:
            raise Exception('Duplicate syscall name: {}'.format(name))

        syscall = Syscall(num, name)

        # TODO: node.children:

        syscalls_by_name[name] = syscall
        syscalls_by_number[num] = syscall

    else:
        print('Unknown top level declaration: {}'.format(node.text))
