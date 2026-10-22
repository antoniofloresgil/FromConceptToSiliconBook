"""Generate original, editable editorial prototypes (not implementation evidence)."""
import argparse
import base64
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "design" / "identity"
SPEC = json.loads((DEST / "palette.json").read_text(encoding="utf-8"))
C = SPEC["colors"]
F = SPEC["fonts"]
LAYOUT = json.loads((DEST / "pdf-layout.json").read_text(encoding="utf-8"))


def text(x, y, content, size=20, color="paper", family="heading", weight=400, extra=""):
    fallback = {"heading": "sans-serif", "body": "serif", "code": "monospace"}[family]
    return (f'<text x="{x}" y="{y}" fill="{C[color]}" font-family="{F[family]}, {fallback}" '
            f'font-size="{size}" font-weight="{weight}" {extra}>{escape(content)}</text>')


def lines(x, y, content, size=20, leading=29, **kwargs):
    return "".join(text(x, y + i * leading, s, size, **kwargs) for i, s in enumerate(content))


def rect(x, y, w, h, color, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{C[color]}" {extra}/>'


def line(x1, y1, x2, y2, color="line", width=1):
    return (f'<path d="M{x1} {y1}H{x2}" stroke="{C[color]}" stroke-width="{width}"/>'
            if y1 == y2 else f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{C[color]}" stroke-width="{width}"/>')


def flow():
    """Concept artwork, with no claim of schematic or implementation accuracy."""
    artwork = json.loads((DEST / "selected-artwork.json").read_text(encoding="utf-8"))["file"]
    data = base64.b64encode((DEST / artwork).read_bytes()).decode("ascii")
    return ('<defs><filter id="art-gray" color-interpolation-filters="linearRGB">'
            '<feColorMatrix type="saturate" values="0"/></filter></defs>'
            '<g aria-label="Four floating layers: architecture, RTL, routing with a highlighted clock tree, and silicon">'
            f'<image x="40" y="512" width="720" height="450" preserveAspectRatio="xMidYMid meet" '
            f'data-cover-art="color" href="data:image/png;base64,{data}"/></g>')


def front():
    s = rect(0, 0, 800, 1100, "cover")
    s += rect(64, 64, 38, 5, "copper")
    s += text(118, 73, "OPEN HARDWARE / RISC-V", 14, "muted", extra='letter-spacing="2"')
    s += text(60, 186, "From", 70, weight=400)
    s += text(58, 284, "Concept", 94, weight=700, extra='letter-spacing="-3"')
    s += text(60, 386, "to Silicon", 92, weight=700, extra='letter-spacing="-3"')
    s += lines(64, 460, ["A Hands-On Guide to Open-Source", "SoC Design Using RISC-V"], 25, 36, color="muted")
    s += flow()
    s += line(64, 972, 736, 972)
    s += text(64, 1028, "Antonio Flores Gil", 25)
    s += text(736, 1028, "FPGA / ASIC", 14, "muted", "code", extra='text-anchor="end"')
    return s


def back():
    s = rect(0, 0, 800, 1100, "paper")
    s += rect(64, 64, 38, 5, "copper")
    s += text(64, 140, "Design. Verify. Integrate.", 39, "ink", weight=700)
    s += text(64, 195, "Then follow the evidence.", 35, "ink")
    s += lines(64, 266, [
        "An open SoC is more than a processor core. Its interfaces,",
        "software, implementation constraints and verification",
        "decisions must work together.",
        "",
        "From Concept to Silicon follows that journey through",
        "RISC-V and CORE-V Wally, with SystemVerilog as its main",
        "RTL language. A dot-product accelerator connects models,",
        "tests, formal checks, integration and FPGA and ASIC flows.",
        "",
        "Executable laboratories and reference results make the",
        "trade-offs concrete, including failed baselines, repairs",
        "and the limits of each validation step."
    ], 20, 31, color="ink", family="body")
    s += line(64, 655, 736, 655, "muted")
    s += text(64, 696, "THREE WAYS THROUGH THE BOOK", 13, "ink", weight=700, extra='letter-spacing="1.6"')
    for i, (n, title, desc) in enumerate([
        ("01", "Foundations", "RTL, architecture and simulation"),
        ("02", "Complete SoC", "Wally, integration, firmware and FPGA"),
        ("03", "ASIC Design", "Synthesis, physical design and GDSII")
    ]):
        y = 745 + i * 66
        s += text(64, y, n, 18, "ink", "code")
        s += text(112, y, title, 20, "ink", weight=700)
        s += text(112, y + 25, desc, 17, "ink")
    s += rect(0, 967, 800, 133, "night")
    s += text(64, 1008, "READ THE BOOK · EXPLORE THE LABS", 13, "paper", weight=700, extra='letter-spacing="1"')
    s += '<a href="https://antoniofloresgil.github.io/FromConceptToSiliconBook/">'
    s += text(64, 1040, "antoniofloresgil.github.io/FromConceptToSiliconBook/", 15, "cyan") + '</a>'
    s += text(64, 1072, "Book & original artwork: CC BY-SA 4.0 · Original code: MIT", 12, "muted")
    return s


def identity():
    s = rect(0, 0, 1400, 1100, "paper")
    s += text(64, 68, "FROM CONCEPT TO SILICON / EDITORIAL IDENTITY", 14, "ink", extra='letter-spacing="2"')
    s += text(60, 142, "From a connection to a system.", 48, "ink", weight=700)
    s += lines(64, 191, ["A precise, quiet identity built from layered systems, generous space and a clear reading hierarchy.",
                           "The cover artwork is a conceptual illustration, not a physical implementation result."], 20, 29, color="ink")
    swatches = [("cover", "Cover"), ("night", "Structure"), ("cyan", "Connections"),
                ("copper", "Amber accent"), ("paper", "Reading surface"), ("ink", "Text")]
    for i, (key, role) in enumerate(swatches):
        x = 64 + i * 212
        s += rect(x, 275, 190, 100, key, f'stroke="{C["muted"]}" stroke-width="1"')
        s += text(x, 405, role, 18, "ink", weight=700)
        s += text(x, 435, C[key], 16, "ink", "code")
    s += line(64, 473, 1336, 473, "muted")
    s += text(64, 520, "TYPOGRAPHY", 14, "ink", weight=700, extra='letter-spacing="2"')
    s += text(64, 577, "Design with evidence.", 39, "ink", weight=700)
    s += text(64, 615, "DejaVu Sans / titles, navigation, captions", 17, "ink")
    s += text(64, 678, "A readable path through complexity.", 29, "ink", "body")
    s += text(64, 716, "DejaVu Serif / long-form reading", 17, "ink")
    s += text(64, 776, "assert (count <= DEPTH);", 25, "ink", "code")
    s += text(64, 814, "DejaVu Sans Mono / RTL, commands, identifiers", 17, "ink")
    s += rect(890, 520, 446, 320, "night")
    s += text(920, 564, "GRAPHIC GRAMMAR", 14, "muted", weight=700)
    for i, label in enumerate(["01  Explicit interfaces", "02  Visible boundaries", "03  Traceable transitions"]):
        y = 620 + i * 76
        s += line(920, y, 1302, y, "cyan" if i != 1 else "copper", 2)
        s += text(920, y - 15, label, 16)
    s += line(64, 880, 1336, 880, "muted")
    s += lines(64, 925, ["PRINT & ACCESS", "Labels and geometry carry meaning; color is supplementary.",
                            "Use dark text on paper. Reserve cyan and amber text for dark backgrounds.",
                            "Review at final size and in grayscale before production."], 18, 30, color="ink")
    s += text(64, 1065, "DIGITAL EDITION · A4 (210 × 297 mm); separate production specifications are needed for print binding.", 14, "ink")
    return s


def document(body, width, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="1100" viewBox="0 0 {width} 1100" '
            f'role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title>'
            '<desc id="desc">Editorial prototype for From Concept to Silicon by Antonio Flores Gil. '
            'Editable vector artwork; not a measured hardware layout.</desc>' + body + '</svg>\n')


def book_styles():
    """Generate both output styles from the reviewed palette and font choices."""
    templates = ROOT / "styles/templates"
    rendered = {name: (templates / (name + ".in")).read_text(encoding="utf-8")
                for name in ["book.scss", "book.tex", "frontmatter.tex"]}
    tokens = {**C, **F, **{k: str(v) for k,v in LAYOUT.items()},
              "toc_counter": str(LAYOUT["toc_numbered_levels"] - 1),
              "inkhex": C["ink"][1:], "nighthex": C["night"][1:], "amberhex": C["copper"][1:]}
    for name, content in rendered.items():
        for key, value in tokens.items():
            content = content.replace("@" + key + "@", value)
        rendered[name] = content
    return {ROOT / "styles" / name: content for name, content in rendered.items()}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-dir", type=Path, help="Also write grayscale SVGs outside the maintained artwork")
    parser.add_argument("--check", action="store_true", help="Reject stale artwork or generated book styles")
    args = parser.parse_args()
    outputs = book_styles()
    for name, width, title, render in [("front", 800, "Front cover", front), ("back", 800, "Back cover", back),
                                       ("identity", 1400, "Visual identity study", identity)]:
        svg = document(render(), width, title)
        outputs[DEST / f"{name}.svg"] = svg
        if args.proof_dir:
            proof = svg.replace('data-cover-art="color"', 'filter="url(#art-gray)"')
            for value in sorted(set(C.values())):
                rgb = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
                linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
                lum = sum(a * b for a, b in zip(linear, [.2126, .7152, .0722]))
                gray = 12.92 * lum if lum <= .0031308 else 1.055 * lum ** (1 / 2.4) - .055
                h = f'{round(gray * 255):02x}'
                proof = proof.replace(value, '#' + h * 3)
            args.proof_dir.mkdir(parents=True, exist_ok=True)
            (args.proof_dir / f"{name}-gray.svg").write_text(proof, encoding="utf-8", newline="\n")
    for path, content in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit("Stale identity output: " + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
