# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

import re

from ..abi import *
from ..generator import *


class MarkdownGenerator(Generator):

    def __init__(self, title, naming):
        super().__init__(comment_begin='<!--', comment_end='-->')
        self.title = title
        self.naming = naming

    def generate_head(self, abi):
        super().generate_head(abi)
        print('# {}\n'.format(self.title))
        self.generate_toc(abi)

    def generate_toc(self, abi):
        print('## Contents\n')
        print('**Types**\n')
        for n in sorted(abi.types):
            print(self.link(abi.types[n]))
        print()
        print('**Syscalls**\n')
        for n in sorted(abi.syscalls_by_name):
            print(self.link(abi.syscalls_by_name[n]))
        print()

    def generate_types(self, abi, types):
        print('## Types\n')
        super().generate_types(abi, types)

    def generate_type(self, abi, type):
        print('### {}\n'.format(self.naming.typename(type)))
        self.generate_doc(abi, type)
        if isinstance(type, IntLikeType):
            if type.values != []:
                if isinstance(type, OpaqueType) or isinstance(type, AliasType):
                    print('Special values:\n')
                for v in type.values:
                    print('- {}`{}`\n'.format(
                        self.anchor(type, v),
                        self.naming.valname(type, v)))
                    self.generate_doc(abi, v, '    ')
        elif isinstance(type, StructType):
            print('Members:\n')
            for m in type.members:
                self.generate_struct_member(abi, m, [type])
        elif isinstance(type, FunctionType):
            pass
        else:
            assert(False)

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
            self.generate_doc(abi, m)
            for vm in m.members:
                print('- When `{}` {} {}:\n'.format(
                    m.tag.name,
                    'is' if len(vm.tag_values) == 1 else 'is one of:',
                    ', '.join([self.link(m.tag.type, v)
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
        print('## Syscalls\n')
        super().generate_syscalls(abi, syscalls)

    def generate_syscall(self, abi, syscall):
        print('### {}\n'.format(self.naming.syscallname(syscall)))
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
                        return self.link(*path)
                    line = re.sub(r'\[([\w.]+)\](?!\()', fix_link, line)
                    print('{}{}'.format(indent, line))
            print()

    def link_name(self, *path):
        if len(path) == 2 and isinstance(path[1], SpecialValue):
            name = self.naming.valname(path[0], path[1])

        elif len(path) == 1 and isinstance(path[0], Syscall):
            name = self.naming.syscallname(path[0])

        elif len(path) == 1 and isinstance(path[0], Type):
            name = self.naming.typename(path[0])

        elif len(path) > 1 and isinstance(path[0], StructType):
            name = self.naming.memname(path[0], *path[1:])

        else:
            raise Exception('Unable to generate link to: {}'.format(path))

        return name

    def link(self, *path):
        name = self.link_name(*path)
        return '[`{}`](#{})'.format(name, name)

    def anchor(self, *path):
        if len(path) > 1 and isinstance(path[0], Syscall):
            return ''
        name = self.link_name(*path)
        return '<a name="{}"></a>'.format(name)
