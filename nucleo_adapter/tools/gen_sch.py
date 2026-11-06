"""Write the KiCad 7 schematic of the Nucleo adapter from design.py."""
import os
import sys
import uuid as uuidlib

from sexpr import Sym as S, dump, find, first
import libs
import design as D

PROJECT = 'nucleo_adapter'
DATE = '2026-11-06'
OUT = sys.argv[1]
G = 1.27
STUB = 2.54
NS = uuidlib.UUID('6f1c8a52-4f37-4c55-9a43-6b1d2f0c7e11')


def uid(*key):
    return str(uuidlib.uuid5(NS, '/'.join(map(str, key))))


def snap(v):
    return round(round(v / G) * G, 4)


def rot_vec(r, x, y):
    """Rotate a screen vector (y down) counter-clockwise on screen by r degrees."""
    for _ in range((r // 90) % 4):
        x, y = y, -x
    return x, y


OUTWARD = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}


def pin_geom(p, r):
    """Pin connection offset and outward direction on screen for a symbol rotated by r."""
    num, name, typ, x, y, ang, ln = p
    ox, oy = rot_vec(r, x, -y)
    dx, dy = rot_vec(r, *OUTWARD[ang])
    return (ox, oy), (dx, dy)


def is_power(net):
    return net in D.POWER_NETS


def power_lib(net):
    return 'power:' + net


def text_len(s):
    return 1.0 * len(s) + 1.5


ROOT_UUID = uid('root')
SHEET_UUID = {s['name']: uid('sheet', s['name']) for s in D.SHEETS}

# nets used per sheet (signals only) -> hierarchical labels where a net spans sheets
nucleo_sym = libs.symbol('MCU_Module:NUCLEO144-H743ZI')
for s in D.SHEETS:
    for p in s['parts']:
        if p['pins'] == 'nucleo':
            p['pins'] = {}
            for pp in libs.pins(nucleo_sym):
                base = pp[1].split('/')[-1]
                p['pins'][pp[0]] = D.NUCLEO_MAP.get(base, D.NC)
net_sheets = {}
for s in D.SHEETS:
    for p in s['parts']:
        for n in p['pins'].values():
            if n and not is_power(n):
                net_sheets.setdefault(n, set()).add(s['name'])
HIER = {n for n, ss in net_sheets.items() if len(ss) > 1}


class Sheet:
    def __init__(self, name, portrait=False):
        self.name = name
        self.items = []
        self.libsyms = {}
        self.portrait = portrait
        self.pwr = 0
        self.hier = {}

    def lib(self, lib_id):
        if lib_id not in self.libsyms:
            self.libsyms[lib_id] = libs.symbol(lib_id)
        return self.libsyms[lib_id]

    def path(self):
        return '/' + ROOT_UUID + ('' if self.name == 'root' else '/' + SHEET_UUID[self.name])

    def wire(self, a, b):
        self.items.append([S('wire'), [S('pts'), [S('xy'), a[0], a[1]], [S('xy'), b[0], b[1]]],
                           [S('stroke'), [S('width'), 0], [S('type'), S('default')]],
                           [S('uuid'), uid(self.name, 'w', a, b)]])

    def symbol(self, lib_id, ref, value, at, r, fp='', pins=(), ref_at=None, val_at=None, hide_ref=False,
               hide_val=False, extra=(), just='left'):
        sym = self.lib(lib_id)
        u = uid(self.name, 'sym', ref)
        ra = ref_at or (at[0] + 2.54, at[1] - 1.27)
        va = val_at or (at[0] + 2.54, at[1] + 1.27)

        fang = 90 if r in (90, 270) else 0
        flip = {'left': 'right', 'right': 'left'}

        def prop(k, v, pos, hide=False, just='left'):
            eff = [S('effects'), [S('font'), [S('size'), 1.27, 1.27]]]
            if just:
                eff.append([S('justify'), S(flip[just] if r in (90, 180) else just)])
            pr = [S('property'), k, v, [S('at'), round(pos[0], 4), round(pos[1], 4), fang]]
            if hide:
                pr.append([S('hide'), S('yes')])
            return pr + [eff]

        flag = {k: (first(sym, k) or [None, S('yes')])[1] for k in ('in_bom', 'on_board')}
        e = [S('symbol'), [S('lib_id'), lib_id], [S('at'), at[0], at[1], r], [S('unit'), 1],
             [S('in_bom'), S(flag['in_bom'])], [S('on_board'), S(flag['on_board'])], [S('dnp'), S('no')],
             [S('uuid'), u],
             prop('Reference', ref, ra, hide_ref, just),
             prop('Value', value, va, hide_val, just),
             prop('Footprint', fp, at, True, None),
             prop('Datasheet', '~', at, True, None)]
        e += list(extra)
        for pp in libs.pins(sym):
            e.append([S('pin'), pp[0], [S('uuid'), uid(self.name, 'pin', ref, pp[0])]])
        e.append([S('instances'), [S('project'), PROJECT,
                                   [S('path'), self.path(), [S('reference'), ref], [S('unit'), 1]]]])
        self.items.append(e)
        return u

    def power(self, net, at, outward):
        """Power symbol whose graphic points along outward."""
        self.pwr += 1
        lib_id = power_lib(net)
        natural = (0, 1) if net in D.GROUNDS else (0, -1)
        r = next(r for r in (0, 90, 180, 270) if rot_vec(r, *natural) == outward)
        ref = f'#PWR{self.name[:3].upper()}{self.pwr:03d}'
        if outward[0] == 0:
            off = (0, 3.81 * outward[1])
            just = None
        else:
            off = (3.3 * outward[0], 0)
            just = 'right' if outward[0] < 0 else 'left'
        self.symbol(lib_id, ref, net, at, r, hide_ref=True,
                    val_at=(at[0] + off[0], at[1] + off[1]), just=just)

    def label(self, net, at, outward, hier=False):
        ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[outward]
        just = 'left' if ang in (0, 90) else 'right'
        eff = [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S(just)]]
        if hier:
            self.items.append([S('hierarchical_label'), net, [S('shape'), S('passive')],
                               [S('at'), at[0], at[1], ang], eff, [S('uuid'), uid(self.name, 'hl', net, at)]])
            self.hier[net] = 'passive'
        else:
            self.items.append([S('label'), net, [S('at'), at[0], at[1], ang], eff,
                               [S('uuid'), uid(self.name, 'l', net, at)]])

    def junction(self, at):
        self.items.append([S('junction'), [S('at'), at[0], at[1]], [S('diameter'), 0],
                           [S('color'), 0, 0, 0, 0], [S('uuid'), uid(self.name, 'j', at)]])

    def noconnect(self, at):
        self.items.append([S('no_connect'), [S('at'), at[0], at[1]], [S('uuid'), uid(self.name, 'nc', at)]])

    def text(self, s, at, size=1.27, bold=False):
        font = [S('font'), [S('size'), size, size]]
        if bold:
            font += [[S('thickness'), 0.4], [S('bold'), S('yes')]]
        self.items.append([S('text'), s, [S('at'), at[0], at[1], 0],
                           [S('effects'), font, [S('justify'), S('left'), S('bottom')]],
                           [S('uuid'), uid(self.name, 'txt', s[:40], at)]])

    def connect(self, net, pin_at, outward, stub=STUB):
        """Stub from the pin outward, ending in a power symbol, label or no-connect."""
        if net is D.NC:
            self.noconnect(pin_at)
            return
        end = (round(pin_at[0] + outward[0] * stub, 4), round(pin_at[1] + outward[1] * stub, 4))
        self.wire(pin_at, end)
        if is_power(net):
            self.power(net, end, outward)
        else:
            self.label(net, end, outward, hier=net in HIER)

    def write(self, title, notes_extra=()):
        paper = [S('paper'), 'A4'] + ([S('portrait')] if self.portrait else [])
        tb = [S('title_block'), [S('title'), title], [S('date'), DATE], [S('rev'), 'A'],
              [S('company'), 'UNIMOC'],
              [S('comment'), 1, 'Nucleo adapter: NUCLEO-H743ZI to the legacy 4850 power board'],
              [S('comment'), 2, 'Generated draft, check before layout']]
        e = [S('kicad_sch'), [S('version'), 20260306], [S('generator'), 'eeschema'], [S('generator_version'), '10.0'],
             [S('uuid'), ROOT_UUID if self.name == 'root' else SHEET_UUID[self.name]], paper, tb,
             [S('lib_symbols')] + list(self.libsyms.values())]
        e += self.items
        if self.name == 'root':
            e.append([S('sheet_instances'), [S('path'), '/', [S('page'), '1']]])
        with open(os.path.join(OUT, (PROJECT if self.name == 'root' else self.name) + '.kicad_sch'), 'w') as f:
            f.write(dump(e) + '\n')


