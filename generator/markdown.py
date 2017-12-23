# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

import re

from .abi import *
from .generator import *
from .c import CNaming
from .rust import RustNaming


class MarkdownNaming:
    def link(self, *path, code=True):
        name = self.link_name(*path)
        target = self.link_target(*path)
        if code:
            name = '`{}`'.format(name)
        else:
            name = _fix_undescores(name)
        if target is None:
            return name
        return '[{}](#{})'.format(name, target)

    def link_target(self, *path):
        for p in path:
            if p.name is None or (isinstance(p, Type)
                                  and not isinstance(p, UserDefinedType)):
                return None
        return '.'.join(p.name for p in path)

    def link_name(self, *path):
        if len(path) == 2 and isinstance(path[1], SpecialValue):
            return self.valname(path[0], path[1])

        elif len(path) == 1 and isinstance(path[0], Syscall):
            return self.syscallname(path[0])

        elif len(path) == 1 and isinstance(path[0], Type):
            return self.typename(path[0], link=False)

        elif len(path) > 1 and isinstance(path[0], StructType):
            return self.memname(*path)

        else:
            return None

    def variantmem(self, member):
        return member.name


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


class MarkdownRustNaming(MarkdownNaming, RustNaming):

    def typename(self, type, link=True, **kwargs):
        if link:
            return self.link(type, code=False)
        else:
            return super().typename(type, **kwargs)

    def memname(self, *path):
        name = self.typename(path[0], link=False) + '.'
        name += '.'.join(
                self.variantmem(m) if isinstance(m, VariantMember) else self.fieldname(m.name)
                for m in path[1:])
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
        elif isinstance(type, AtomicOpaqueType):
            return '`struct(Atomic{})`'.format(self.typename(type.int_type).capitalize())
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

