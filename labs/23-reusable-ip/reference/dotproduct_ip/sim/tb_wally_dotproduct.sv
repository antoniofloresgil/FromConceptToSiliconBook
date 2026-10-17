`include "config.vh"
`include "BranchPredictorType.vh"
import cvw::*;
module tb_wally_dotproduct;
 `include "parameter-defs.vh"
 function automatic cvw_t course_config();
   cvw_t c;
   c=P;
   c.DTIM_SUPPORTED=0; c.IROM_SUPPORTED=0;
   c.DCACHE_SUPPORTED=0; c.ICACHE_SUPPORTED=0;
   c.UNCORE_RAM_SUPPORTED=1;
   c.UNCORE_RAM_BASE=64'h80000000; c.UNCORE_RAM_RANGE=64'h0000ffff;
   c.COUNTERS=3; c.EXT_MEM_SUPPORTED=1; c.EXT_MEM_BASE=64'h10080000; c.EXT_MEM_RANGE=64'h1f;
   return c;
 endfunction
 localparam cvw_t COURSE=course_config();
 logic clk=0,reset=1;
 always #5 clk=~clk;
 `include "axi_connections.svh"
 logic [COURSE.PA_BITS-1:0] haddr;
 logic [31:0] hwdata, hrdata;
 logic [3:0] hwstrb;
 logic hwrite,hready,hresp,hclk,hresetn,hlock;
 logic [2:0] hsize,hburst;
 logic [3:0] hprot;
 logic [1:0] htrans;
 logic bridge_ready,bridge_error;
 logic [31:0] bridge_data,ram_address=0;
 logic previous_mmio=0,previous_ram=0,ram_write=0;
 logic select_mmio;
 integer cycles=0,k;
 assign select_mmio=haddr>=34'h010080000 && haddr<34'h010080020;
 assign hready=previous_mmio ? bridge_ready : 1'b1;
 assign hresp=previous_mmio ? bridge_error : 1'b0;
 assign hrdata=previous_mmio ? bridge_data : ram.mem[(ram_address-32'h80000000)>>2];
 wallypipelinedcore #(.P(COURSE)) cpu (
   .clk(clk),.reset(reset),.MTimerInt(1'b0),.MExtInt(irq),.SExtInt(1'b0),.MSwInt(1'b0),
   .MTIME_CLINT(64'b0),.HRDATA(hrdata),.HREADY(hready),.HRESP(hresp),
   .HCLK(hclk),.HRESETn(hresetn),.HADDR(haddr),.HWDATA(hwdata),.HWSTRB(hwstrb),
   .HWRITE(hwrite),.HSIZE(hsize),.HBURST(hburst),.HPROT(hprot),.HTRANS(htrans),
   .HMASTLOCK(hlock),.ExternalStall(1'b0)
 );
 ahb_to_axil bridge (
   .clk(clk),.reset(reset),.hsel(select_mmio),.hready(hready),.haddr(haddr[31:0]),
   .hwdata(hwdata),.hwstrb(hwstrb),.hwrite(hwrite),.hsize(hsize),.htrans(htrans),
   .hrdata(bridge_data),.hreadyout(bridge_ready),.hresp(bridge_error),
   .s_awaddr(s_awaddr),.s_awvalid(s_awvalid),.s_awready(s_awready),
   .s_wdata(s_wdata),.s_wstrb(s_wstrb),.s_wvalid(s_wvalid),.s_wready(s_wready),
   .s_bresp(s_bresp),.s_bvalid(s_bvalid),.s_bready(s_bready),
   .s_araddr(s_araddr),.s_arvalid(s_arvalid),.s_arready(s_arready),
   .s_rdata(s_rdata),.s_rresp(s_rresp),.s_rvalid(s_rvalid),.s_rready(s_rready)
 );
 initial begin
   // RAM model initializes at time zero; load after that initialization.
   #1; $readmemh("firmware.hex",ram.mem);
   repeat(8) @(negedge clk); reset=0;
 end
 always @(posedge clk) begin
   cycles<=cycles+1;
   if(cycles>2000000) $fatal(1,"Wally firmware timed out PC=%h",cpu.ifu.PCF);
   if(reset) begin previous_mmio<=0;previous_ram<=0;end
   else begin
     if(previous_ram && ram_write && hready) begin
       for(k=0;k<4;k=k+1) if(hwstrb[k])
         ram.mem[(ram_address-32'h80000000)>>2][8*k+:8]<=hwdata[8*k+:8];
       if(ram_address==32'h8000fff0) begin
         if(hwdata!=32'h600d600d) $fatal(1,"Firmware failure %h PC=%h",hwdata,cpu.ifu.PCF);
         for(k=0;k<5;k=k+1)
           $display("METRIC N=%0d software_cycles=%0d accelerator_total_cycles=%0d",
             ram.mem[16256+k*3],ram.mem[16257+k*3],ram.mem[16258+k*3]);
         $display("PASS real Wally: five polling jobs, IRQ handler, invalid descriptor, %0d cycles",cycles);
         $finish;
       end
     end
     if(hready) begin
       previous_mmio<=htrans[1] && select_mmio;
       previous_ram<=htrans[1] && !select_mmio;
       if(htrans[1] && !select_mmio) begin
         if(haddr<34'h080000000 || haddr>=34'h080010000) $fatal(1,"CPU outside RAM/MMIO %h",haddr);
         ram_address<=haddr[31:0];ram_write<=hwrite;
       end
     end
   end
 end
endmodule
