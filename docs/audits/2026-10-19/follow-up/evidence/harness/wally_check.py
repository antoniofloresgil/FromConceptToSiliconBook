import hashlib
import json
from pathlib import Path
import subprocess
import sys

from external import snapshot

root=Path('/work');out=root/'labs/build/audit-wally-rtl';base=root/'labs/build'
before=json.loads((base/'audit-wally-external-before.json').read_text())
after=snapshot()
assert before==after,'Pinned upstream checkout changed'
(base/'audit-wally-external-after.json').write_text(json.dumps(after,indent=2)+'\n')
report=json.loads((out/'report.json').read_text())
assert report['status']=='pass' and report['revision']==before['revision']
for name,digest in report['original_sources'].items():
    assert hashlib.sha256((Path('/cvw')/name).read_bytes()).hexdigest()==digest,name
result=subprocess.run([sys.executable,'labs/18-linux-accelerator/collect.py',
    '--qemu','labs/build/audit-linux/report.json','--wally','labs/build/audit-wally-rtl/report.json'],
    check=True,text=True,stdout=subprocess.PIPE)
summary=json.loads(result.stdout)
assert summary['qemu']==summary['wally']=='pass'
historical=json.loads((root/'labs/18-linux-accelerator/reference/wally-report.json').read_text())
historical_summary=json.loads((root/'labs/18-linux-accelerator/reference/results.json').read_text())
(base/'audit-wally-collection.json').write_text(result.stdout)
subprocess.run([sys.executable,'/audit-tools/verify.py','unchanged','labs/build/audit-tool-snapshot.json'],check=True)
record=dict(status='pass',revision=report['revision'],stages=report['stages'],
    bundle_matches_fresh_qemu=report['bundle']==json.loads((base/'audit-linux/report.json').read_text())['bundle'],
    upstream_checkout_unchanged=True,upstream_tracked_files_checked=len(after['files']),
    upstream_gitlinks_recorded_not_used=len(after['gitlinks']),original_export_files_checked=len(report['original_sources']),
    book_sources_and_references_unchanged=True,wally_cycles=summary['wally_cycles'],
    metric_rows=len(summary['wally_metrics']),manufacturing_or_board_qualification=False,
    historical_comparison=dict(original_rtl_export_equal=report['original_sources']==historical['original_sources'],
        patched_rtl_config_equal=report['patched_sources']==historical['patched_sources'],
        boot_cycle_count_equal=summary['wally_cycles']==historical_summary['wally_cycles'],
        metric_values_equal=summary['wally_metrics']==historical_summary['wally_metrics'],
        bundle_hashes_equal={k:v==historical['bundle'][k] for k,v in report['bundle'].items()}))
(base/'audit-wally-final-checks.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
