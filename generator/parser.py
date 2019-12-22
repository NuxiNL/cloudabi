# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .itf import read_itf, Node
from .abi import *


class AbiParser:
    def parse_abi_file(self, file_name):
        return self.parse_abi(read_itf(file_name))

    def parse_abi(self, nodes):
        abi = Abi()

        abi.doc = self.pop_documentation(Node(text='ROOT', children=nodes))

        for node in nodes:
            decl = node.text.split()

            doc = self.pop_documentation(node)

            thing = None

            if decl[0] in int_like_types:
                t = self.parse_int_like_type(abi, decl, node.children)
                abi.types[t.name] = t
                thing = t

            elif decl[0] == 'struct':
                t = self.parse_struct(abi, decl, node.children)
                abi.types[t.name] = t
                thing = t

            elif decl[0] == 'function':
                t = self.parse_function(abi, decl, node.children)
                abi.types[t.name] = t
                thing = t

            elif decl[0] == 'syscall':
                s = self.parse_syscall(abi, decl, node.children)
                abi.syscalls[s.name] = s
                thing = s

            else:
                print('Invalid top level declaration: {}'.format(node.text))

            thing.doc = doc

        for type in abi.types.values():
            type.used_by = {
                t
                for t in abi.types.values()
                if type in getattr(t, 'dependencies', set())
            }

            type.used_by.update({
                s
                for s in abi.syscalls.values()
                if type in getattr(s, 'dependencies', set())
            })

        return abi

    def parse_int_like_type(self, abi, decl, children):
        if len(decl) != 3:
            raise Exception('Invalid {} declaration: {}'.format(
                decl[0], ' '.join(decl)))

        name = decl[2]
        if name in abi.types:
            raise Exception('Duplicate definition of {}'.format(name))

        int_type = decl[1]
        if int_type not in int_types:
            raise Exception('Invalid int type: {}'.format(int_type))

        values = []
        attr = {}

        for node in children:
            value_decl = node.text.split()
            if value_decl[0] == '@cprefix' and len(value_decl) <= 2:
                self.__expect_no_children(node)
                attr['cprefix'] = (value_decl[1]
                                   if len(value_decl) == 2 else '')
            elif len(value_decl) == 2:
                v = SpecialValue(value_decl[1], int(value_decl[0], 0))
                v.doc = self.pop_documentation(node)
                self.__expect_no_children(node)
                values.append(v)
            else:
                raise Exception('Invalid value: {}'.format(child.text))

        return int_like_types[decl[0]](name, int_types[int_type], values,
                                       **attr)

    def parse_struct(self, abi, decl, children):
        if len(decl) != 2:
            raise Exception('Invalid struct declaration: {}'.format(
                decl, ' '.join(decl)))

        name = decl[1]
        if name in abi.types:
            raise Exception('Duplicate definition of {}'.format(name))

        members = self.parse_struct_members(abi, children)

        return StructType(name, members)

    def parse_struct_members(self, abi, children):
        members = []

        for node in children:
            mem_decl = node.text.split()
            mem = None

            if mem_decl[0] == 'variant' and len(mem_decl) == 2:
                tag_member_name = mem_decl[1]
                tag_member = None
                for m in members:
                    if m.name == tag_member_name:
                        if (isinstance(m, SimpleStructMember)
                                and (isinstance(m.type, EnumType)
                                     or isinstance(m.type, AliasType))):
                            tag_member = m
                            break
                        else:
                            raise Exception(
                                'Variant tag ({}) must be an enum or '
                                'an alias type.'.format(m.name))
                if tag_member is None:
                    raise Exception('No such member to use as variant tag: '
                                    '{}.'.format(tag_member_name))
                mem = self.parse_variant(abi, tag_member, node.children)

            elif mem_decl[0] in {'range', 'crange'}:
                doc = self.pop_documentation(node)
                self.__expect_no_children(node)
                if len(mem_decl) < 3:
                    raise Exception('Invalid range: {}'.format(node.text))
                mem_type = self.parse_type(abi, mem_decl[1:-1])
                mem_name = mem_decl[-1]
                mem = RangeStructMember(mem_name, mem_decl[0] == 'crange',
                                        mem_type)
                mem.doc = doc
                mem.raw_members[0].doc = doc

            else:
                mem_name = mem_decl[-1]
                mem_type = self.parse_type(abi, mem_decl[:-1])
                mem_vals = []
                if isinstance(mem_type, IntLikeType):
                    doc = self.pop_documentation(node, optional=True)
                    for n in node.children:
                        vname = n.text
                        val = [v for v in mem_type.values if vname == v.name]
                        if len(val) != 1:
                            raise Exception(
                                'Struct member type {} has no value {}'.format(
                                    mem_type.name, vname))
                        v = SpecialValue(val[0].name, val[0].value)
                        v.doc = self.pop_documentation(n)
                        self.__expect_no_children(n)
                        mem_vals.append(v)
                else:
                    doc = self.pop_documentation(node)
                    self.__expect_no_children(node)
                mem = SimpleStructMember(mem_name, mem_type, mem_vals)
                mem.doc = doc

            members.append(mem)

        return members

    def parse_function(self, abi, decl, children):
        if len(decl) != 2:
            raise Exception('Invalid function declaration: {}'.format(
                ' '.join(decl)))

        name = decl[1]
        if name in abi.types:
            raise Exception('Duplicate definition of {}'.format(name))

        parameters = StructType(None, [])
        return_type = VoidType()

        if len(children) > 0 and children[0].text == 'in':
            param_spec = children.pop(0)
            parameters = StructType(
                None, self.parse_struct_members(abi, param_spec.children))

        if len(children) > 0 and children[0].text == 'out':
            out_spec = children.pop(0)
            doc = self.pop_documentation(out_spec)
            if len(out_spec.children) != 1:
                raise Exception('Expected a single return type in '
                                '`out\' section of function.')
            self.__expect_no_children(out_spec.children[0])
            return_type = (self.parse_type(abi,
                                           out_spec.children[0].text.split()))
            return_type.doc = doc

        return FunctionType(name, parameters, return_type)

    def parse_syscall(self, abi, decl, children):
        if len(decl) != 2:
            raise Exception('Invalid declaration: {}'.format(' '.join(decl)))

        name = decl[1]
        if name in abi.syscalls:
            raise Exception('Duplicate syscall name: {}'.format(name))

        input = StructType('', [])
        output = StructType('', [])
        attr = {}

        if len(children) > 0 and children[0].text == 'in':
            in_spec = children.pop(0)
            input = StructType(
                None, self.parse_struct_members(abi, in_spec.children))

        if len(children) > 0:
            if children[0].text == 'out':
                out_spec = children.pop(0)
                output = StructType(
                    None, self.parse_struct_members(abi, out_spec.children))

            elif children[0].text == 'noreturn':
                noreturn_spec = children.pop(0)
                self.__expect_no_children(noreturn_spec)
                attr['noreturn'] = True

        if children != []:
            raise Exception('Invalid node under syscall: {}'.format(
                children[0].text))

        syscall = Syscall(name, input, output, **attr)

        return syscall

    def parse_variant(self, abi, tag_member, children):
        tag_type = tag_member.type
        members = []

        for node in children:
            tag_value_names = node.text.split()
            tag_values = []
            for vname in tag_value_names:
                val = [v for v in tag_type.values if vname == v.name]
                if len(val) != 1:
                    raise Exception(
                        'Variant tag type {} has no value {}'.format(
                            tag_type.name, vname))
                tag_values.append(val[0])
            if len(node.children) != 1:
                raise Exception(
                    'Excepted a single member in variant member `{}\'.'.format(
                        node.text))
            decl = node.children[0].text.split()
            if len(decl) == 2 and decl[0] == 'struct':
                name = decl[1]
                spec = node.children[0]
            else:
                name = None
                spec = node
            type = StructType(None,
                              self.parse_struct_members(abi, spec.children))
            members.append(VariantMember(name, tag_values, type))

        return VariantStructMember(tag_member, members)

    def parse_type(self, abi, decl):
        if decl == ['void']:
            return VoidType()
        elif len(decl) == 1:
            if decl[0] in int_types:
                return int_types[decl[0]]
            if decl[0] in abi.types:
                return abi.types[decl[0]]
            raise Exception('Unknown type {}'.format(' '.join(decl)))
        elif decl[:1] == ['array'] and len(decl) > 2:
            return ArrayType(int(decl[1], 0), self.parse_type(abi, decl[2:]))
        elif decl[:1] == ['ptr']:
            return PointerType(self.parse_type(abi, decl[1:]))
        elif decl[:1] == ['cptr']:
            return PointerType(self.parse_type(abi, decl[1:]), const=True)
        elif decl[:1] == ['atomic']:
            return AtomicType(self.parse_type(abi, decl[1:]))
        else:
            raise Exception('Invalid type: {}'.format(' '.join(decl)))

    def pop_documentation(self, node, optional=False):
        doc = ''
        while len(
                node.children) > 0 and (node.children[0].text.startswith('| ')
                                        or node.children[0].text == '|'):
            n = node.children.pop(0)
            if n.children != []:
                raise Exception(
                    'Documentation nodes should not have children.')
            doc += n.text[2:] + '\n'
        if doc == '' and not optional:
            import sys
            sys.stderr.write('Missing documentation for: {}\n'.format(
                node.text))
        return doc

    @staticmethod
    def __expect_no_children(node):
        if len(node.children) > 0:
            raise Exception('Unexpected node inside {}: {}'.format(
                node.text, node.children[0].text))
