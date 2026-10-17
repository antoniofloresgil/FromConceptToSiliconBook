set p /OpenROAD-flow-scripts/flow/platforms/nangate45
set out $::env(VERIFY_OUT)
set src $::env(VERIFY_INPUT)
read_liberty $p/lib/NangateOpenCellLibrary_typical.lib
read_db $src/routed.odb
proc pg_count {} {
  set n 0
  foreach i [[ord::get_db_block] getInsts] {
    foreach t [$i getITerms] {
      if {[$t getSigType] in {POWER GROUND} && [$t getNet] eq "NULL"} {incr n}
    }
  }
  return $n
}
proc functional_snapshot {path} {
  set f [open $path w]
  foreach i [[ord::get_db_block] getInsts] {
    if {[[$i getMaster] getName] in {TAPCELL_X1 FILLCELL_X1}} {continue}
    puts $f "[$i getName] [[$i getMaster] getName] [$i getLocation] [$i getOrient]"
    foreach t [$i getITerms] {
      if {[$t getSigType] ni {POWER GROUND}} {
        set net [$t getNet]
        set name {unconnected}
        if {$net ne "NULL"} {set name [$net getName]}
        puts $f "[[$t getMTerm] getName] $name"
      }
    }
  }
  close $f
}
set before [pg_count]
functional_snapshot $out/functional-before.txt
write_cdl -masters $p/cdl/NangateOpenCellLibrary.cdl $out/baseline.cdl
global_connect
set reconnected [pg_count]
if {$reconnected != 0} {error "Power reconnection incomplete"}
write_cdl -masters $p/cdl/NangateOpenCellLibrary.cdl $out/reconnected.cdl
# Deliberately conservative teaching finish: fill all free sites with body ties,
# using one-site filler only where needed. This is not an optimized tap pitch.
set initial [llength [[ord::get_db_block] getInsts]]
filler_placement {TAPCELL_X1 FILLCELL_X1}
global_connect
set after [pg_count]
if {$after != 0} {error "Finishing left unconnected power pins"}
check_placement -verbose
functional_snapshot $out/functional-after.txt
set added [expr {[llength [[ord::get_db_block] getInsts]] - $initial}]
set f [open $out/power-connectivity.json w]
puts $f "{\"missing_pg_before\":$before,\"missing_pg_reconnected\":$reconnected,\"missing_pg_finished\":$after,\"added_physical_cells\":$added}"
close $f
write_cdl -masters $p/cdl/NangateOpenCellLibrary.cdl $out/finished.cdl
read_sdc $src/routed.sdc
set_propagated_clock [all_clocks]
source $p/setRC.tcl
extract_parasitics -ext_model_file $p/rcx_patterns.rules
write_spef $out/routed.spef
read_spef $out/routed.spef
tee -file $out/setup.rpt {report_checks -path_delay max -group_path_count 3 -fields {slew cap fanout} -digits 5}
tee -file $out/hold.rpt {report_checks -path_delay min -group_path_count 3 -fields {slew cap fanout} -digits 5}
tee -file $out/limits.rpt {report_check_types -max_slew -max_capacitance -max_fanout -violators}
tee -file $out/constraints.rpt {check_setup -verbose}
set f [open $out/timing.json w]
puts $f "{\"setup_ns\":[sta::worst_slack -max],\"hold_ns\":[sta::worst_slack -min]}"
close $f
write_db $out/routed.odb
write_def $out/routed.def
write_sdc $out/routed.sdc