# ------------------------------------------------------------------ placement

def orient(sh, part):
    """Choose a rotation: grounds point down, supplies up, else pin 1 to the left."""
    sym = sh.lib(part['lib'])
    ps = libs.pins(sym)
    if part['lib'] == 'power:PWR_FLAG':
        return 0 if part['pins']['1'] in D.GROUNDS else 180
    if len(ps) != 2:
        return part.get('rot', 0)
    best, score = 0, -99
    for r in (0, 90, 180, 270):
        s = 0
        for p in ps:
            net = part['pins'][p[0]]
            _, d = pin_geom(p, r)
            if net in D.GROUNDS:
                s += 4 if d == (0, 1) else -4
            elif is_power(net):
                s += 3 if d == (0, -1) else -1
        nets = list(part['pins'].values())
        if not any(is_power(n) for n in nets):
            _, d1 = pin_geom([p for p in ps if p[0] == '1'][0], r)
            s += 2 if d1 == (-1, 0) else 0
        if s > score:
            best, score = r, s
    return best


def extent(sh, part, r):
    """Bounding box (screen, relative to the anchor) including stubs and labels."""
    sym = sh.lib(part['lib'])
    x0, y0, x1, y1 = libs.bbox(sym)
    corners = [rot_vec(r, x, -y) for x in (x0, x1) for y in (y0, y1)]
    bx0 = min(c[0] for c in corners); bx1 = max(c[0] for c in corners)
    by0 = min(c[1] for c in corners); by1 = max(c[1] for c in corners)
    for p in libs.pins(sym):
        net = part['pins'][p[0]]
        (ox, oy), (dx, dy) = pin_geom(p, r)
        ln = STUB + (5.5 if net is not D.NC and is_power(net) else (text_len(net) + (2 if net in HIER else 0) if net else 0))
        ex, ey = ox + dx * ln, oy + dy * ln
        bx0, bx1 = min(bx0, ex - 1.5), max(bx1, ex + 1.5)
        by0, by1 = min(by0, ey - 1.5), max(by1, ey + 1.5)
    # reference / value text to the right
    w = max(text_len(part['ref']), text_len(part['value'])) + 3
    if all(pin_geom(p, r)[1][1] == 0 for p in libs.pins(sym)) and len(libs.pins(sym)) == 2:
        by0, by1 = min(by0, -4.5), max(by1, 4.5)
    else:
        bx1 = max(bx1, max(abs(c[0]) for c in corners) + w)
    return bx0, by0, bx1, by1


