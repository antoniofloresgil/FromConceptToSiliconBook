import json
from pathlib import Path
import subprocess
import sys

base=Path(__file__).resolve().parent;root=base.parents[2]
review=json.loads((base/'publication-review.json').read_text())
assert review['status']=='pass'
subprocess.run([sys.executable,'tools/figures/print_audit.py','--check',
    '--pdf',str(root/review['release']/'From-Concept-to-Silicon.pdf'),
    '--output',str(base/'figure-review')],cwd=root,check=True)
