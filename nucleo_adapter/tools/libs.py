import copy, os
from sexpr import parse, find, first, Sym
LIBDIR = os.environ.get('KICAD10_SYMBOL_DIR', '/usr/share/kicad/symbols')
_cache = {}
def _lib(name):
    if name not in _cache:
        _cache[name] = parse(open(os.path.join(LIBDIR, name + '.kicad_sym')).read())
    return _cache[name]

def symbol(lib_id):
    """Flattened symbol definition named lib_id (as embedded in a schematic)."""
    lib, name = lib_id.split(':')
    L = _lib(lib)
    syms = {s[1]: s for s in find(L, 'symbol')}
    s = copy.deepcopy(syms[name])
    ext = first(s, 'extends')
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        props = find(s, 'property')
        pn = {p[1] for p in props}
        body = [x for x in parent[2:] if not (isinstance(x, list) and x[0] == 'property' and x[1] in pn)]
        new = [Sym('symbol'), name]
        # keep parent flags (in_bom etc.) then child props, then parent graphics
        flags = [x for x in body if isinstance(x, list) and x[0] in ('pin_numbers', 'pin_names', 'exclude_from_sim', 'in_bom', 'on_board', 'power')]
        rest = [x for x in body if x not in flags]
        for u in rest:
            if isinstance(u, list) and u[0] == 'symbol':
                u[1] = u[1].replace(ext[1], name)
        s = new + flags + props + rest
    s[1] = lib_id
    return s

def pins(sym):
    """[(number, name, type, x, y, angle, length)] in symbol coordinates (y up), unit 1 / common."""
    out = []
    for u in find(sym, 'symbol'):
        unit = u[1].rsplit('_', 2)
        if unit[-2] not in ('0', '1'):
            continue
        for p in find(u, 'pin'):
            at = first(p, 'at'); ln = first(p, 'length')
            nm = first(p, 'name')[1]; num = first(p, 'number')[1]
            out.append((num, nm, str(p[1]), float(at[1]), float(at[2]), int(float(at[3])), float(ln[1])))
    return out

def bbox(sym):
    xs, ys = [], []
    for u in find(sym, 'symbol'):
        for g in u[2:]:
            if not isinstance(g, list): continue
            if g[0] == 'rectangle':
                for k in ('start', 'end'):
                    a = first(g, k); xs.append(float(a[1])); ys.append(float(a[2]))
            elif g[0] in ('polyline',):
                for xy in find(first(g, 'pts'), 'xy'):
                    xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif g[0] == 'circle':
                c = first(g, 'center'); r = float(first(g, 'radius')[1])
                xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
            elif g[0] == 'pin':
                a = first(g, 'at'); xs.append(float(a[1])); ys.append(float(a[2]))
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (-1, -1, 1, 1)
