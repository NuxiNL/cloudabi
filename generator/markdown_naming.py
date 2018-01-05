from .abi import *


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


def _fix_undescores(text):
    return text.replace('\\_', '_').replace('_', '\\_')
