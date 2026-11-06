"""Minimal S-expression parser/writer for KiCad files."""
import re
_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')

class Sym(str):
    """Unquoted atom."""

def parse(text):
    pos = 0
    stack = [[]]
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError(text[pos:pos+50])
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            e = stack.pop()
            stack[-1].append(e)
        elif m.group(3):
            s = m.group(3)[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            stack[-1].append(s)
        elif m.group(4):
            stack[-1].append(Sym(m.group(4)))
    return stack[0][0]

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def dump(e, indent=0):
    if isinstance(e, list):
        simple = all(not isinstance(x, list) for x in e)
        if simple:
            return '(' + ' '.join(dump(x) for x in e) + ')'
        out = '(' + ' '.join(dump(x) for x in e if not isinstance(x, list)) if False else None
        parts = []
        head = []
        i = 0
        while i < len(e) and not isinstance(e[i], list):
            head.append(dump(e[i])); i += 1
        s = '(' + ' '.join(head)
        for x in e[i:]:
            s += '\n' + '  ' * (indent + 1) + dump(x, indent + 1) if isinstance(x, list) else ' ' + dump(x)
        return s + '\n' + '  ' * indent + ')'
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, (int, float)):
        return fmt(e)
    return q(e)

def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]

def first(e, key):
    r = find(e, key)
    return r[0] if r else None
