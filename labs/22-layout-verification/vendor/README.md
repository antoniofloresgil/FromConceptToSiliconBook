# Upstream extraction reference

`lvs_freepdk45.lylvs` and `LICENSE` are unchanged files from
https://github.com/klayoutmatthias/FreePDK45_for_KLayout at commit
`ab0495a69fa76fdc726a75f890bbf67b518db42a` (GPL version 3).

The executable `../lvs.lvs` is a GPL-3.0-only adaptation for the pinned Nangate45
cell GDS/CDL: explicit batch inputs, VTL model convention, actual unmarked body
contacts in the known TAPCELL master, geometric well connections, matching
normalization on both sides, and JSON comparison evidence. It does not insert
implicit or global power connections to make LVS pass. The original GUI/OpenRAM
example is retained for attribution and review, not executed unmodified.
