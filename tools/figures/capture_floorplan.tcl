# Replay only the verified Lab 16 floorplan prefix, before global placement.
set f [open /work/labs/16-openroad-study/flow.tcl r]
set recipe [read $f]
close $f
set boundary [string first "proc checkpoint" $recipe]
if {$boundary < 0} { error "Missing floorplan boundary" }
eval [string range $recipe 0 [expr {$boundary - 1}]]
write_db $out/floorplan.odb
set rect [[ord::get_db_block] getDieArea]
set scale [[ord::get_db_tech] getDbUnitsPerMicron]
set area [list [expr {double([$rect xMin])/$scale}] [expr {double([$rect yMin])/$scale}] [expr {double([$rect xMax])/$scale}] [expr {double([$rect yMax])/$scale}]]
gui::fit
save_image -area $area -width 1400 $out/floorplan.png
