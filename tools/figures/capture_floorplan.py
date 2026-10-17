#!/usr/bin/env python3
"""Run inside the pinned ORFS image; preserve the original Lab 16 evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/work')
OUT = ROOT / 'labs/build/architecture-floorplan'
IMAGE = 'sha256:e05f28d06032f16d5121b2476b6d4277598506972254142fa5470eb0d70557d3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ['FIGURE_IMAGE_ID'] == IMAGE
    OUT.mkdir(parents=True, exist_ok=True)
    study = ROOT / 'labs/16-openroad-study/reference'
    identity = json.loads((study / 'study.json').read_text())
    assert identity['image'] == IMAGE
    assert sha(study / 'mapped.v') == identity['netlist_sha256']
    for name in ['flow.tcl', 'constraints.sdc']:
        path = ROOT / 'labs/16-openroad-study' / name
        assert sha(path) == identity['inputs'][str(path)]
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen',
           'STUDY_OUT': str(OUT), 'STUDY_PERIOD': '0.91', 'STUDY_UTIL': '55',
           'STUDY_NETLIST': str(study / 'mapped.v'),
           'STUDY_SDC': str(ROOT / 'labs/16-openroad-study/constraints.sdc')}
    recipe = ROOT / 'tools/figures/capture_floorplan.tcl'
    command = ['openroad', '-gui', '-no_init', '-exit', '-threads', '2', str(recipe)]
    with (OUT / 'capture.log').open('w') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    assert '[ERROR ' not in (OUT / 'capture.log').read_text()
    shutil.copyfile(OUT / 'floorplan.png', ROOT / 'figures/architecture-floorplan.png')
    paths = [Path(__file__), recipe, study / 'study.json', study / 'mapped.v',
             ROOT / 'labs/16-openroad-study/flow.tcl',
             ROOT / 'labs/16-openroad-study/constraints.sdc']
    record = dict(image_id=IMAGE, command=command,
                  tool=subprocess.check_output(['openroad', '-version'], text=True).strip(),
                  scope='Floorplan prefix replay only; no placement or new timing claim.',
                  case=dict(target_util_pct=55, period_ns=0.91),
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in paths},
                  outputs={p.name: sha(p) for p in [OUT / 'floorplan.odb',
                                                   OUT / 'floorplan.png', OUT / 'capture.log']})
    (ROOT / 'figures/architecture-floorplan.json').write_text(json.dumps(record, indent=2)+'\n')
    print('PASS actual floorplan GUI export; original Lab 16 evidence unchanged')


if __name__ == '__main__':
    main()