class MarkdownGenerator(Generator):
    def __init__(self, naming):
        super().__init__(comment_begin='<!--', comment_end='-->')
        self.naming = naming

    def generate_abi(self, abi):
        self.generate_head(abi)
        self.generate_syscalls(abi, abi.syscalls)
        self.generate_types(abi, abi.types)
        self.generate_foot(abi)

    def generate_head(self, abi):
        super().generate_head(abi)
        self.generate_doc(abi, abi)

    def generate_types(self, abi, types):
        print('### Types\n')
        for type in sorted(types):
            self.generate_type(abi, types[type])

    def generate_type(self, abi, type):
        extra = self.naming.kinddesc(type)
        print('#### {}`{}` ({})\n'.format(
            self.anchor(type), self.naming.typename(type, link=False), extra))
        self.generate_doc(abi, type)
        if len(type.used_by) > 0 and len(type.used_by) < 10:
            if all('[{}]'.format(x.name) in type.doc for x in type.used_by):
                # Documentation string already refers to all uses.
                pass
            else:
                by = sorted(
                    type.used_by,
                    key=lambda x: ('A' if isinstance(x, Type) else 'B') + x.name
                )
                print('Used by {}.\n'.format(
                    _list('and', [self.naming.link(x) for x in by])))
        if isinstance(type, IntLikeType):
            if type.values != []:
                if isinstance(type, OpaqueType) or isinstance(type, AliasType):
                    print('Special values:\n')
                else:
                    print('Possible values:\n')
                for v in type.values:
                    print('- {}**`{}`**\n'.format(
                        self.anchor(type, v), self.naming.valname(type, v)))
                    self.generate_doc(abi, v, '    ')
        elif isinstance(type, StructType):
            print('Members:\n')
            for m in type.members:
                self.generate_struct_member(abi, m, [type])
        elif isinstance(type, FunctionType):
            if type.parameters.members:
                print('Parameters:\n')
                for m in type.parameters.members:
                    self.generate_struct_member(abi, m, [type])
            if not isinstance(type.return_type, VoidType):
                print('Returns:\n')
                print('- {}\n'.format(self.naming.link(type.return_type)))
                self.generate_doc(abi, type.return_type.doc, '    ')

    def generate_struct_member(
            self, abi, m, parents, indent='', is_variant_member = False):
        print(indent, end='')
        if isinstance(m, SimpleStructMember):
            if is_variant_member:
                name = self.naming.variantmem(m)
            else:
                name = self.naming.fieldname(m.name)
            print('- {}<code>{}</code>\n'.format(
                self.anchor(*(parents + [m])),
                self.naming.vardecl(m.type, '<strong>{}</strong>'.format(
                    _escape(name)))))
            self.generate_doc(abi, m, indent + '    ')
            if m.special_values:
                print('    Possible values:\n')
                for v in m.special_values:
                    print('    - {}\n'.format(self.naming.link(m.type, v)))
                    self.generate_doc(abi, v, indent + '        ')
        elif isinstance(m, RangeStructMember):
            print('- {}<code>{}</code> and {}<code>{}</code>\n'.format(
                self.anchor(*(parents + [m.raw_members[0]])),
                self.naming.vardecl(m.raw_members[0].type,
                                    '<strong>{}</strong>'.format(
                                        _escape(m.raw_members[0].name))),
                self.anchor(*(parents + [m.raw_members[1]])),
                self.naming.vardecl(m.raw_members[1].type,
                                    '<strong>{}</strong>'.format(
                                        _escape(m.raw_members[1].name)))))
            self.generate_doc(abi, m, indent + '    ')
        elif isinstance(m, VariantStructMember):
            for vm in m.members:
                print('- When `{}` is {}:\n'.format(
                    m.tag.name,
                    _list('or', [
                        self.naming.link(m.tag.type, v) for v in vm.tag_values
                    ])))
                if vm.name is None:
                    assert(len(vm.type.members) == 1)
                    mm = vm.type.members[0]
                    self.generate_struct_member(
                        abi, mm, parents, indent + '    ', True)
                else:
                    print('    - {}**`{}`**\n'.format(
                        self.anchor(*(parents + [vm])),
                        self.naming.variantmem(vm)))
                    for mm in vm.type.members:
                        self.generate_struct_member(abi, mm, parents + [vm],
                                                    indent + '        ')

    def generate_syscalls(self, abi, syscalls):
        print('### System calls\n')
        for n in sorted(abi.syscalls):
            print('- {}'.format(self.naming.link(abi.syscalls[n])))
        print()
        super().generate_syscalls(abi, syscalls)

    def generate_syscall(self, abi, syscall):
        print('#### {}`{}`\n'.format(
            self.anchor(syscall), self.naming.syscallname(syscall)))
        self.generate_doc(abi, syscall)

        if syscall.input.members:
            print('Inputs:\n')
            for m in syscall.input.members:
                self.generate_struct_member(abi, m, [syscall])

        if syscall.output.members:
            print('Outputs:\n')
            for m in syscall.output.members:
                self.generate_struct_member(abi, m, [syscall])
        elif syscall.noreturn:
            print('Does not return.\n')

    def generate_doc(self, abi, thing, indent=''):
        if thing.doc != '':
            for line in thing.doc.splitlines():
                if line == '':
                    print()
                else:

                    def fix_link(match):
                        path = abi.resolve_path(match.group(1))
                        if path is None:
                            raise Exception('Unable to resolve link: '
                                            '{}'.format(match.group(1)))
                        return self.naming.link(*path)

                    line = re.sub(r'\[([\w.]+)\](?!\()', fix_link, line)
                    print('{}{}'.format(indent, line))
            print()

    def anchor(self, *path):
        target = self.naming.link_target(*path)
        if target is None:
            return ''
        return '<a href="#{}" name="{}"></a>'.format(target, target)


def _escape(text):
    return text.replace('_', '\\_')


def _fix_undescores(text):
    return _escape(text.replace('\\_', '_'))


def _list(word, items):
    assert (len(items) > 0)
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return '{} {} {}'.format(items[0], word, items[1])
    else:
        return '{}, {} {}'.format(', '.join(items[:-1]), word, items[-1])
