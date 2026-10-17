# Pin/voltage assignments from Digilent Nexys-Video-Master.xdc, Rev. A.
# https://github.com/Digilent/digilent-xdc/blob/master/Nexys-Video-Master.xdc
set_property -dict {PACKAGE_PIN R4 IOSTANDARD LVCMOS33} [get_ports clk100]
set_property -dict {PACKAGE_PIN G4 IOSTANDARD LVCMOS15} [get_ports resetn]
set_property -dict {PACKAGE_PIN E22 IOSTANDARD LVCMOS12} [get_ports scan_data]
set_property -dict {PACKAGE_PIN F21 IOSTANDARD LVCMOS12} [get_ports scan_tick]
set_property -dict {PACKAGE_PIN G21 IOSTANDARD LVCMOS12} [get_ports apply]
set_property -dict {PACKAGE_PIN G22 IOSTANDARD LVCMOS12} [get_ports capture]
set_property -dict {PACKAGE_PIN T14 IOSTANDARD LVCMOS25} [get_ports scan_out]
# nextpnr uses --freq 100 for the clock target. The asynchronous controls
# have synchronizers; this XDC is not a complete vendor STA/CDC signoff file.
