# Architectural figures

The `architecture-*.svg` series is original editable artwork for *From Concept to
Silicon*. Generate it with Python's standard library:

```sh
python tools/figures/architecture.py
python tools/figures/architecture.py --check
```

The manifest binds the generator, embedded image inputs and SVG outputs by SHA-256.
The book build renders the SVGs as vectors for the PDF and retains SVG in HTML.
The physical overview embeds raster GUI captures inside vector frames.

## Graphic vocabulary

- White background, Arial/sans-serif, dark text; rounded boxes and 2 px outlines.
- Blue `#24577a`: compute, control and ordinary request paths.
- Green `#28705c`: memory, service or policy paths, identified by text.
- Orange `#a34624`, dashed arrows: events, dependencies or external influences.
- Nested frames mean containment; a dashed enclosure means a declared boundary.
- Arrow labels and captions determine meaning. Color alone never establishes
  coherence, trust, privilege or measured implementation status.
- 960-unit canvas; titles 26, block labels 21 and supporting text generally 18–19.

The local meaning of arrows is stated in each caption. Timing diagrams show the
interval immediately before each numbered rising edge; green dots mark accepted
transfers. They are protocol examples, not recorded simulation waveforms.

## Technical anchors

| Figure | Scope and source |
|---|---|
| Wally hierarchy | Pinned CVW `3b30ba6b6519bd2c26c1437e6d61f632a35cef6c`, `src/wally/{wallypipelinedsoc,wallypipelinedcore}.sv`; abbreviated functional subtrees, not an exhaustive elaboration dump |
| OoO | Conceptual physical-register / ROB organization; independent of a selected BOOM or XiangShan generation |
| Cache miss | Blocking write-back sequence and the chapter's selected RV32 AHB geometry |
| AXI write / read | Protocol examples matching the chapter's handshake and burst rules; read burst is not an implemented feature of the single-beat accelerator |
| Boot | Conventional OpenSBI/Linux handoff and the chapter's boot contract; no measured time scale |
| Nexys | Open `fpgaOpenSource` / LiteDRAM target documented in the FPGA chapter; unresolved hardware bring-up remains unresolved |
| Security | Proposed enforcement architecture; not a claim that all guards or a root of trust exist in pinned Wally |
| RVV | Architectural VLEN/SEW/LMUL example and separately labelled optional banking; not a Wally vector implementation |
| Dot product | Actual `labs/10-dotproduct/rtl/{dotproduct_axi,dotproduct_engine,dotproduct_mac}.sv`; Linux/Wally MMIO extension at `0x10080000` |
| OpenROAD | Actual new floorplan prefix replay plus unchanged Lab 16 placement / CTS / routed captures |

## Reproduce the actual floorplan panel

This runs only the initialization/floorplan prefix of the verified Lab 16 recipe,
with its recorded mapped netlist, constraints, utilization and pinned ASIC image.
It does not rerun or alter the historical timing study. From the repository root:

```sh
docker run --rm --network none --env HOME=/tmp \
  --env FIGURE_IMAGE_ID=sha256:e05f28d06032f16d5121b2476b6d4277598506972254142fa5470eb0d70557d3 \
  --mount type=bind,source="$PWD",target=/work --workdir /work \
  --entrypoint /bin/bash \
  openroad/orfs@sha256:fd3e27cf1788815be526e86fbe449310d1114bf256fd6c7af9dced6eaf12c699 \
  -lc 'source /OpenROAD-flow-scripts/env.sh && python3 tools/figures/capture_floorplan.py'
python tools/figures/architecture.py
```

`figures/architecture-floorplan.json` records the actual command, tool/image and
input/output hashes. The raw OpenDB and capture log stay under
`labs/build/architecture-floorplan/`. There is no new timing claim. The generator
embeds the new PNG and the three existing OpenROAD study PNGs without repainting
their implementation geometry. The original Lab 16 provenance remains intact.
