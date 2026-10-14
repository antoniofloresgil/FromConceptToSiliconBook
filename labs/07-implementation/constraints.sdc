create_clock -name core_clk -period 10.0 [get_ports Clk]
set_clock_uncertainty 1.0 [get_clocks core_clk]

set_input_delay  1.0 -clock core_clk [get_ports {Reset Enable Clear A* B*}]
set_output_delay 1.0 -clock core_clk [get_ports {Sum* Valid Overflow}]
