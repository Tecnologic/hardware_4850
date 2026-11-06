import sys
sys.path.insert(0, sys.argv[2])
from sexpr import parse, find, first
import design as D
n = parse(open(sys.argv[1]).read())
comps = find(first(n, 'components'), 'comp')
print('components', len(comps))
got = {}
for net in find(first(n, 'nets'), 'net'):
    name = first(net, 'name')[1]
    for node in find(net, 'node'):
        got[(first(node, 'ref')[1], first(node, 'pin')[1])] = name
# expected
import libs
bad = 0
for s in D.SHEETS:
    for p in s['parts']:
        if p['ref'].startswith('#'):
            continue
        pins = p['pins']
        if pins == 'nucleo':
            sym = libs.symbol(p['lib'])
            pins = {pp[0]: D.NUCLEO_MAP.get(pp[1].split('/')[-1]) for pp in libs.pins(sym)}
        for num, net in pins.items():
            g = got.get((p['ref'], num))
            if net is None:
                if g and not g.startswith('unconnected-'):
                    print('NC but', p['ref'], num, g); bad += 1
                continue
            gn = g.split('/')[-1] if g else None
            if gn != net:
                print('MISMATCH', p['ref'], num, 'want', net, 'got', g); bad += 1
print('mismatches', bad)
names = sorted({v for v in got.values() if not v.startswith('unconnected')})
print(len(names), names)
