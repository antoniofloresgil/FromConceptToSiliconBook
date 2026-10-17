# Real GUI exports; QT_QPA_PLATFORM=offscreen avoids a host display dependency.
set platform /OpenROAD-flow-scripts/flow/platforms/nangate45
set out $::env(STUDY_OUT)
set stage $::env(STUDY_STAGE)
read_liberty $platform/lib/NangateOpenCellLibrary_typical.lib
read_db $out/$stage.odb
read_sdc $out/$stage.sdc
source $platform/setRC.tcl
if {$stage eq "routed"} {
  read_spef $out/routed.spef
} else {
  estimate_parasitics -placement
}
if {$stage ne "placed"} { set_propagated_clock [all_clocks] }
set rect [[ord::get_db_block] getDieArea]
set scale [[ord::get_db_tech] getDbUnitsPerMicron]
set area [list [expr {double([$rect xMin])/$scale}] [expr {double([$rect yMin])/$scale}] [expr {double([$rect xMax])/$scale}] [expr {double([$rect yMax])/$scale}]]
gui::fit
save_image -area $area -width 1400 $out/$stage.png
if {$stage eq "cts"} {
  save_clocktree_image -width 1400 -height 850 -clock core_clk $out/clocktree.png
}
if {$stage eq "routed"} {
  set paths [find_timing_paths -path_delay max -group_path_count 1 -sort_by_slack]
  set path [lindex $paths 0]
  set f [open $out/critical-path-pins.txt w]
  foreach point [get_property $path points] {
    set pin [get_property $point pin]
    set name [get_full_name $pin]
    puts $f $name
    set iterm [[ord::get_db_block] findITerm $name]
    if {$iterm ne "NULL"} {
      gui::highlight_inst [[$iterm getInst] getName] 0
      set net [$iterm getNet]
      if {$net ne "NULL"} { gui::highlight_net [$net getName] 0 }
    }
  }
  close $f
  save_image -area $area -width 1400 $out/critical-path.png
}
