# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause


class Layout:
    def __init__(self, size, align=None, machine_dep=None):
        if align is None:
            align = size
        if not isinstance(size, tuple):
            size = (size, size)
        if not isinstance(align, tuple):
            align = (align, align)
        self.size = size
        self.align = align
        if machine_dep is None:
            machine_dep = size[0] != size[1] or align[0] != align[1]
        self.machine_dep = machine_dep

    @staticmethod
    def struct(members):
        if members == []:
            return Layout(1, 1, False)

        if any(m.layout is None for m in members):
            return None

        align = (max(m.layout.align[0] for m in members),
                 max(m.layout.align[1] for m in members))

        offset = (0, 0)
        for m in members:
            m.offset = (_align(offset[0], m.layout.align[0]),
                        _align(offset[1], m.layout.align[1]))
            offset = (m.offset[0] + m.layout.size[0],
                      m.offset[1] + m.layout.size[1])

        size = (_align(offset[0], align[0]), _align(offset[1], align[1]))

        machine_dep = any(m.layout.machine_dep for m in members)

        return Layout(size, align, machine_dep)

    @staticmethod
    def array(type, count):
        if count == 0:
            return Layout(0, 1, False)

        if type.layout is None:
            return None

        size = (type.layout.size[0] * count, type.layout.size[1] * count)

        return Layout(size, type.layout.align, type.layout.machine_dep)

    @staticmethod
    def union(members):
        if members == []:
            return Layout(1, 1, False)

        if any(m.layout is None for m in members):
            return None

        size = (max(m.layout.size[0]
                    for m in members), max(m.layout.size[1] for m in members))

        align = (max(m.layout.align[0] for m in members),
                 max(m.layout.align[1] for m in members))

        machine_dep = any(m.layout.machine_dep for m in members)

        return Layout(size, align, machine_dep)

    def fits_in(self, other_layout):
        return (self.size[0] <= other_layout.size[0]
                and self.size[1] <= other_layout.size[1])


def _align(size, align):
    misalignment = size % align
    if misalignment == 0:
        return size
    else:
        return size + align - misalignment
