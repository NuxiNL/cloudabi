from .abi import *
from .markdown_naming import *


class CNaming:
    def __init__(self,
                 prefix,
                 md_prefix=None,
                 c11=True,
                 syscall_prefix=None,
                 pointer_prefix=''):
        self.prefix = prefix
        self.md_prefix = md_prefix
        self.c11 = c11
        self.syscall_prefix = syscall_prefix
        self.pointer_prefix = pointer_prefix

    def typename(self, type):
        if isinstance(type, VoidType):
            return 'void'
        elif isinstance(type, IntType):
            if type.name == 'char':
                return 'char'
            return '{}_t'.format(type.name)
        elif isinstance(type, UserDefinedType):
            prefix = self.prefix
            if self.md_prefix is not None and type.layout.machine_dep:
                prefix = self.md_prefix
            return '{}{}_t'.format(prefix, type.name)
        elif isinstance(type, AtomicType):
            if self.c11:
                return '_Atomic({})'.format(self.typename(type.target_type))
            else:
                return self.typename(type.target_type)
        elif isinstance(type, PointerType) or isinstance(type, ArrayType):
            return self.vardecl(type, '')
        else:
            raise Exception('Unable to generate C declaration '
                            'for type: {}'.format(type))

    def valname(self, type, value):
        return '{}{}{}'.format(self.prefix, type.cprefix, value.name).upper()

    def syscallname(self, syscall):
        if self.syscall_prefix is not None:
            prefix = self.syscall_prefix
        else:
            prefix = self.prefix
            if self.md_prefix is not None and syscall.machine_dep:
                prefix = self.md_prefix
            prefix += 'sys_'
        return '{}{}'.format(prefix, syscall.name)

    def vardecl(self, type, name, array_need_parens=False):
        if isinstance(type, OutputPointerType):
            return self.vardecl(type.target_type,
                                '*{}'.format(name),
                                array_need_parens=True)
        elif isinstance(type, PointerType):
            decl = self.vardecl(type.target_type,
                                '{}*{}'.format(self.pointer_prefix, name),
                                array_need_parens=True)
            if type.const:
                decl = 'const ' + decl
            return decl
        elif isinstance(type, ArrayType):
            if array_need_parens:
                name = '({})'.format(name)
            return self.vardecl(type.element_type,
                                '{}[{}]'.format(name, type.count))
        else:
            return '{} {}'.format(self.typename(type), name)

    def fieldname(self, name):
        return name


class MarkdownCNaming(MarkdownNaming, CNaming):
    def typename(self, type, link=True, **kwargs):
        if link:
            return self.link(type, code=False)
        else:
            return super().typename(type, **kwargs)

    def memname(self, *path):
        name = self.typename(path[0], link=False)
        name += '::'
        name += '.'.join(m.name for m in path[1:])
        return name

    def syscallname(self, syscall):
        return CNaming.syscallname(self, syscall) + '()'

    def kinddesc(self, type):
        if isinstance(type, IntLikeType):
            return '{}{}'.format(
                self.link(type.int_type),
                ' bitfield' if isinstance(type, FlagsType) else '')
        elif isinstance(type, StructType):
            return '`struct`'
        elif isinstance(type, FunctionType):
            return 'function type'
        else:
            assert (False)
