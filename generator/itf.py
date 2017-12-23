# Copyright (c) 2016 Nuxi (https://nuxi.nl/) and contributors.
#
# SPDX-License-Identifier: BSD-2-Clause

# 'Indented Tree Format': An extremely simple text format to describe a tree
# using indentation. Every non-empty line represents a node, with the
# indentation determining the tree structure.
#
# Every node is parsed to a namedtuple with:
#  - text: The original line without surrounding whitespace.
#  - children: The array of child nodes.
#
# A file is parsed to an array of these nodes.
#
# Example:
#
#  Source:
#    foo
#      bar
#      baz
#    test
#    quux
#      1 2 3
#        4 5 6
#
#  Result:
#    [
#      Node(text='foo', children=[
#        Node(text='bar', children=[]),
#        Node(text='baz', children=[])
#      ]),
#      Node(text='test', children=[]),
#      Node(text='quux', children=[
#        Node(text='1 2 3', children=[
#          Node(text='4 5 6', children=[])
#        ])
#      ])
#    ]

from collections import namedtuple

Node = namedtuple('Node', ['text', 'children'])


def read_itf(file_name):

    # The stack holds pairs of indentation and the array of nodes at that
    # level.
    stack = [('', [])]

    # Merge the deepest level of indentation into the children of the last node
    # of the level above it.
    def pop_stack():
        children = stack.pop()[1]
        deepest_nodes = stack[-1][1]
        deepest_nodes[-1].children.extend(children)

    with open(file_name) as f:

        line_num = 0

        for line in f:
            line_num += 1

            # Skip empty and comment lines.
            if line.strip()[:1] in ('', '#'):
                continue

            indent = line[:-len(line.lstrip())]
            previndent = stack[-1][0]
            if len(indent) > len(previndent) and indent.startswith(previndent):
                # We have to go deeper.
                stack.append((indent, []))
            else:
                while indent != previndent:
                    if not previndent.startswith(indent):
                        raise Exception('%s:%d: Invalid indentation' %
                                        (file_name, line_num))
                    pop_stack()
                    previndent = stack[-1][0]

            stack[-1][1].append(Node(line.strip(), []))

    while len(stack) > 1:
        pop_stack()

    return stack[-1][1]