def place_part(sh, part, at, r):
    sym = sh.lib(part['lib'])
    x0, y0, x1, y1 = libs.bbox(sym)
    corners = [rot_vec(r, x, -y) for x in (x0, x1) for y in (y0, y1)]
    right = max(c[0] for c in corners)
    top = min(c[1] for c in corners)
    big = len(libs.pins(sym)) > 2
    if big:
        ra = (at[0] + min(c[0] for c in corners), at[1] + top - 1.27)
        va = (ra[0] + text_len(part['ref']) + 1.27, ra[1])
        just = 'left'
    else:
        horiz = all(pin_geom(p, r)[1][1] == 0 for p in libs.pins(sym))
        if horiz:
            ra = (at[0], at[1] + top - 1.27)
            va = (at[0], at[1] - top + 2.54)
            just = None
        else:
            ra = (at[0] + right + 1.27, at[1] - 0.635)
            va = (at[0] + right + 1.27, at[1] + 1.905)
            just = 'left'
    sh.symbol(part['lib'], part['ref'], part['value'], at, r, fp=part['fp'], ref_at=ra, val_at=va, just=just)
    groups = {}
    for p in libs.pins(sym):
        (ox, oy), d = pin_geom(p, r)
        pa = (round(at[0] + ox, 4), round(at[1] + oy, 4))
        net = part['pins'][p[0]]
        if big and net is not D.NC and is_power(net):
            groups.setdefault((net, d), []).append(pa)
        else:
            sh.connect(net, pa, d)
    singles = {}
    for (net, d), pts in groups.items():
        if len(pts) == 1:
            singles.setdefault(d, []).append((net, pts[0]))
            continue
        ends = [(round(x + d[0] * STUB, 4), round(y + d[1] * STUB, 4)) for x, y in pts]
        for a, b in zip(pts, ends):
            sh.wire(a, b)
        ends.sort()
        sh.wire(ends[0], ends[-1])
        for e in ends[1:-1]:
            sh.junction(e)
        ground = net in D.GROUNDS
        if d[0] == 0:          # bus along x: tap from the left end, along the stub direction
            tap, tdir = ends[0], d
        else:                  # bus along y: grounds leave at the bottom, supplies at the top
            tap, tdir = (ends[-1], (0, 1)) if ground else (ends[0], (0, -1))
        sh.junction(tap)
        tip = (round(tap[0] + tdir[0] * STUB, 4), round(tap[1] + tdir[1] * STUB, 4))
        sh.wire(tap, tip)
        sh.power(net, tip, tdir)
    for d, items in singles.items():
        items.sort(key=lambda it: it[1])
        for k, (net, pa) in enumerate(items):
            sh.connect(net, pa, d, stub=STUB + (5.08 if (k % 2 and d[0] == 0) else 0))


