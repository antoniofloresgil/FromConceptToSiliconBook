# Teaching input budget, not achieved physical timing or a board pin assignment.
create_clock -name core_clk -period 10.0 [get_ports clk]
set_input_delay 2.0 -clock core_clk [get_ports {reset s_awaddr* s_awvalid s_wdata* s_wstrb* s_wvalid s_bready s_araddr* s_arvalid s_rready m_arready m_rdata* m_rresp* m_rid* m_rvalid m_rlast m_awready m_wready m_bresp* m_bid* m_bvalid}]
set_output_delay 2.0 -clock core_clk [get_ports {s_awready s_wready s_bresp* s_bvalid s_arready s_rdata* s_rresp* s_rvalid irq m_araddr* m_arvalid m_arid* m_arlen* m_arsize* m_arburst* m_arlock m_arcache* m_arprot* m_arqos* m_rready m_awaddr* m_awvalid m_awid* m_awlen* m_awsize* m_awburst* m_awlock m_awcache* m_awprot* m_awqos* m_wdata* m_wstrb* m_wvalid m_wlast m_bready}]
# No false paths or reset exceptions are silently asserted. Adapt the budgets,
# clock/reset strategy and port names to the real integration before signoff.
