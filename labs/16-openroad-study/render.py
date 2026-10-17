#!/usr/bin/env python3
"""Export real OpenROAD GUI images and record checkpoint/image provenance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

SOURCE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    jobs = []
    cases = [('u55-p0.91', stage) for stage in ['placed', 'cts', 'routed']]
    cases += [(f'u{util}-p1.00', 'placed') for util in [45, 65]]
    for name, stage in cases:
        out = directory/name
        names = [stage+'.png']
        if stage == 'cts':
            names.append('clocktree.png')
        if stage == 'routed':
            names.append('critical-path.png')
        for picture in names:
            (out/picture).unlink(missing_ok=True)
        env = {**os.environ, 'STUDY_OUT': str(out), 'STUDY_STAGE': stage,
               'QT_QPA_PLATFORM': 'offscreen'}
        command = ['openroad', '-gui', '-no_init', '-exit', str(SOURCE/'images.tcl')]
        log = out/f'image-{stage}.log'
        with log.open('w') as stream:
            result = subprocess.run(command, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=120)
        if result.returncode or '[ERROR ' in log.read_text():
            raise RuntimeError(f'Image export failed: {log}')
        for picture in names:
            if not (out/picture).is_file() or (out/picture).stat().st_size < 1000:
                raise RuntimeError(f'Missing GUI export: {out/picture}')
        inputs = [out/(stage+'.odb'), out/(stage+'.sdc'), SOURCE/'images.tcl']
        if stage == 'routed':
            inputs.append(out/'routed.spef')
        jobs.append({'case': name, 'stage': stage, 'command': command,
                     'inputs': {str(p): sha(p) for p in inputs},
                     'images': {name+'/'+p: sha(out/p) for p in names},
                     'log_sha256': sha(log)})
        print('EXPORTED', name, stage, flush=True)
    (directory/'images.json').write_text(json.dumps(jobs, indent=2)+'\n')


if __name__ == '__main__':
    main()
