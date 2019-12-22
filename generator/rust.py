# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE and CONTRIBUTORS files for details.

import re

from .abi import *
from .format import format_list
from .generator import *
from .rust_naming import *


class RustGenerator(Generator):
    def doc_link(self, *path):
        if len(path) == 1 and isinstance(path[0], Syscall):
            return '(fn.{}.html)'.format(path[0].name)
        elif len(path) == 2 and isinstance(path[0], FlagsType) and isinstance(
                path[1], SpecialValue):
            return '(struct.{}.html#associatedconstant.{})'.format(
                self.naming.typename(path[0]),
                self.naming.valname(path[0], path[1]))
        elif len(path) == 2 and isinstance(path[0], EnumType) and isinstance(
                path[1], SpecialValue):
            return '(enum.{}.html#variant.{})'.format(
                self.naming.typename(path[0]),
                self.naming.valname(path[0], path[1]))
        elif len(path) == 2 and isinstance(path[0], OpaqueType) and isinstance(
                path[1], SpecialValue):
            return '(constant.{}.html)'.format(
                self.naming.valname(path[0], path[1]))
        elif len(path) == 1 and (isinstance(path[0], StructType) or isinstance(
                path[0], OpaqueType) or isinstance(path[0], FlagsType)):
            return '(struct.{}.html)'.format(self.naming.typename(path[0]))
        elif len(path) == 2 and isinstance(path[0], StructType) and isinstance(
                path[1], StructMember):
            return '(struct.{}.html#structfield.{})'.format(
                self.naming.typename(path[0]), path[1].name)
        elif len(path) == 3 and (isinstance(path[0], StructType)
                                 and isinstance(path[1], VariantMember)
                                 and isinstance(path[2], StructMember)):
            return '(struct.{}_{}.html#structfield.{})'.format(
                self.naming.typename(path[0]), path[1].name,
                self.naming.fieldname(path[2].name))
        else:
            raise Exception('Unknown link target: {}'.format(repr(path)))

    def print_doc(self, abi, thing, indent='', prefix='///'):
        def make_link(match):
            path = abi.resolve_path(match.group(1))
            assert path is not None
            return '[`{}`]{}'.format(MarkdownRustNaming().link_name(*path),
                                     self.doc_link(*path))

        if hasattr(thing, 'doc'):
            for line in thing.doc.splitlines():
                line = re.sub(r'\[([\w.]+)\](?!\()', make_link, line)
                print((indent + prefix + ' ' + line).rstrip())

    def __init__(self, naming):
        super().__init__(comment_prefix='// ')
        self.naming = naming

    def syscall_params(self, syscall):
        params = []
        for p in syscall.input.raw_members:
            params.append(self.naming.vardecl(p.type, p.name))
        for p in syscall.output.raw_members:
            params.append(
                self.naming.vardecl(OutputPointerType(p.type), p.name))
        return params

    def generate_head(self, abi):
        super().generate_head(abi)
        print('// Appease Rust\'s tidy.')
        print('// ignore-license')
        print('// ignore-tidy-linelength')
        print()
        print('//! **PLEASE NOTE: This entire crate including this')
        print('//! documentation is automatically generated from')
        print(
            '//! [`cloudabi.txt`](https://github.com/NuxiNL/cloudabi/blob/master/cloudabi.txt)**'
        )
        print('//!')
        self.print_doc(abi, abi, '', '//!')
        print()
        print('#![no_std]')
        print('#![allow(non_camel_case_types)]')
        print('''
#[cfg(feature = "bitflags")]
use bitflags::bitflags;

// Minimal implementation of bitflags! in case we can't depend on the bitflags
// crate. Only implements `bits()` and a `from_bits_unchecked()`.
#[cfg(not(feature = "bitflags"))]
macro_rules! bitflags {
  (
    $(#[$attr:meta])*
    pub struct $name:ident: $type:ty {
      $($(#[$const_attr:meta])* const $const:ident = $val:expr;)*
    }
  ) => {
    $(#[$attr])*
    #[derive(Copy, Clone, Eq, PartialEq, Hash, Debug)]
    pub struct $name { bits: $type }
    impl $name {
      $($(#[$const_attr])* pub const $const: $name = $name{ bits: $val };)*
      pub const fn bits(&self) -> $type { self.bits }
      pub const unsafe fn from_bits_unchecked(bits: $type) -> Self { $name{ bits } }
    }
  }
}
''')

    def generate_type(self, abi, type):

        if isinstance(type, FlagsType):
            print('bitflags! {')
            self.print_doc(abi, type, '  ')
            print('  #[repr(C)]')
            print('  pub struct {}: {} {{'.format(
                self.naming.typename(type),
                self.naming.typename(type.int_type)))
            if len(type.values) > 0:
                width = max(
                    len(self.naming.valname(type, v)) for v in type.values)
                val_format = '#0{}x'.format(type.layout.size[0] * 2 + 2)
                for v in type.values:
                    self.print_doc(abi, v, '    ')
                    print('    const {name:{width}} = {val:{val_format}};'.
                          format(name=self.naming.valname(type, v),
                                 width=width,
                                 val=v.value,
                                 val_format=val_format))
            else:
                print('    const DEFAULT = 0;')
            print('  }')
            print('}')

        elif isinstance(type, EnumType):
            self.print_doc(abi, type)
            print('#[repr({})]'.format(self.naming.typename(type.int_type)))
            print('#[derive(Copy, Clone, Eq, PartialEq, Hash, Debug)]')
            print('#[non_exhaustive]')
            print('pub enum {} {{'.format(self.naming.typename(type)))
            if len(type.values) > 0:
                width = max(
                    len(self.naming.valname(type, v)) for v in type.values)
                val_format = '{}d'.format(
                    max(len(str(v.value)) for v in type.values))
                for v in type.values:
                    self.print_doc(abi, v, '  ')
                    print('  {name:{width}} = {val:{val_format}},'.format(
                        name=self.naming.valname(type, v),
                        width=width,
                        val=v.value,
                        val_format=val_format))
            print('}')

        elif isinstance(type, OpaqueType) or isinstance(type, AliasType):
            self.print_doc(abi, type)
            if isinstance(type, OpaqueType):
                print('#[repr(C)]')
                print('#[derive(Copy, Clone, Eq, PartialEq, Hash, Debug)]')
                print('pub struct {}(pub {});'.format(
                    self.naming.typename(type),
                    self.naming.typename(type.int_type)))
                const_format = 'pub const {name:{width}}: {type} = {type}({val:{val_format}});'
            else:
                print('pub type {} = {};'.format(
                    self.naming.typename(type),
                    self.naming.typename(type.int_type)))
                const_format = 'pub const {name:{width}}: {type} = {val:{val_format}};'
            if len(type.values) > 0:
                width = max(
                    len(self.naming.valname(type, v)) for v in type.values)
                if (isinstance(type, FlagsType)
                        or isinstance(type, OpaqueType)):
                    if len(type.values) == 1 and type.values[0].value == 0:
                        val_format = 'd'
                    elif type.int_type.name[0] == 'i':  # Signed
                        val_format = 'd'
                    else:
                        val_format = '#0{}x'.format(type.layout.size[0] * 2 +
                                                    2)
                else:
                    val_width = max(len(str(v.value)) for v in type.values)
                    val_format = '{}d'.format(val_width)
                for v in type.values:
                    self.print_doc(abi, v)
                    print(
                        const_format.format(name=self.naming.valname(type, v),
                                            width=width,
                                            type=self.naming.typename(type),
                                            val=v.value,
                                            val_format=val_format))

        elif isinstance(type, FunctionType):
            self.print_doc(abi, type)
            for param in type.parameters.raw_members:
                print('///')
                print('/// **{}**:'.format(param.name))
                self.print_doc(abi, param)
            print('pub type {} = unsafe extern "C" fn('.format(
                self.naming.typename(type)))
            for param in type.parameters.raw_members:
                print('  {}: {},'.format(param.name,
                                         self.naming.typename(param.type)))
            print(') -> {};'.format(self.naming.typename(type.return_type)))

        elif isinstance(type, StructType):
            structs = [(self.naming.typename(type), type)]
            unions = []

            while len(structs) > 0 or len(unions) > 0:
                for name, struct in structs:
                    self.print_doc(abi, struct)
                    print('#[repr(C)]')
                    print('#[derive(Copy, Clone)]')
                    print('pub struct {} {{'.format(name))
                    for m in struct.members:
                        self.print_doc(abi, m, '  ')
                        if isinstance(m, SimpleStructMember):
                            print('  pub {}: {},'.format(
                                self.naming.fieldname(m.name),
                                self.naming.typename(m.type)))
                        elif isinstance(m, RangeStructMember):
                            print('  pub {}: ({}, {}),'.format(
                                self.naming.fieldname(m.name),
                                self.naming.typename(m.raw_members[0].type),
                                self.naming.typename(m.raw_members[1].type)))
                        elif isinstance(m, VariantStructMember):
                            unions.append((name + '_union', m))
                            print('  pub union: {}_union'.format(name))
                        else:
                            raise Exception(
                                'Unknown struct member: {}'.format(m))
                    print('}')

                structs = []

                # To support multiple unions in the same struct, we should first
                # give them different names.
                assert (len(unions) <= 1)

                for name, union in unions:
                    print('/// A union inside `{}`.'.format(
                        self.naming.typename(type)))
                    print('#[repr(C)]')
                    print('#[derive(Copy, Clone)]')
                    print('pub union {} {{'.format(name))
                    for x in union.members:
                        print('  /// Used when [`{}`]{} is {}.'.format(
                            union.tag.name, self.doc_link(type, union.tag),
                            format_list('or', [
                                '[`{}`]{}'.format(
                                    self.naming.valname(union.tag.type, v),
                                    self.doc_link(union.tag.type, v))
                                for v in x.tag_values
                            ])))
                        if x.name is None:
                            assert (len(x.type.members) == 1)
                            m = x.type.members[0]
                            self.print_doc(abi, m, '  ')
                            print('  pub {}: {},'.format(
                                self.naming.fieldname(m.name),
                                self.naming.typename(m.type)))
                        else:
                            structname = '{}_{}'.format(
                                self.naming.typename(type), x.name)
                            structs.append((structname, x.type))
                            print('  pub {}: {},'.format(
                                self.naming.fieldname(x.name), structname))
                    print('}')

                unions = []

            self.generate_struct_tests(type)

        else:
            raise Exception('Unknown class of type: {}'.format(type))

        print()

    def generate_struct_tests(self, type):
        configs = [(0, 32),
                   (1, 64)] if type.layout.machine_dep else [(0, None)]
        for i, bits in configs:
            print('#[test]')
            if bits is not None:
                print('#[cfg(target_pointer_width = "{}")]'.format(bits))
            print('fn {}_layout_test{}() {{'.format(
                type.name, '_{}'.format(bits) if bits is not None else ''))
            print('  assert_eq!(core::mem::size_of::<{}>(), {});'.format(
                self.naming.typename(type), type.layout.size[i]))
            print('  assert_eq!(core::mem::align_of::<{}>(), {});'.format(
                self.naming.typename(type), type.layout.align[i]))
            mut = ''
            if any(isinstance(m, VariantStructMember) for m in type.members):
                mut = 'mut '
            print('  let {}obj = '.format(mut), end='')
            self.generate_test_value(type, '  ')
            print(';')
            print('  let base = &obj as *const _ as usize;')
            self.generate_offset_asserts(type, type.members, i)
            print('}')

    def generate_test_value(self, type, indent='', typename=None):
        if typename is None:
            typename = self.naming.typename(type)

        if isinstance(type, VoidType):
            print('()', end='')

        elif isinstance(type, IntType) or isinstance(type, AliasType):
            print('0', end='')

        elif isinstance(type, PointerType):
            if isinstance(type.target_type, FunctionType):
                print('{{ extern "C" fn f({}) -> {} {{'.format(
                    ', '.join('_: {}'.format(self.naming.typename(t.type))
                              for t in type.target_type.parameters.members),
                    self.naming.typename(type.target_type.return_type),
                ),
                      end='')
                if not isinstance(type.target_type.return_type, VoidType):
                    print(' ', end='')
                    self.generate_test_value(type.target_type.return_type,
                                             indent + '  ')
                    print(' ', end='')
                print('} f }', end='')
            else:
                print('0 as {}'.format(typename), end='')

        elif isinstance(type, FlagsType) or isinstance(type, EnumType):
            if len(type.values) > 0:
                valname = self.naming.valname(type, type.values[0])
            else:
                valname = 'DEFAULT'
            print('{}::{}'.format(typename, valname), end='')

        elif isinstance(type, OpaqueType):
            print('{}(0)'.format(typename), end='')

        elif isinstance(type, ArrayType):
            print('[', end='')
            self.generate_test_value(type.element_type, indent + '  ')
            print('; {}]'.format(type.count), end='')

        elif isinstance(type, StructType):
            print('{} {{'.format(typename))
            for m in type.members:
                if isinstance(m, SimpleStructMember):
                    print('{}  {}: '.format(indent,
                                            self.naming.fieldname(m.name)),
                          end='')
                    self.generate_test_value(m.type, indent + '  ')
                elif isinstance(m, RangeStructMember):
                    print('{}  {}: (0 as *{} _, 0)'.format(
                        indent,
                        self.naming.fieldname(m.name),
                        'const' if m.const else 'mut',
                    ),
                          end='')
                else:
                    print('{}  union: '.format(indent), end='')
                    self.generate_test_union_value(type, m.members[0],
                                                   indent + '  ')
                print(',')
            print('{}}}'.format(indent), end='')

        else:
            raise Exception('Unknown class of type: {}'.format(type))

    def generate_test_union_value(self, type, variant, indent=''):
        typename = self.naming.typename(type)
        unionname = '{}_union'.format(typename)
        if variant.name is None:
            self.generate_test_value(variant.type, indent, typename=unionname)
        else:
            print('{} {{'.format(unionname))
            memname = self.naming.fieldname(variant.name)
            print('{}  {}: '.format(indent, memname), end='')
            self.generate_test_value(variant.type,
                                     indent + '  ',
                                     typename='{}_{}'.format(
                                         typename, memname))
            print(',')
            print('{}}}'.format(indent), end='')

    def generate_offset_asserts(self,
                                type,
                                members,
                                machine_index,
                                prefix='',
                                offset=0,
                                indent='  '):
        for m in members:
            if isinstance(m, VariantMember):
                mprefix = prefix + 'union.'
                if m.name is None:
                    fieldname = self.naming.fieldname(m.type.members[0].name)
                    fieldtype = m.type.members[0].type
                    fieldtypename = None
                else:
                    fieldname = self.naming.fieldname(m.name)
                    fieldtype = self.naming.fieldname(m.type)
                    fieldtypename = '{}_{}'.format(
                        self.naming.typename(type),
                        self.naming.fieldname(m.name))
                    mprefix += fieldname + '.'
                print('  obj.{}union.{} = '.format(prefix, fieldname), end='')
                self.generate_test_value(fieldtype,
                                         indent='  ',
                                         typename=fieldtypename)
                print(';')
                print('  unsafe {')
                self.generate_offset_asserts(m.type, m.type.members,
                                             machine_index, mprefix, offset,
                                             indent + '  ')
                print('  }')
            elif isinstance(m, RangeStructMember):
                for i, raw_m in enumerate(m.raw_members):
                    moffset = offset + raw_m.offset[machine_index]
                    self.generate_offset_assert(
                        prefix + self.naming.fieldname(m.name) + '.' + str(i),
                        moffset, indent)
            elif m.offset is not None:
                moffset = offset + m.offset[machine_index]
                if isinstance(m, VariantStructMember):
                    self.generate_offset_asserts(type, m.members,
                                                 machine_index, prefix,
                                                 moffset)
                else:
                    self.generate_offset_assert(
                        prefix + self.naming.fieldname(m.name), moffset,
                        indent)

    def generate_offset_assert(self, member_name, offset, indent=''):
        print('{}assert_eq!(&obj.{} as *const _ as usize - base, {});'.format(
            indent, member_name, offset))

    def generate_syscalls(self, abi, syscalls):
        print('/// The table with pointers to all syscall implementations.')
        print('#[allow(improper_ctypes)]')
        print('extern "C" {')
        for s in sorted(abi.syscalls):
            self.generate_syscall_declaration(abi, abi.syscalls[s])
        print('}')
        for s in sorted(abi.syscalls):
            print()
            self.generate_syscall_wrapper(abi, abi.syscalls[s])

    def generate_syscall_declaration(self, abi, syscall):
        if syscall.noreturn:
            return_type = '!'
        else:
            return_type = self.naming.typename(abi.types['errno'])
        params = []
        for p in syscall.input.raw_members:
            params.append('_: ' + self.naming.typename(p.type))
        for p in syscall.output.raw_members:
            params.append('_: ' +
                          self.naming.typename(OutputPointerType(p.type)))
        print('  fn cloudabi_sys_{}({}) -> {};'.format(syscall.name,
                                                       ', '.join(params),
                                                       return_type))

    def generate_syscall_wrapper(self, abi, syscall):
        self.print_doc(abi, syscall)

        if syscall.input.members or syscall.output.members:
            print('///\n/// ## Parameters')
        for p in syscall.input.members + syscall.output.members:
            print('///\n/// **{}**:'.format(p.name))
            self.print_doc(abi, p)
            if getattr(p, 'special_values', None):
                print('/// Possible values:\n///')
                for val in p.special_values:
                    print('///   - [`{}`]{}:'.format(
                        self.naming.valname(p.type, val),
                        self.doc_link(p.type, val)))
                    self.print_doc(abi, val, '', '///    ')

        if syscall.noreturn:
            return_type = '!'
        else:
            return_type = self.naming.typename(abi.types['errno'])

        params = []
        for p in syscall.input.members:
            params.append(self.syscall_param(p))
        for p in syscall.output.members:
            params.append(self.syscall_param(p, True))

        print('#[inline]')
        print('pub unsafe fn {}({}) -> {} {{'.format(syscall.name,
                                                     ', '.join(params),
                                                     return_type))

        args = []
        for p in syscall.input.members:
            n = p.name + '_'
            if isinstance(p, RangeStructMember):
                cast = ''
                if isinstance(p.target_type, VoidType):
                    cast = ' as *const ()' if p.const else ' as *mut ()'
                args.append(n + ('.as_ptr()' if p.const else '.as_mut_ptr()') +
                            cast)
                args.append(n + '.len()')
            else:
                args.append(n)
        for p in syscall.output.members:
            assert not isinstance(p, RangeStructMember)
            args.append(p.name + '_')

        print('  cloudabi_sys_{}({})'.format(syscall.name, ', '.join(args)))
        print('}')

    def syscall_param(self, p, output=False):
        name = p.name + '_'
        if isinstance(p, RangeStructMember):
            return '{}: {}&{}[{}]'.format(
                name, '*mut ' if output else '', '' if p.const else 'mut ',
                'u8' if isinstance(p.target_type, VoidType) else
                self.naming.typename(p.target_type))
        else:
            return '{}: {}{}'.format(name, '*mut ' if output else '',
                                     self.naming.typename(p.type))
