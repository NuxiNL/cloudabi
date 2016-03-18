# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from src.itf import read_itf


class Type:

    def __init__(self, name):
        self.name = name


class VoidType(Type):

    def __init__(self):
        super().__init__('void')


class IntType(Type):

    def __init__(self, name, width, alignment=None):
        super().__init__(name)
        self.width = width
        self.alignment = alignment if alignment is not None else width


int_types = {
    'char': IntType('char', 1),
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


class IntLikeType(Type):

    def __init__(self, name, int_type, values):
        super().__init__(name)
        self.int_type = int_type
        self.values = values
        self.cprefix = name.upper() + '_'


class AliasType(IntLikeType):
    pass


class OpaqueType(IntLikeType):
    pass


class EnumType(IntLikeType):
    pass


class FlagsType(IntLikeType):
    pass


int_like_types = {
    'alias': AliasType,
    'opaque': OpaqueType,
    'enum': EnumType,
    'flags': FlagsType
}


class ArrayType(Type):

    def __init__(self, count, type):
        super().__init__('array {} {}'.format(count, type.name))
        self.count = count
        self.type = type


class PointerType(Type):

    def __init__(self, const, type):
        super().__init__(('cptr ' if const else 'ptr ') + type.name)
        self.const = const
        self.type = type


class AtomicType(Type):

    def __init__(self, type):
        super().__init__('atomic ' + type.name)
        self.type = type


class StructType(Type):

    def __init__(self, name, members):
        super().__init__(name)
        self.members = members
        self.cprefix = ''


class StructMember:

    def __init__(self, name):
        self.name = name


class SimpleStructMember(StructMember):

    def __init__(self, name, type):
        super().__init__(name)
        self.type = type


class RangeStructMember(StructMember):

    def __init__(self, base_name, length_name, name, const, type):
        self.type = type
        self.base_name = base_name
        self.length_name = length_name
        self.name = name
        self.const = const
        self.type = type


class VariantStructMember(StructMember):

    def __init__(self, members):
        super().__init__(None)
        self.members = members


class VariantMember:

    def __init__(self, name, tag_values, type):
        self.name = name
        self.tag_values = tag_values
        self.type = type


class FunctionPointerType(Type):

    def __init__(self, name, parameters, return_type):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type


class Syscall:

    def __init__(self, number, name, input, output):
        self.number = number
        self.name = name
        self.input = input
        self.output = output
        self.noreturn = False


class Abi:

    def __init__(self, file_name):
        self.types = {}
        self.syscalls_by_name = {}
        self.syscalls_by_number = {}

        for node in read_itf(file_name):
            decl = node.text.split()

            if decl[0] in int_like_types:

                if len(decl) != 3:
                    raise Exception(
                        'Invalid declaration: {}'.format(
                            node.text))

                name = decl[2]
                if name in self.types:
                    raise Exception('Duplicate definition of {}'.format(name))

                int_type = decl[1]
                if int_type not in int_types:
                    raise Exception('Invalid int type: {}'.format(int_type))

                type = int_like_types[decl[0]](name, int_type, [])

                for child in node.children:
                    self.__expect_no_children(child)
                    value_decl = child.text.split()
                    if value_decl[0] == '@cprefix' and len(value_decl) <= 2:
                        type.cprefix = value_decl[1] if len(
                            value_decl) == 2 else ''
                    elif len(value_decl) == 2:
                        type.values.append(
                            (int(value_decl[0], 0), value_decl[1]))
                    else:
                        raise Exception('Invalid value: {}'.format(child.text))

                self.types[name] = type

            elif decl[0] == 'struct':

                if len(decl) != 2:
                    raise Exception('Invalid declaration: {}'.format(decl))

                name = decl[1]
                if name in self.types:
                    raise Exception('Duplicate definition of {}'.format(name))

                self.types[name] = self.parse_struct(name, node.children)

            elif decl[0] == 'funptr':

                if len(decl) != 2:
                    raise Exception('Invalid declaration: {}'.format(decl))

                name = decl[1]
                if name in self.types:
                    raise Exception('Duplicate definition of {}'.format(name))

                type = FunctionPointerType(name, [], VoidType())

                if len(node.children) > 0 and node.children[0].text == 'in':
                    param_spec = node.children.pop(0)
                    type.parameters = self.parse_struct(
                        None, param_spec.children)

                if len(node.children) > 0 and node.children[0].text == 'out':
                    out_spec = node.children.pop(0)
                    if len(out_spec.children) != 1:
                        raise Exception(
                            'Expected a single return type in `out\' section of funptr.')
                    type.return_type = self.parse_type(out_spec.children[0])

                self.types[name] = type

            elif decl[0] == 'syscall':

                if len(decl) != 3:
                    raise Exception('Invalid declaration: {}'.format(decl))

                num = int(decl[1], 0)
                if num in self.syscalls_by_number:
                    raise Exception('Duplicate syscall number: {}'.format(num))

                name = decl[2]
                if name in self.syscalls_by_name:
                    raise Exception('Duplicate syscall name: {}'.format(name))

                syscall = Syscall(num, name, [], [])

                if len(node.children) > 0 and node.children[0].text == 'in':
                    in_spec = node.children.pop(0)
                    syscall.input = self.parse_struct(None, in_spec.children)

                if len(node.children) > 0:
                    if node.children[0].text == 'out':
                        out_spec = node.children.pop(0)
                        syscall.output = self.parse_struct(
                            None, out_spec.children)

                    elif node.children[0].text == 'noreturn':
                        noreturn_spec = node.children.pop(0)
                        self.__expect_no_children(noreturn_spec)
                        syscall.noreturn = True

                self.__expect_no_children(node)

                self.syscalls_by_name[name] = syscall
                self.syscalls_by_number[num] = syscall

            else:
                print('Invalid top level declaration: {}'.format(node.text))

    def parse_type(self, decl):
        if decl == ['void']:
            return VoidType()
        elif len(decl) == 1:
            if decl[0] in int_types:
                return int_types[decl[0]]
            if decl[0] in self.types:
                return self.types[decl[0]]
            raise Exception('Unknown type {}'.format(decl[0]))
        elif decl[:1] == ['array'] and len(decl) > 2:
            return ArrayType(int(decl[1], 0), self.parse_type(decl[2:]))
        elif decl[:1] == ['ptr']:
            return PointerType(False, self.parse_type(decl[1:]))
        elif decl[:1] == ['cptr']:
            return PointerType(True, self.parse_type(decl[1:]))
        elif decl[:1] == ['atomic']:
            return AtomicType(self.parse_type(decl[1:]))
        else:
            raise Exception('Invalid type: {}'.format(decl))

    def parse_struct(self, name, spec):

        type = StructType(name, [])

        for node in spec:
            mem_decl = node.text.split()
            if mem_decl[0] == '@cprefix' and len(mem_decl) == 2:
                self.__expect_no_children(node)
                type.cprefix = mem_decl[1]
            elif mem_decl[0] == 'variant' and len(mem_decl) == 2:
                tag_member_name = mem_decl[1]
                tag_member = None
                for m in type.members:
                    if m.name == tag_member_name:
                        if (isinstance(m, SimpleStructMember) and
                            (isinstance(m.type, EnumType) or
                             isinstance(m.type, AliasType))):
                            tag_member = m
                            break
                        else:
                            raise Exception(
                                'Variant tag ({}) must be an enum or an alias type.'.format(
                                    m.name))
                if tag_member is None:
                    raise Exception(
                        'No such member to use as variant tag: {}.'.format(tag_member_name))
                mem = self.parse_variant(tag_member, node.children)
                type.members.append(mem)
                pass
            elif mem_decl[0] in {'range', 'crange'}:
                self.__expect_no_children(node)
                if len(mem_decl) < 5:
                    raise Exception('Invalid range: {}'.format(node.text))
                mem_type = self.parse_type(mem_decl[1:-3])
                mem_base_name, mem_length_name, mem_name = mem_decl[-3:]
                type.members.append(
                    RangeStructMember(
                        mem_base_name,
                        mem_length_name,
                        mem_name,
                        mem_decl[0] == 'crange',
                        mem_type))
            else:
                self.__expect_no_children(node)
                mem_name = mem_decl[-1]
                mem_type = self.parse_type(mem_decl[:-1])
                type.members.append(SimpleStructMember(mem_name, mem_type))

        return type

    def parse_variant(self, tag_member, spec):

        tag_type = tag_member.type

        variant = VariantStructMember([])

        for node in spec:
            tag_values = node.text.split()
            for v in tag_values:
                if not any(v == tv[1] for tv in tag_type.values):
                    raise Exception(
                        'Variant tag type {} has no value {}'.format(
                            tag_type.name, v))
            if len(node.children) != 1:
                raise Exception(
                    'Excepted a single member in variant member `{}\'.'.format(
                        node.text))
            decl = node.children[0].text.split()
            if len(decl) == 2 and decl[0] == 'struct':
                name = decl[1]
                spec = node.children[0].children
            else:
                name = None
                spec = node.children
            type = self.parse_struct(None, spec)
            variant.members.append(VariantMember(name, tag_values, type))

        return variant

    @staticmethod
    def __expect_no_children(node):
        if len(node.children) > 0:
            raise Exception(
                'Unexpected node inside {}: {}'.format(
                    node.text, node.children[0].text))
