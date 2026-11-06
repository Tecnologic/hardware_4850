"""Build nucleo_adapter.kicad_pcb (KiCad 10 pcbnew) from the schematic netlist.

argv: netlist, legacy logic PCB (KiCad 5, as ordered), output .kicad_pcb
Coordinates are those of the legacy power board (production/legacy_kicad5/power),
so the adapter lines up with it when both files are overlaid.
"""
import os
import sys
import pcbnew
from sexpr import parse, find, first

NETLIST, LEGACY_LOGIC, OUT = sys.argv[1:4]
FPDIR = os.environ.get('KICAD10_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
MM = pcbnew.FromMM

# legacy logic board -> legacy power board coordinates (both boards' outline origins)
DX, DY = 56.975 - 180.225, 102.975 - 58.975
KEEP = ['J101', 'J102', 'H101', 'H102', 'H103']   # placed like the old logic board

# ---------------------------------------------------------------- netlist
n = parse(open(NETLIST).read())
comps = {}
for c in find(first(n, 'components'), 'comp'):
    ref = first(c, 'ref')[1]
    sp = first(c, 'sheetpath')
    comps[ref] = dict(value=first(c, 'value')[1], fp=first(c, 'footprint')[1],
                      path=first(sp, 'tstamps')[1] + first(c, 'tstamps')[1],
                      sheetname=first(sp, 'names')[1], sheetfile=[p for p in find(c, 'property')
                                                                  if first(p, 'name')[1] == 'Sheetfile'][0])
    comps[ref]['sheetfile'] = first(comps[ref]['sheetfile'], 'value')[1]
pin_net = {}
nets = []
for net in find(first(n, 'nets'), 'net'):
    name = first(net, 'name')[1]
    nets.append(name)
    for node in find(net, 'node'):
        pin_net[(first(node, 'ref')[1], first(node, 'pin')[1])] = name

# ---------------------------------------------------------------- board
board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
tb = board.GetTitleBlock()
tb.SetTitle('Nucleo adapter for the legacy 4850 power board')
tb.SetDate('2026-11-06')
tb.SetRevision('A')
tb.SetCompany('UNIMOC')
tb.SetComment(0, 'NUCLEO-H743ZI on top, J101/J102 on the bottom into the power board')
tb.SetComment(1, 'Coordinates = legacy power board (production/legacy_kicad5/power)')

netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    netinfo[name] = ni

legacy = pcbnew.LoadBoard(LEGACY_LOGIC)
legacy_fp = {f.GetReference(): f for f in legacy.GetFootprints()}


def vec(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def add_fp(ref):
    c = comps[ref]
    lib, name = c['fp'].split(':')
    fp = pcbnew.FootprintLoad(f'{FPDIR}/{lib}.pretty', name)
    fp.SetFPIDAsString(c['fp'])
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH(c['path']))
    fp.SetSheetname(c['sheetname'])
    fp.SetSheetfile(c['sheetfile'])
    fp.GetField(pcbnew.FIELD_T_DATASHEET).SetText('~')
    board.Add(fp)
    for pad in fp.Pads():
        net = pin_net.get((ref, pad.GetNumber()))
        if net in netinfo:
            pad.SetNet(netinfo[net])
    return fp


placed = {}
report = []
# power-board connectors and holes: exactly where the old logic board had them
for ref in KEEP:
    old = legacy_fp[ref]
    fp = add_fp(ref)
    if old.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    fp.SetOrientationDegrees(old.GetOrientationDegrees())
    p = old.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + MM(DX), p.y + MM(DY)))
    fp.SetLocked(True)
    # pad check against the old board (by number; mounting-hole vias share number 1)
    if ref.startswith('J'):
        oldpads = {pd.GetNumber(): pd.GetPosition() for pd in old.Pads()}
        for pd in fp.Pads():
            q, o = pd.GetPosition(), oldpads[pd.GetNumber()]
            err = max(abs(q.x - o.x - MM(DX)), abs(q.y - o.y - MM(DY)))
            if err > MM(0.001):
                raise SystemExit(f'{ref} pad {pd.GetNumber()} off by {pcbnew.ToMM(err)} mm')
    report.append(f'{ref}: ({pcbnew.ToMM(fp.GetPosition().x):.3f}, {pcbnew.ToMM(fp.GetPosition().y):.3f}) '
                  f'rot {fp.GetOrientationDegrees():.0f} {"bottom" if fp.IsFlipped() else "top"}')
    placed[ref] = fp

