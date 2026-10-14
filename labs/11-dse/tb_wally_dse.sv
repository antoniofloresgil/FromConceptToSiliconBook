`include "config.vh"
`include "BranchPredictorType.vh"
import cvw::*;
`ifndef DSE_DIV_BITS
`define DSE_DIV_BITS 2
`endif
module tb_wally_dse;
 `include "parameter-defs.vh"
 function automatic cvw_t experiment_config();
   cvw_t c;
   c=P;
   c.DTIM_SUPPORTED=0;c.IROM_SUPPORTED=0;
   c.DCACHE_SUPPORTED=0;c.ICACHE_SUPPORTED=0;c.BPRED_SUPPORTED=0;
   c.UNCORE_RAM_SUPPORTED=1;
   c.UNCORE_RAM_BASE=64'h80000000;c.UNCORE_RAM_RANGE=64'h0000ffff;
   c.COUNTERS=3;c.IDIV_BITSPERCYCLE=`DSE_DIV_BITS;
   return c;
 endfunction
 localparam cvw_t EXPERIMENT=experiment_config();
 logic clk=0,reset=1;
 always #5 clk=~clk;
 logic [EXPERIMENT.PA_BITS-1:0] haddr;
 logic [31:0] hwdata,hrdata;
 logic [3:0] hwstrb;
 logic hwrite,hclk,hresetn,hlock;
 logic [2:0] hsize,hburst;
 logic [3:0] hprot;
 logic [1:0] htrans;
 logic [31:0] memory[0:16383];
 logic [31:0] data_address=32'h80000000;
 logic data_valid=0,data_write=0;
 integer ticks=0,k;
 assign hrdata=memory[(data_address-32'h80000000)>>2];
 wallypipelinedcore #(.P(EXPERIMENT)) cpu (
  .clk(clk),.reset(reset),.MTimerInt(1'b0),.MExtInt(1'b0),.SExtInt(1'b0),.MSwInt(1'b0),
  .MTIME_CLINT(64'b0),.HRDATA(hrdata),.HREADY(1'b1),.HRESP(1'b0),
  .HCLK(hclk),.HRESETn(hresetn),.HADDR(haddr),.HWDATA(hwdata),.HWSTRB(hwstrb),
  .HWRITE(hwrite),.HSIZE(hsize),.HBURST(hburst),.HPROT(hprot),.HTRANS(htrans),
  .HMASTLOCK(hlock),.ExternalStall(1'b0)
 );
 initial begin
   $readmemh("firmware.hex",memory);
   $display("DSE_CONFIG divider_bits=%0d",EXPERIMENT.IDIV_BITSPERCYCLE);
   repeat(8) @(negedge clk);reset=0;
 end
 always @(posedge clk) begin
   ticks<=ticks+1;
   if(ticks>2000000) $fatal(1,"DSE firmware timed out PC=%h",cpu.ifu.PCF);
   if(reset) data_valid<=0;
   else begin
     if(data_valid && data_write) begin
       for(k=0;k<4;k=k+1) if(hwstrb[k])
         memory[(data_address-32'h80000000)>>2][8*k+:8]<=hwdata[8*k+:8];
       if(data_address==32'h8000fff0) begin
         if(hwdata!=32'h600d600d) $fatal(1,"DSE numerical/trap failure %h",hwdata);
         $display("DSE_RESULT divider_bits=%0d cycles=%0d instret=%0d checksum=%0d pairs=%0d",
           EXPERIMENT.IDIV_BITSPERCYCLE,{memory[16257],memory[16256]},
           {memory[16259],memory[16258]},memory[16260],memory[16261]);
         $finish;
       end
     end
     data_valid<=htrans[1];
     if(htrans[1]) begin
       if(haddr<34'h080000000 || haddr>=34'h080010000) $fatal(1,"DSE access outside RAM");
       data_address<=haddr[31:0];data_write<=hwrite;
     end
   end
 end
endmodule
