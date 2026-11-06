import json, sys, re
tmpl, jacobi, out, sch_dir = sys.argv[1:5]
p = json.load(open(tmpl))
j = json.load(open(jacobi))
p['meta']['filename'] = 'nucleo_adapter.kicad_pro'
ds = j['board']['design_settings']
p['board']['design_settings'] = {k: ds[k] for k in ds if k != 'drc_exclusions'}
p['board']['design_settings']['drc_exclusions'] = []
p['net_settings']['classes'] = [c for c in j['net_settings']['classes'] if c['name'] == 'Default']
p['net_settings']['netclass_assignments'] = None
p['net_settings']['netclass_patterns'] = []
root = open(f'{sch_dir}/nucleo_adapter.kicad_sch').read()
ruuid = re.search(r'\(uuid "([^"]+)"', root).group(1)
sheets = [[ruuid, 'Root']] + [[u, n] for u, n in re.findall(r'\(sheet\s.*?\(uuid "([^"]+)"\).*?\(property "Sheetname" "([^"]+)"', root, re.S)]
p['sheets'] = sheets
json.dump(p, open(out, 'w'), indent=2)
print(sheets)
