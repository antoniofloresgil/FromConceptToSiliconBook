"""Prepare selected cover artwork for the maintained PDF page dimensions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
NS = "http://www.w3.org/2000/svg"


def verify_artwork(directory):
    manifest = json.loads((directory / "selected-artwork.json").read_text(encoding="utf-8"))
    actual = hashlib.sha256((directory / manifest["file"]).read_bytes()).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError("Selected cover artwork differs from its reviewed identity")


def print_cover(source, destination, background, width_mm, height_mm):
    ET.register_namespace("", NS)
    tree = ET.parse(source)
    svg = tree.getroot()
    # Contain the complete composition; extend the canvas rather than crop/stretch.
    width = max(800., 1100 * width_mm / height_mm)
    height = width * height_mm / width_mm
    left, top = (800 - width) / 2, (1100 - height) / 2
    svg.set("width", f"{width_mm}mm")
    svg.set("height", f"{height_mm}mm")
    svg.set("viewBox", f"{left:g} {top:g} {width:g} {height:g}")
    svg.insert(0, ET.Element(f"{{{NS}}}rect", {
        "x": f"{left:g}", "y": f"{top:g}", "width": f"{width:g}", "height": f"{height:g}", "fill": background}))
    # Carry full-width background bands into the added side canvas as well.
    bands = [child for child in list(svg)[1:] if child.tag == f"{{{NS}}}rect"
             and child.get("x") == "0" and child.get("width") == "800"
             and child.get("height") != "1100"]
    for child in bands:
        attrs = {**child.attrib, "x": f"{left:g}", "width": f"{width:g}"}
        # A taller print canvas also needs the bottom band to reach its edge.
        if float(child.get("y", 0)) + float(child.get("height")) == 1100:
            attrs["height"] = f"{top + height - float(child.get('y', 0)):g}"
        svg.insert(1, ET.Element(f"{{{NS}}}rect", attrs))
    tree.write(destination, encoding="utf-8", xml_declaration=True)


def main():
    source = ROOT / "design/identity"
    verify_artwork(source)
    subprocess.run([sys.executable, str(ROOT / "tools/design/identity.py"), "--check"], check=True)
    colors = json.loads((source / "palette.json").read_text(encoding="utf-8"))["colors"]
    layout = json.loads((source / "pdf-layout.json").read_text(encoding="utf-8"))
    output = ROOT / ".quarto/identity"
    output.mkdir(parents=True, exist_ok=True)
    for name, background in [("front", colors["cover"]), ("back", colors["paper"])]:
        svg = output / f"{name}.svg"
        print_cover(source / f"{name}.svg", svg, background, layout["width_mm"], layout["height_mm"])
        subprocess.run(["rsvg-convert", "--format", "pdf", "--output",
                        str(output / f"{name}.pdf"), str(svg)], check=True)


if __name__ == "__main__":
    main()
