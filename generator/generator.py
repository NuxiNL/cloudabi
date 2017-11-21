# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

from .abi import *


class Generator:
    def __init__(self, comment_prefix='', comment_begin=None,
                 comment_end=None):
        self.comment_begin = comment_begin
        self.comment_prefix = comment_prefix
        self.comment_end = comment_end

    def generate_head(self, abi):
        import os
        license = os.path.dirname(__file__) + '/../parts/head'
        if self.comment_begin is not None:
            print(self.comment_begin)
        with open(license) as f:
            for line in f:
                print((self.comment_prefix + line).rstrip())
        if self.comment_end is not None:
            print(self.comment_end)
        print()

    def generate_foot(self, abi):
        pass

    def generate_type(self, abi, type):
        pass

    def generate_syscall(self, abi, syscall):
        pass

    def generate_types(self, abi, types):
        first_pass = True
        generate_now = [types[name] for name in sorted(types)]
        generate_later = []
        generated = set()

        while generate_now != []:
            for type in generate_now:

                if (not (getattr(type, 'dependencies', set()) <= generated)
                        or (first_pass and not isinstance(type, IntLikeType))):
                    generate_later.append(type)
                else:
                    self.generate_type(abi, type)
                    generated.add(type)

            generate_now = generate_later
            generate_later = []
            first_pass = False

        assert (generated == set(types.values()))

    def generate_syscalls(self, abi, syscalls):
        for syscall in sorted(syscalls):
            self.generate_syscall(abi, syscalls[syscall])

    def generate_abi(self, abi):
        self.generate_head(abi)
        self.generate_types(abi, abi.types)
        self.generate_syscalls(abi, abi.syscalls)
        self.generate_foot(abi)
