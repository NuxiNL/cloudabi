from .abi import *
from .markdown_naming import *


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
            return type.name
        elif isinstance(type, AtomicType):
            # TODO: Update once rust has generic atomic types
            return self.typename(type.target_type)
        elif isinstance(type, PointerType):
            if isinstance(type.target_type, FunctionType):
                return self.typename(type.target_type)
            mut = 'const' if type.const else 'mut'
            return '*{} {}'.format(mut, self.typename(type.target_type))
        elif isinstance(type, ArrayType):
            return '[{}; {}]'.format(self.typename(type.element_type),
                                     type.count)
        else:
            raise Exception('Unable to generate Rust declaration '
                            'for type: {}'.format(type))

    def valname(self, type, value):
        if isinstance(type, FlagsType) or isinstance(type, EnumType):
            if value.name == '2big':
                return 'TOOBIG'
            return value.name.upper()
        else:
            return '{}{}'.format(type.cprefix, value.name).upper()

    def syscallname(self, syscall):
        return syscall.name

    def vardecl(self, type, name, array_need_parens=False):
        return '{}: {}'.format(name, self.typename(type))

    def fieldname(self, name):
        if name == 'type':
            return 'r#type'
        return name


class MarkdownRustNaming(MarkdownNaming, RustNaming):
    def typename(self, type, link=True, **kwargs):
        if link:
            return self.link(type, code=False)
        else:
            return super().typename(type, **kwargs)

    def memname(self, *path):
        name = self.typename(path[0], link=False) + '.'
        name += '.'.join(
            self.variantmem(m) if isinstance(m, VariantMember) else self.
            fieldname(m.name) for m in path[1:])
        return name

    def variantmem(self, member):
        return 'union.' + self.fieldname(member.name)

    def syscallname(self, syscall):
        return RustNaming.syscallname(self, syscall) + '()'

    def kinddesc(self, type):
        if isinstance(type, EnumType):
            return '{} `enum`'.format(self.link(type.int_type))
        elif isinstance(type, AliasType):
            return '= {}'.format(self.link(type.int_type))
        elif isinstance(type, OpaqueType):
            return '`struct({})`'.format(self.typename(type.int_type))
        elif isinstance(type, FlagsType):
            return '{} bitfield'.format(self.link(type.int_type))
        elif isinstance(type, StructType):
            return '`struct`'
        elif isinstance(type, FunctionType):
            return 'function pointer'
        else:
            assert (False)
