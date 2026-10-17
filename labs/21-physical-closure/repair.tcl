set p /OpenROAD-flow-scripts/flow/platforms/nangate45
set out $::env(CASE_OUT)
read_lef $p/lef/NangateOpenCellLibrary.tech.lef
read_lef $p/lef/NangateOpenCellLibrary.macro.mod.lef
read_liberty $p/lib/NangateOpenCellLibrary_typical.lib
read_verilog $out/mapped.v
link_design dotproduct_axi
read_sdc $::env(CASE_SDC)
source $p/setRC.tcl
initialize_floorplan -utilization $::env(CASE_UTIL) -aspect_ratio 1 -core_space 5 \
  -site FreePDK45_38x28_10R_NP_162NW_34O
source $p/make_tracks.tcl
place_pins -hor_layers metal5 -ver_layers metal6
source /OpenROAD-flow-scripts/flow/designs/nangate45/gcd/grid_strategy-M1-M4-M7.tcl
pdngen
repair_tie_fanout -separation 0 LOGIC0_X1/Z
repair_tie_fanout -separation 0 LOGIC1_X1/Z
set_routing_layers -signal metal2-metal6 -clock metal4-metal6
set_global_routing_layer_adjustment metal2-metal6 0.3
proc evidence {stage model} {
  global out
  tee -file $out/$stage-setup.rpt {report_checks -path_delay max -group_path_count 5 -fields {slew cap fanout input_pins} -format full_clock_expanded -digits 5}
  tee -file $out/$stage-hold.rpt {report_checks -path_delay min -group_path_count 5 -fields {slew cap fanout input_pins} -format full_clock_expanded -digits 5}
  tee -file $out/$stage-constraints.rpt {check_setup -verbose}
  tee -file $out/$stage-limits.rpt {report_check_types -max_slew -max_capacitance -max_fanout -violators}
  tee -file $out/$stage-area.rpt {report_design_area}
  set f [open $out/$stage-metrics.json w]
  set rect [[ord::get_db_block] getCoreArea]
  set dbu [[ord::get_db_tech] getDbUnitsPerMicron]
  set area [expr {double([$rect dx])*[$rect dy]/$dbu/$dbu}]
  puts $f "{\"setup_ns\": [sta::worst_slack -max], \"hold_ns\": [sta::worst_slack -min], \"core_um2\": $area, \"model\": \"$model\"}"
  close $f
  write_db $out/$stage.odb
  write_sdc $out/$stage.sdc
}
global_placement -density 0.65
detailed_placement
check_placement -verbose
estimate_parasitics -placement
evidence placed placement_ideal_clock
repair_design -slew_margin 20 -cap_margin 20
detailed_placement
estimate_parasitics -placement
evidence repaired placement_ideal_clock
clock_tree_synthesis -root_buf CLKBUF_X3 -buf_list {CLKBUF_X1 CLKBUF_X2 CLKBUF_X3} -sink_clustering_enable
repair_clock_nets
detailed_placement
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_timing -setup
repair_timing -hold -hold_margin 0.03 -max_buffer_percent 50
detailed_placement
estimate_parasitics -placement
tee -file $out/cts-tree.rpt {report_cts}
evidence cts placement_propagated_clock
global_route -guide_file $out/route.guide -congestion_iterations 100
estimate_parasitics -global_routing
repair_design -slew_margin 20 -cap_margin 20
repair_timing -setup
repair_timing -hold -hold_margin 0.03 -max_buffer_percent 50
detailed_placement
global_route -guide_file $out/route.guide -congestion_iterations 100
estimate_parasitics -global_routing
evidence global global_route_propagated_clock
detailed_route -output_drc $out/route-drc.rpt
extract_parasitics -ext_model_file $p/rcx_patterns.rules
write_spef $out/routed.spef
read_spef $out/routed.spef
evidence routed openrcx_propagated_clock
set_power_activity -global -activity 0.1
tee -file $out/power.rpt {report_power}
write_def $out/routed.def
write_verilog $out/routed.v
