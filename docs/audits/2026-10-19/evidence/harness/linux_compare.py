import json
from pathlib import Path
base=Path('/work/labs/build');r=json.loads((base/'audit-linux/report.json').read_text())
old=json.loads(Path('/work/labs/18-linux-accelerator/reference/qemu-report.json').read_text())
shape=lambda metrics:[(x['mode'],x['length']) for x in metrics]
result=dict(status_equal=r['status']==old['status']=='pass',sources_equal=r['sources']==old['sources'],
 manifest_equal=r['manifest_sha256']==old['manifest_sha256'],qemu_version_equal=r['qemu']==old['qemu'],
 boot_results_equal=r['runs']==old['runs'],metric_modes_lengths_equal=shape(r['metrics'])==shape(old['metrics']),
 metric_times_equal=r['metrics']==old['metrics'],bundle_hashes_equal={k:v==old['bundle'][k] for k,v in r['bundle'].items()},
 scope='Functional/model/configuration comparison; wall-time metrics and kernel/initramfs binary identity are not acceptance gates. Current bundle hashes independently verified against the fresh raw files.')
for k in ['status_equal','sources_equal','manifest_equal','qemu_version_equal','boot_results_equal','metric_modes_lengths_equal']:assert result[k],k
for k in ['kernel.config','fw_dynamic.bin']:assert result['bundle_hashes_equal'][k],k
(base/'audit-linux-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
