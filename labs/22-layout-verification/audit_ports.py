"""Inspect the actual LVS cross-reference for top-port identity after matching."""
import hashlib
import json
from pathlib import Path
import pya

out=Path(out)
db=pya.LayoutVsSchematic();db.read(str(out/'finished-lvs.lvsdb'))
rows=[]
for pair in db.xref().each_pin_pair(db.netlist().top_circuit()):
    a,b=pair.first(),pair.second()
    rows.append({'layout':None if a is None else a.name(),
                 'reference':None if b is None else b.name(), 'status':str(pair.status())})
ok=bool(rows) and all(r['layout'] and r['reference'] and r['layout'].upper()==r['reference'].upper() for r in rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r={'identity_pass':ok,'compared_pins':len(rows),'pairs':rows,
   'database_sha256':sha(out/'finished-lvs.lvsdb'),'input_report_sha256':sha(out/'report.json'),
   'recipe_sha256':sha(Path(__file__))}
(out/'port-identity.json').write_text(json.dumps(r,indent=2)+'\n')
if not ok:raise RuntimeError('LVS port identity differs; inspect port-identity.json')
print('PASS actual LVS top-port names:',len(rows))