# Nucleo: pin 1 of CN11 at (X0, Y0); morpho pins end 2 mm before the power-board edge
X0, Y0 = 67.25, -5.0
u = add_fp('U201')
u.SetPosition(vec(X0, Y0))
u.SetLocked(True)
placed['U201'] = u
report.append(f'U201: pin 1 at ({X0}, {Y0}), top')

# other connectors along the edges of the Nucleo extension (not locked)
edge = {
    'J601': (56.5, -29.0, 90), 'J401': (54.0, 5.0, 90), 'J503': (54.0, 25.0, 90),
    'J301': (54.0, 50.0, 90), 'J302': (54.0, 70.0, 90),
    'J501': (144.0, 5.0, 270), 'J502': (144.0, 25.0, 270),
}
for ref, (x, y, r) in edge.items():
    fp = add_fp(ref)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(r)
    placed[ref] = fp

# all other parts: parked right of the board, one column per sheet
cols = {}
for ref in sorted(comps, key=lambda r: (comps[r]['sheetname'], r)):
    if ref in placed:
        continue
    sh = comps[ref]['sheetname']
    col = cols.setdefault(sh, [len(cols), 0])
    fp = add_fp(ref)
    fp.SetPosition(vec(175 + 14 * col[0], -35 + 6 * col[1]))
    col[1] += 1

# ---------------------------------------------------------------- outline
def seg(layer, a, b, w=0.1):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(vec(*a))
    s.SetEnd(vec(*b))
    s.SetWidth(MM(w))
    board.Add(s)


def arc(layer, start, mid, end, w=0.1):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetLayer(layer)
    s.SetArcGeometry(vec(*start), vec(*mid), vec(*end))
    s.SetWidth(MM(w))
    board.Add(s)


def poly_round(layer, pts, rad=1.0):
    """Closed outline through pts (axis-parallel corners) with corner radius rad."""
    k = len(pts)
    import math
    for i in range(k):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % k]
        def unit(a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy)
            return dx / d, dy / d
        u1, u2 = unit(p1, p0), unit(p1, p2)
        a = (p1[0] + u1[0] * rad, p1[1] + u1[1] * rad)
        b = (p1[0] + u2[0] * rad, p1[1] + u2[1] * rad)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        L = math.hypot(*bis)
        c = (p1[0] + bis[0] / L * rad * (1 - 1 / math.sqrt(2)) * math.sqrt(2),
             p1[1] + bis[1] / L * rad * (1 - 1 / math.sqrt(2)) * math.sqrt(2))
        arc(layer, a, c, b)
        nxt = pts[(i + 1) % k]
        u3 = unit(p1, nxt)
        seg(layer, b, (nxt[0] - u3[0] * rad, nxt[1] - u3[1] * rad))


E = pcbnew.Edge_Cuts
# extension x 49..149 for the Nucleo, power area x 57..141 with the old logic board's
# 8 x 8 mm corner notches at the far end (enclosure posts)
outline = [(49, -39), (149, -39), (149, 103), (141, 103), (141, 174), (133, 174), (133, 182),
           (65, 182), (65, 174), (57, 174), (57, 103), (49, 103)]
poly_round(E, outline, 1.0)

# legacy power board outline and its centre hole H106 for reference
D = board.GetLayerID('User.Drawings')
for a, b in [((57, 103), (141, 103)), ((141, 103), (141, 182)), ((141, 182), (57, 182)), ((57, 182), (57, 103))]:
    seg(D, a, b, 0.15)
c = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
c.SetLayer(D)
c.SetCenter(vec(100.25, 157.5))
c.SetEnd(vec(100.25 + 3.5, 157.5))
c.SetWidth(MM(0.15))
board.Add(c)
for txt, (x, y) in [('legacy 4850 power board outline (84 x 79)', (59, 184.5)),
                    ('power board H106 (heatsink bolt below)', (104.5, 157.5))]:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetLayer(D)
    t.SetPosition(vec(x, y))
    t.SetTextSize(vec(1.0, 1.0))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)

board.Save(OUT)
print('\n'.join(report))
print('footprints', len(board.GetFootprints()), 'nets', len(netinfo))