def layout(sh, parts, area):
    ax0, ay0, ax1, ay1 = area
    x, y, row_h = ax0, ay0, 0
    for part in parts:
        r = orient(sh, part)
        bx0, by0, bx1, by1 = extent(sh, part, r)
        w, h = bx1 - bx0, by1 - by0
        if x + w > ax1 or (part.get('br') and x > ax0):
            x, y, row_h = ax0, y + row_h + 2.54, 0
        at = (snap(x - bx0), snap(y - by0))
        if at[1] + by1 > ay1:
            raise SystemExit(f'{sh.name}: no room for {part["ref"]}')
        place_part(sh, part, at, r)
        x += w + 3.81
        row_h = max(row_h, h)


def notes(sh, lines, at):
    sh.text(lines[0], at, size=2.0, bold=True)
    for k, line in enumerate(lines[1:]):
        sh.text(line, (at[0], snap(at[1] + 5.08 + 2.54 * k)))


pages = {}
for i, s in enumerate(D.SHEETS):
    sh = Sheet(s['name'], s['portrait'])
    if s['portrait']:
        notes(sh, s['notes'], (snap(15), snap(17)))
        part = s['parts'][0]
        place_part(sh, part, (snap(104), snap(140)), 0)
    else:
        notes(sh, s['notes'], (snap(15), snap(15)))
        top = 15 + 5.08 + 2.54 * len(s['notes']) + 2
        layout(sh, s['parts'], (15, top, 280, 172))
    sh.write(s['title'])
    s['hier'] = sorted(sh.hier)
    pages[s['name']] = i + 2

# ------------------------------------------------------------------ root
root = Sheet('root')
notes(root, [
    'Nucleo adapter for the legacy 4850 power board',
    'Bench adapter: a NUCLEO-H743ZI drives the 4850 power board (as ordered 2019-11-20) in place',
    'of the old STM32F730 logic board. The power board is not part of this design.',
    'Board: power-board area = old logic board (J101, J102, H101-H103 at the same place),',
    'extended on one side for the Nucleo morpho sockets. Firmware: unimoc nucleo_h743zi overlay.',
], (snap(15), snap(15)))
x, y = 40.64, 45.72
col = 0
for s in D.SHEETS:
    pins_ = s['hier']
    h = max(12.7, snap(2.54 * (len(pins_) + 1)))
    w = 38.1
    sx, sy = snap(x), snap(y)
    u = SHEET_UUID[s['name']]
    e = [S('sheet'), [S('at'), sx, sy], [S('size'), w, h], [S('fields_autoplaced'), S('yes')],
         [S('stroke'), [S('width'), 0.1524], [S('type'), S('solid')]],
         [S('fill'), [S('color'), 0, 0, 0, 0.0]], [S('uuid'), u],
         [S('property'), 'Sheetname', s['name'], [S('at'), sx, snap(sy - 0.7112), 0],
          [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left'), S('bottom')]]],
         [S('property'), 'Sheetfile', s['name'] + '.kicad_sch', [S('at'), sx, snap(sy + h) + 0.5842, 0],
          [S('hide'), S('yes')], [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left'), S('top')]]]]
    for k, n in enumerate(pins_):
        py = snap(sy + 2.54 * (k + 1))
        e.append([S('pin'), n, S('passive'), [S('at'), sx, py, 180],
                  [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left')]],
                  [S('uuid'), uid('sheetpin', s['name'], n)]])
        root.wire((sx, py), (round(sx - STUB, 4), py))
        root.label(n, (round(sx - STUB, 4), py), (-1, 0))
    e.append([S('instances'), [S('project'), PROJECT, [S('path'), '/' + ROOT_UUID, [S('page'), str(pages[s['name']])]]]])
    root.items.append(e)
    col += 1
    if col == 4:
        col, x, y = 0, 40.64, y + 71.12
    else:
        x += 64.77
root.write('Nucleo adapter, overview')

with open(os.path.join(OUT, 'hier.txt'), 'w') as f:
    for s in D.SHEETS:
        f.write(f"{s['name']}: {' '.join(s['hier'])}\n")
print('sheets:', [s['name'] for s in D.SHEETS])
print('hier nets:', sorted(HIER))
