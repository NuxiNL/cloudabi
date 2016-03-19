# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from .itf import read_itf
from .layout import Layout


class Type:

    def __init__(self, name, layout=None):
        self.name = name
        self.layout = layout


class VoidType(Type):

    def __init__(self):
        super().__init__('void', layout=Layout(None))


class IntType(Type):

    def __init__(self, name, size):
        super().__init__(name, layout=Layout(size))


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
    'size': IntType('size', (4, 8)),
}


class UserDefinedType(Type):
    pass


class IntLikeType(UserDefinedType):

    def __init__(self, name, int_type, values, cprefix=None):
        super().__init__(name, layout=int_type.layout)
        self.int_type = int_type
        self.values = values
        self.cprefix = cprefix if cprefix is not None else name.upper() + '_'


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

    def __init__(self, count, element_type):
        super().__init__('array {} {}'.format(count, element_type.name),
                         layout=Layout.array(element_type, count))
        self.count = count
        self.element_type = element_type


class PointerType(Type):

    def __init__(self, const, target_type):
        super().__init__(('cptr ' if const else 'ptr ') + target_type.name,
                         layout=Layout((4, 8), (4, 8)))
        self.const = const
        self.target_type = target_type


class AtomicType(Type):

    def __init__(self, target_type):
        super().__init__('atomic ' + target_type.name,
                         layout=target_type.layout)
        self.target_type = target_type


class StructType(UserDefinedType):

    def __init__(self, name, members):
        self.members = members
        self.raw_members = []
        for m in self.members:
            if isinstance(m, RangeStructMember):
                self.raw_members.extend(m.raw_members)
            else:
                self.raw_members.append(m)
        super().__init__(name, layout=Layout.struct(self.raw_members))
        self.dependencies = _compute_dependencies(self)


class StructMember:

    def __init__(self, name, layout=None):
        self.name = name
        self.layout = layout
        self.offset = None


class SimpleStructMember(StructMember):

    def __init__(self, name, type):
        super().__init__(name, layout=type.layout)
        self.type = type


class RangeStructMember(StructMember):

    def __init__(self, base_name, length_name, name, const, target_type):
        super().__init__(name, layout=None)
        self.type = type
        self.base_name = base_name
        self.length_name = length_name
        self.const = const
        self.target_type = target_type
        self.raw_members = [
            SimpleStructMember(base_name, PointerType(const, target_type)),
            SimpleStructMember(length_name, int_types['size'])]


class VariantStructMember(StructMember):

    def __init__(self, members):
        super().__init__(None, layout=Layout.union(members))
        self.members = members


class VariantMember:

    def __init__(self, name, tag_values, type):
        self.name = name
        self.tag_values = tag_values
        self.type = type
        self.layout = type.layout


class FunctionType(UserDefinedType):

    def __init__(self, name, parameters, return_type):
        machine_dep = (parameters.layout.machine_dep or
                       return_type.layout.machine_dep)
        super().__init__(name, layout=Layout(None, None, machine_dep))
        self.parameters = parameters
        self.return_type = return_type


class Syscall:

    def __init__(self, number, name, input, output, noreturn=False):
        self.number = number
        self.name = name
        self.input = input
        self.output = output
        self.noreturn = noreturn


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

                values = []
                attr = {}

                for child in node.children:
                    self.__expect_no_children(child)
                    value_decl = child.text.split()
                    if value_decl[0] == '@cprefix' and len(value_decl) <= 2:
                        attr['cprefix'] = (value_decl[1]
                                           if len(value_decl) == 2 else '')
                    elif len(value_decl) == 2:
                        values.append((int(value_decl[0], 0), value_decl[1]))
                    else:
                        raise Exception('Invalid value: {}'.format(child.text))

                self.types[name] = int_like_types[decl[0]](
                    name, int_types[int_type], values, **attr)

            elif decl[0] == 'struct':

                if len(decl) != 2:
                    raise Exception('Invalid declaration: {}'.format(decl))

                name = decl[1]
                if name in self.types:
                    raise Exception('Duplicate definition of {}'.format(name))

                self.types[name] = self.parse_struct(name, node.children)

            elif decl[0] == 'function':

                if len(decl) != 2:
                    raise Exception('Invalid declaration: {}'.format(decl))

                name = decl[1]
                if name in self.types:
                    raise Exception('Duplicate definition of {}'.format(name))

                parameters = StructType('', [])
                return_type = VoidType()

                if len(node.children) > 0 and node.children[0].text == 'in':
                    param_spec = node.children.pop(0)
                    parameters = self.parse_struct(
                        None, param_spec.children)

                if len(node.children) > 0 and node.children[0].text == 'out':
                    out_spec = node.children.pop(0)
                    if len(out_spec.children) != 1:
                        raise Exception(
                            'Expected a single return type in `out\' section of function.')
                    self.__expect_no_children(out_spec.children[0])
                    return_type = (
                        self.parse_type(out_spec.children[0].text.split()))

                self.types[name] = FunctionType(
                    name, parameters, return_type)

            elif decl[0] == 'syscall':

                if len(decl) != 3:
                    raise Exception('Invalid declaration: {}'.format(decl))

                num = int(decl[1], 0)
                if num in self.syscalls_by_number:
                    raise Exception('Duplicate syscall number: {}'.format(num))

                name = decl[2]
                if name in self.syscalls_by_name:
                    raise Exception('Duplicate syscall name: {}'.format(name))

                input = StructType('', [])
                output = StructType('', [])
                attr = {}

                if len(node.children) > 0 and node.children[0].text == 'in':
                    in_spec = node.children.pop(0)
                    input = self.parse_struct(None, in_spec.children)

                if len(node.children) > 0:
                    if node.children[0].text == 'out':
                        out_spec = node.children.pop(0)
                        output = self.parse_struct(
                            None, out_spec.children)

                    elif node.children[0].text == 'noreturn':
                        noreturn_spec = node.children.pop(0)
                        self.__expect_no_children(noreturn_spec)
                        attr['noreturn'] = True

                self.__expect_no_children(node)

                syscall = Syscall(num, name, input, output, **attr)

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

        members = []

        for node in spec:
            mem_decl = node.text.split()
            if mem_decl[0] == 'variant' and len(mem_decl) == 2:
                tag_member_name = mem_decl[1]
                tag_member = None
                for m in members:
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
                members.append(mem)
                pass
            elif mem_decl[0] in {'range', 'crange'}:
                self.__expect_no_children(node)
                if len(mem_decl) < 5:
                    raise Exception('Invalid range: {}'.format(node.text))
                mem_type = self.parse_type(mem_decl[1:-3])
                mem_base_name, mem_length_name, mem_name = mem_decl[-3:]
                members.append(
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
                members.append(SimpleStructMember(mem_name, mem_type))

        return StructType(name, members)

    def parse_variant(self, tag_member, spec):

        tag_type = tag_member.type

        members = []

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
            members.append(VariantMember(name, tag_values, type))

        return VariantStructMember(members)

    @staticmethod
    def __expect_no_children(node):
        if len(node.children) > 0:
            raise Exception(
                'Unexpected node inside {}: {}'.format(
                    node.text, node.children[0].text))


def _compute_dependencies(thing):

    if hasattr(thing, 'dependencies'):
        return thing.dependencies

    deps = set()

    members = set(getattr(thing, 'members', []))
    for attr in ['type', 'target_type', 'element_type']:
        m = getattr(thing, attr, None)
        if m is not None:
            members.add(m)

    for m in members:
        if isinstance(m, UserDefinedType) and m.name is not None:
            deps.add(m.name)

        deps.update(_compute_dependencies(m))

    return deps
