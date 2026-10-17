// Shared signal declarations and the complete AXI interface used by both fixtures.
logic [4:0] s_awaddr, s_araddr;
logic s_awvalid, s_awready, s_wvalid, s_wready, s_bvalid, s_bready;
logic [31:0] s_wdata, s_rdata;
logic [3:0] s_wstrb;
logic [1:0] s_bresp, s_rresp;
logic s_arvalid, s_arready, s_rvalid, s_rready, irq;
logic [31:0] m_araddr, m_rdata, m_awaddr, m_wdata;
logic m_arvalid, m_arready, m_rvalid, m_rlast, m_rready;
logic m_awvalid, m_awready, m_wvalid, m_wlast, m_wready, m_bvalid, m_bready;
logic [3:0] m_arid, m_rid, m_awid, m_bid, m_wstrb;
logic [7:0] m_arlen, m_awlen;
logic [2:0] m_arsize, m_awsize;
logic [1:0] m_arburst, m_awburst, m_rresp, m_bresp;
logic m_arlock,m_awlock;
logic [3:0] m_arcache,m_awcache,m_arqos,m_awqos;
logic [2:0] m_arprot,m_awprot;
`ifndef TEST_MAX_LENGTH
`define TEST_MAX_LENGTH 256
`endif
dotproduct_axi #(.MAX_LENGTH(`TEST_MAX_LENGTH)) dut (.*);
integer inject_read=0, inject_write=0;
axi_ram_model ram (.*);
