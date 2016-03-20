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


class SpecialValue:

    def __init__(self, name, value):
        self.name = name
        self.value = value


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

    def __init__(self, tag, members):
        super().__init__(None, layout=Layout.union(members))
        self.tag = tag
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

    def __init__(self):
        self.types = {}
        self.syscalls_by_name = {}
        self.syscalls_by_number = {}


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
