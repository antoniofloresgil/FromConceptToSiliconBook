create_clock -name core_clk -period $::env(CASE_PERIOD) [get_ports clk]
set_clock_uncertainty 0.10 [get_clocks core_clk]
set inputs {}
foreach port [all_inputs] {
  if {[get_full_name $port] ne "clk"} { lappend inputs $port }
}
set_input_delay -max 2.0 -clock core_clk $inputs
set_input_delay -min 0.2 -clock core_clk $inputs
set_output_delay -max 2.0 -clock core_clk [all_outputs]
set_output_delay -min 0.0 -clock core_clk [all_outputs]
set_input_transition 0.05 $inputs
set_load 5.0 [all_outputs]
