# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

import re

from ..abi import *
from ..generator import *
from .c import CNaming

class MarkdownNaming:

    def link(self, *path, code=True):
        name = self.link_name(*path)
        target = self.link_target(*path)
        if code:
            name = '`{}`'.format(name)
        if target is None:
            return name
        return '[{}](#{})'.format(name, target)

    def link_target(self, *path):
        l = self.link_name(*path)
        if l is not None:
            l = l.replace('::', '.')
        return l

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


class MarkdownCNaming(MarkdownNaming, CNaming):

    def typename(self, type, link=True, **kwargs):
        if link and isinstance(type, UserDefinedType):
            return self.link(type, code=False)
        else:
            return super().typename(type, **kwargs)

    def memname(self, *path):
        name = self.typename(path[0], link=False)
        name += '::'
        name += '.'.join(m.name for m in path[1:])
        return name


class MarkdownGenerator(Generator):

    def __init__(self, naming):
        super().__init__(comment_begin='<!--', comment_end='-->')
        self.naming = naming

    def generate_abi(self, abi):
        self.generate_head(abi)
        self.generate_syscalls(abi, abi.syscalls_by_name)
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
        if isinstance(type, IntLikeType):
            extra = ' ({}{})'.format(
                self.naming.typename(type.int_type),
                ' bitfield' if isinstance(type, FlagsType) else '')
        elif isinstance(type, StructType):
            extra = ' (struct)'
        elif isinstance(type, FunctionType):
            extra = ' (function type)'
        else:
            assert(False)
        print('#### {}{}{}\n'.format(
            self.anchor(type), self.naming.typename(type, link=False), extra))
        self.generate_doc(abi, type)
        if isinstance(type, IntLikeType):
            if type.values != []:
                if isinstance(type, OpaqueType) or isinstance(type, AliasType):
                    print('Special values:\n')
                for v in type.values:
                    print('- {}**`{}`**\n'.format(
                        self.anchor(type, v),
                        self.naming.valname(type, v)))
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
                print('- <code>{}</code>\n'.format(
                    self.naming.typename(type.return_type)))
                self.generate_doc(abi, type.return_type.doc, '    ')

    def generate_struct_member(self, abi, m, parents, indent=''):
        print(indent, end='')
        if isinstance(m, SimpleStructMember):
            print('- {}<code>{}</code>\n'.format(
                self.anchor(*parents, m),
                self.naming.vardecl(
                    m.type, '<strong>{}</strong>'.format(m.name))))
            self.generate_doc(abi, m, indent + '    ')
        elif isinstance(m, RangeStructMember):
            print('- {}<code>{}</code> and {}<code>{}</code>\n'.format(
                self.anchor(*parents, m.raw_members[0]),
                self.naming.vardecl(
                    m.raw_members[0].type,
                    '<strong>{}</strong>'.format(m.raw_members[0].name)),
                self.anchor(*parents, m.raw_members[1]),
                self.naming.vardecl(
                    m.raw_members[1].type,
                    '<strong>{}</strong>'.format(m.raw_members[1].name))))
            self.generate_doc(abi, m, indent + '    ')
        elif isinstance(m, VariantStructMember):
            for vm in m.members:
                print('- When `{}` {} {}:\n'.format(
                    m.tag.name,
                    'is' if len(vm.tag_values) == 1 else 'is one of:',
                    ', '.join([self.naming.link(m.tag.type, v)
                               for v in vm.tag_values])))
                if vm.name is None:
                    for mm in vm.type.members:
                        self.generate_struct_member(
                            abi, mm, parents, indent + '  ')
                else:
                    print('  - {}**`{}`**\n'.format(
                        self.anchor(*parents, vm), vm.name))
                    for mm in vm.type.members:
                        self.generate_struct_member(
                            abi, mm, parents + [vm], indent + '    ')

    def generate_syscalls(self, abi, syscalls):
        print('### Syscalls\n')
        for n in sorted(abi.syscalls_by_name):
            print('- {}'.format(self.naming.link(abi.syscalls_by_name[n])))
        print()
        super().generate_syscalls(abi, syscalls)

    def generate_syscall(self, abi, syscall):
        print('#### {}\n'.format(self.naming.syscallname(syscall)))
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
                            raise Exception(
                                'Unable to resolve link: '
                                '{}'.format(match.group(1)))
                        return self.naming.link(*path)
                    line = re.sub(r'\[([\w.]+)\](?!\()', fix_link, line)
                    print('{}{}'.format(indent, line))
            print()

    def anchor(self, *path):
        target = self.naming.link_target(*path)
        if target is None:
            return ''
        return '<a name="{}"></a>'.format(target)
