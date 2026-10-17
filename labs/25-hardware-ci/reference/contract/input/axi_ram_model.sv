// Simulation fixture, not a production interconnect or synthesizable SRAM.
module axi_ram_model (
 input logic clk, reset,
 input integer inject_read, inject_write,
 input logic [31:0] m_araddr, input logic m_arvalid, output logic m_arready,
 input logic [3:0] m_arid, input logic [7:0] m_arlen,
 input logic [2:0] m_arsize, input logic [1:0] m_arburst,
 input logic m_arlock, input logic [3:0] m_arcache,m_arqos, input logic [2:0] m_arprot,
 output logic [31:0] m_rdata, output logic [1:0] m_rresp,
 output logic [3:0] m_rid, output logic m_rvalid, m_rlast, input logic m_rready,
 input logic [31:0] m_awaddr, input logic m_awvalid, output logic m_awready,
 input logic [3:0] m_awid, input logic [7:0] m_awlen,
 input logic [2:0] m_awsize, input logic [1:0] m_awburst,
 input logic m_awlock, input logic [3:0] m_awcache,m_awqos, input logic [2:0] m_awprot,
 input logic [31:0] m_wdata, input logic [3:0] m_wstrb,
 input logic m_wvalid, m_wlast, output logic m_wready,
 output logic [1:0] m_bresp, output logic [3:0] m_bid,
 output logic m_bvalid, input logic m_bready
);
 logic [31:0] mem [0:16383];
 logic [31:0] random_state;
 logic read_pending, address_pending, data_pending;
 logic [31:0] read_address, write_address, write_data;
 logic [3:0] write_mask;
 integer reads, writes, b_okay, seed, i;
 initial begin
   seed=2026; if ($value$plusargs("SEED=%d",seed)) begin end
   for (i=0;i<16384;i=i+1) mem[i]=0;
 end
 assign m_arready = !read_pending && !m_rvalid && random_state[0];
 assign m_awready = !address_pending && !m_bvalid && random_state[3];
 assign m_wready = !data_pending && !m_bvalid && random_state[7];
 assign m_rid=0, m_bid=0, m_rlast=1;
 always @(posedge clk) begin
   if (reset) begin
     random_state<=seed; read_pending<=0; address_pending<=0; data_pending<=0;
     m_rvalid<=0; m_bvalid<=0; m_rdata<=0; m_rresp<=0; m_bresp<=0;
     reads<=0; writes<=0; b_okay<=0;
     read_address<=0; write_address<=0; write_data<=0; write_mask<=0;
   end else begin
     random_state<=random_state*32'd1664525+32'd1013904223;
     if (m_arvalid && m_arready) begin
       if (m_arid!=0 || m_arlen!=0 || m_arsize!=2 || m_arburst!=1 || m_araddr[1:0]!=0)
         $fatal(1,"Invalid DMA read attributes");
       if(m_arlock || m_arcache!=0 || m_arprot!=0 || m_arqos!=0) $fatal(1,"Invalid DMA read sidebands");
       if (m_araddr<32'h80008000 || m_araddr>=32'h8000c000) $fatal(1,"DMA read escaped window");
       read_pending<=1; read_address<=m_araddr; reads<=reads+1;
     end
     if (read_pending && random_state[11]) begin
       m_rvalid<=1; read_pending<=0;
       m_rdata<=mem[(read_address-32'h80000000)>>2];
       m_rresp<=(inject_read!=0 && reads==inject_read) ? 2'b10 : 2'b00;
     end
     if (m_rvalid && m_rready) m_rvalid<=0;
     if (m_awvalid && m_awready) begin
       if (m_awid!=0 || m_awlen!=0 || m_awsize!=2 || m_awburst!=1 || m_awaddr[1:0]!=0)
         $fatal(1,"Invalid DMA write attributes");
       if(m_awlock || m_awcache!=0 || m_awprot!=0 || m_awqos!=0) $fatal(1,"Invalid DMA write sidebands");
       if (m_awaddr<32'h80008000 || m_awaddr>=32'h8000c000) $fatal(1,"DMA write escaped window");
       address_pending<=1; write_address<=m_awaddr;
     end
     if (m_wvalid && m_wready) begin
       if (!m_wlast || m_wstrb!=15) $fatal(1,"Invalid DMA write beat");
       data_pending<=1; write_data<=m_wdata; write_mask<=m_wstrb;
     end
     if (address_pending && data_pending && !m_bvalid && random_state[15]) begin
       writes<=writes+1; address_pending<=0; data_pending<=0; m_bvalid<=1;
       m_bresp<=(inject_write!=0 && writes+1==inject_write) ? 2'b10 : 2'b00;
       // Error response deliberately does not imply rollback. The write happened.
       for (i=0;i<4;i=i+1) if (write_mask[i])
         mem[(write_address-32'h80000000)>>2][8*i+:8]<=write_data[8*i+:8];
     end
     if (m_bvalid && m_bready) begin m_bvalid<=0; if (m_bresp==0) b_okay<=b_okay+1; end
   end
 end
endmodule
