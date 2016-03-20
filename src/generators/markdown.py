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

    def generate_head(self):
        super().generate_head()
        print('# {}\n'.format(self.title))

    def generate_types(self, types):
        print('## Types\n')
        super().generate_types(types)

    def generate_type(self, type):
        print('### {}\n'.format(self.naming.typename(type)))
        self.generate_doc(type)
        if isinstance(type, IntLikeType):
            if type.values != []:
                if isinstance(type, OpaqueType) or isinstance(type, AliasType):
                    print('Special values:\n')
                for v in type.values:
                    print('- `{}`\n'.format(self.naming.valname(type, v)))
                    self.generate_doc(v, '    ')
        elif isinstance(type, StructType):
            print('Members:\n')
            for m in type.members:
                self.generate_struct_member(m)
        elif isinstance(type, FunctionType):
            pass
        else:
            assert(False)

    def generate_struct_member(self, m, indent=''):
        print(indent, end='')
        if isinstance(m, SimpleStructMember):
            print('- <code>{}</code>\n'.format(
                self.naming.vardecl(
                    m.type, '<strong>{}</strong>'.format(m.name))))
            self.generate_doc(m, indent + '    ')
        elif isinstance(m, RangeStructMember):
            print('- <code>{}</code> and <code>{}</code>\n'.format(
                self.naming.vardecl(
                    m.raw_members[0].type,
                    '<strong>{}</strong>'.format(m.raw_members[0].name)),
                self.naming.vardecl(
                    m.raw_members[1].type,
                    '<strong>{}</strong>'.format(m.raw_members[1].name))))
            self.generate_doc(m, indent + '    ')
        elif isinstance(m, VariantStructMember):
            self.generate_doc(m)
            for vm in m.members:
                print('- When `{}` {} {}:\n'.format(
                    m.tag.name,
                    'is' if len(vm.tag_values) == 1 else 'is one of:',
                    ', '.join(['`{}`'.format(
                            self.naming.valname(m.tag.type, v))
                            for v in vm.tag_values])))
                if vm.name is None:
                    for mm in vm.type.members:
                        self.generate_struct_member(mm, indent + '  ')
                else:
                    print('  - `{}`\n'.format(vm.name))
                    for mm in vm.type.members:
                        self.generate_struct_member(mm, indent + '    ')

    def generate_syscalls(self, syscalls):
        print('## Syscalls\n')
        super().generate_syscalls(syscalls)

    def generate_syscall(self, syscall):
        print('### {}\n'.format(self.naming.syscallname(syscall)))
        self.generate_doc(syscall)

        print('Inputs:\n')
        if syscall.input.members == []:
            print('- *None*\n')
        else:
            for m in syscall.input.members:
                self.generate_struct_member(m)

        print('Outputs:\n')
        if syscall.output.members == []:
            if syscall.noreturn:
                print('- *Does not return*\n')
            else:
                print('- *None*\n')
        else:
            for m in syscall.output.members:
                self.generate_struct_member(m)

    def generate_doc(self, thing, indent=''):
        if thing.doc != '':
            for line in thing.doc.splitlines():
                if line == '':
                    print()
                else:
                    line = re.sub(r'\[([\w.]+)\](?!\()', r'[\1](#\1)', line)
                    print('{}{}'.format(indent, line))
            print()
