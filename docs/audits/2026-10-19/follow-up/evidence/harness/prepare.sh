set -eu
python3 /audit-tools/verify.py --root /cvw snapshot /work/labs/build/audit-wally-source-before.json
python3 /audit-tools/verify.py unchanged /work/labs/build/audit-tool-snapshot.json
python3 labs/18-linux-accelerator/wally.py prepare --bundle labs/build/audit-linux/bundle --output-dir labs/build/audit-wally
