from .abi import *
from .markdown_naming import *


class GoNaming:
    def __init__(self):
        pass

    def typename(self, type):
        if isinstance(type, VoidType):
            # VoidType may occur directly for function return types.
            # Return an empty string for void returns.
            return ''
        elif isinstance(type, IntType):
            if type.name == 'char':
                return 'byte'
            elif type.name == 'size':
                return 'uint'
            elif type.name[0:3] == 'int':
                return 'int' + type.name[3:]
            elif type.name[0:4] == 'uint':
                return 'uint' + type.name[4:]
            else:
                raise Exception('Unknown int type: {}'.format(type.name))
        elif isinstance(type, UserDefinedType):
            return ''.join(c.capitalize() for c in type.name.split('_'))
        elif isinstance(type, AtomicType):
            # TODO: Update once rust has generic atomic types
            return self.typename(type.target_type)
        elif isinstance(type, PointerType):
            if isinstance(type.target_type, FunctionType):
                return self.typename(type.target_type)
            if isinstance(type.target_type, VoidType):
                return 'unsafe.Pointer'
            return '*' + self.typename(type.target_type)
        elif isinstance(type, ArrayType):
            return '[{}]{}'.format(
                type.count, self.typename(type.element_type))
        else:
            raise Exception('Unable to generate Rust declaration '
                            'for type: {}'.format(type))

    def valname(self, type, value):
        return '{}_{}'.format(
            ''.join(c.capitalize() for c in type.name.split('_')),
            ''.join(c.capitalize() for c in value.name.split('_')))

    def syscallname(self, syscall):
        return syscall.name

    def vardecl(self, type, name, array_need_parens=False):
        return '{}: {}'.format(name, self.typename(type))

    def fieldname(self, name):
        return ''.join(c.capitalize() for c in name.split('_'))
