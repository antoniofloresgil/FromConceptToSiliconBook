#!/usr/bin/env python3
"""Audit saved DRC/LVS metrics and their actual source/artifact identities."""
import argparse
import hashlib
import json
from pathlib import Path
from run import drc_metrics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--reference-dir',default='labs/22-layout-verification/reference')
a=p.parse_args();ref=(ROOT/a.reference_dir).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
i=json.loads((ref/'inventory.json').read_text())
for n,d in i['sources'].items():
    if sha(ROOT/n)!=d:raise ValueError('Stale source '+n)
for n,d in i['artifacts'].items():
    if sha(ref/n)!=d:raise ValueError('Altered evidence '+n)
r=json.loads((ref/'report.json').read_text());v=json.loads((ref/'results.json').read_text())
if r['status']!='completed' or any(c['exit_code'] for c in r['commands']):raise ValueError('Incomplete commands')
for c in r['commands']:
    if sha(ref/c['log'])!=r['artifacts'][c['log']]:raise ValueError('Changed command log')
for label in ['baseline','finished','negative']:
    if drc_metrics(ref/(label+'-drc.lyrdb'))!=v[label+'_drc']:raise ValueError('DRC summary differs')
    if json.loads((ref/(label+'-lvs.json')).read_text())!=v[label+'_lvs']:raise ValueError('LVS summary differs')
    if sha(ref/(label+'-lvs.json'))!=r['artifacts'][label+'-lvs.json']:raise ValueError('Wrong extraction record')
    if sha(ref/(label+'-drc.lyrdb'))!=r['artifacts'][label+'-drc.lyrdb']:raise ValueError('Wrong DRC record')
pg=json.loads((ref/'power-connectivity.json').read_text())
if pg!=v['pg'] or pg['missing_pg_reconnected'] or pg['missing_pg_finished']:raise ValueError('PG closure missing')
if r['artifacts']['functional-before.txt']!=r['artifacts']['functional-after.txt'] or not v['functional_snapshot_equal']:raise ValueError('Functional net graph or placement changed')
t=json.loads((ref/'timing.json').read_text())
if t!=v['timing'] or min(t.values())<0:raise ValueError('Timing did not close')
if (ref/'limits.rpt').read_text().count('(VIOLATED)')!=v['electrical_violations'] or v['electrical_violations']:raise ValueError('Electrical failure')
if (ref/'constraints.rpt').read_text().strip() or not v['unconstrained_report_empty']:raise ValueError('Unconstrained paths')
if v['baseline_lvs']['match'] or v['baseline_drc']['markers']!=0:raise ValueError('Baseline failure distinction lost')
if v['finished_drc']['categories']<100 or v['finished_drc']['markers'] or not v['finished_lvs']['match']:raise ValueError('Finished reference checks do not pass')
if not v['negative_drc']['markers'] or v['negative_lvs']['match']:raise ValueError('Negative control missing')
if v['finished_lvs']['layout']['devices']!=v['finished_lvs']['reference']['devices'] or sum(v['finished_lvs']['layout']['devices'].values())<10000:raise ValueError('Vacuous device extraction')
if not v['reference_gate_pass'] or v['manufacturing_qualified'] or r['manufacturing_qualified']:raise ValueError('Qualification scope changed')
ports=json.loads((ref/'port-identity.json').read_text())
if not ports['identity_pass'] or ports['input_report_sha256']!=sha(ref/'report.json') or ports['database_sha256']!=r['artifacts']['finished-lvs.lvsdb'] or ports['recipe_sha256']!=sha(HERE/'audit_ports.py'):raise ValueError('Port identity audit missing or stale')
if ports['compared_pins']!=v['finished_lvs']['layout']['pins'] or len(ports['pairs'])!=ports['compared_pins']:raise ValueError('Missing port comparisons')
if not all(row['layout'] and row['reference'] and row['layout'].upper()==row['reference'].upper() for row in ports['pairs']):raise ValueError('Port identity changed')
# Link the new GDS/ODB obligation to the exact historical timing-closure release.
baseline=json.loads((ref/'input-report.json').read_text())
if r['input_report_sha256']!=sha(ref/'input-report.json'):raise ValueError('Different input report')
if baseline['status']!='completed' or baseline['target']!='asic' or baseline['candidate']!='repair' or baseline['requested_mhz']!=100:raise ValueError('Wrong input profile')
if baseline['common_manifest_sha256']!=sha(ROOT/'labs/17-complete-case/manifest.json'):raise ValueError('Different common RTL release')
for n,d in r['input_artifacts'].items():
    if baseline['artifacts'][n]!=d:raise ValueError('Different original layout')
print('PASS actual FreePDK45 reference DRC/LVS, power repair, fresh extracted timing, transistor counts and rejected geometry defects; no foundry signoff')
