set p /OpenROAD-flow-scripts/flow/platforms/nangate45
set out $::env(CASE_OUT)
read_liberty $p/lib/NangateOpenCellLibrary_typical.lib
read_db $out/routed.odb
read_sdc $out/routed.sdc
read_spef $out/routed.spef
set_propagated_clock [all_clocks]
gui::fit
set rect [[ord::get_db_block] getDieArea]
set dbu [[ord::get_db_tech] getDbUnitsPerMicron]
set area [list [expr {double([$rect xMin])/$dbu}] [expr {double([$rect yMin])/$dbu}] [expr {double([$rect xMax])/$dbu}] [expr {double([$rect yMax])/$dbu}]]
save_image -area $area -width 1800 $out/implementation.png
save_clocktree_image -width 1400 -height 850 -clock core_clk $out/clocktree.png
set path [lindex [find_timing_paths -path_delay max -group_path_count 1 -sort_by_slack] 0]
foreach point [get_property $path points] {
  set name [get_full_name [get_property $point pin]]
  set term [[ord::get_db_block] findITerm $name]
  if {$term ne "NULL"} {
    gui::highlight_inst [[$term getInst] getName] 0
    set net [$term getNet]
    if {$net ne "NULL"} {gui::highlight_net [$net getName] 0}
  }
}
save_image -area $area -width 1800 $out/critical-path.png
