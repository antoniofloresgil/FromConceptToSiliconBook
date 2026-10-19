"""Render the identity study using the existing book container's tools."""
from pathlib import Path
import argparse
import subprocess
import sys

from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, default=Path("_book/identity-preview"),
                    help="Separate proof directory; preserves an earlier PDF open in a viewer")
args = parser.parse_args()
OUT = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(ROOT / "tools/design/identity.py"),
                "--proof-dir", str(OUT)], check=True)
writer = PdfWriter()
for grayscale in [False, True]:
    for name in ["front", "back", "identity"]:
        stem = name + ("-gray" if grayscale else "")
        source = OUT / f"{stem}.svg" if grayscale else ROOT / "design/identity" / f"{name}.svg"
        subprocess.run(["rsvg-convert", str(source), "-o", str(OUT / f"{stem}.png")], check=True)
        pdf = OUT / f"{stem}.pdf"
        subprocess.run(["rsvg-convert", "-f", "pdf", str(source), "-o", str(pdf)], check=True)
        writer.append(str(pdf))
writer.add_metadata({"/Title": "From Concept to Silicon — Editorial Study 01",
                     "/Author": "Antonio Flores Gil",
                     "/Subject": "Cover, back cover and identity prototype; color and grayscale proofs"})
with (OUT / "identity-study.pdf").open("wb") as stream:
    writer.write(stream)
writer.close()
print(OUT / "identity-study.pdf")
