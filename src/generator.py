# Copyright (c) 2016 Nuxi, https://nuxi.nl/
#
# This file is distributed under a 2-clause BSD license.
# See the LICENSE file for details.

from .abi import *


class Generator:

    def generate_type(self, type):
        pass

    def generate_syscall(self, syscall):
        pass

    def generate_types(self, types):
        first_pass = True
        generate_now = [name for name in sorted(types)]
        generate_later = []
        generated = set()

        while generate_now != []:
            for type_name in generate_now:
                type = types[type_name]

                if (not (getattr(type, 'dependencies', set()) <= generated) or
                        (first_pass and not isinstance(type, IntLikeType))):
                    generate_later.append(type_name)
                else:
                    self.generate_type(type)
                    generated.add(type_name)

            generate_now = generate_later
            generate_later = []
            first_pass = False

        assert(generated == {n for n in types})

    def generate_syscalls(self, syscalls):
        for syscall in sorted(syscalls):
            self.generate_syscall(syscalls[syscall])

    def generate_abi(self, abi):
        self.generate_types(abi.types)
        self.generate_syscalls(abi.syscalls_by_number)
