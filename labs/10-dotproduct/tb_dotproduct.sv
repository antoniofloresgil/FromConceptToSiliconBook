module tb_dotproduct;
 logic clk=0, reset=1;
 always #5 clk=~clk;
 `include "axi_connections.svh"
 logic [31:0] a[0:255],b[0:255];
 logic [63:0] expected[0:255];
 logic [63:0] square[0:255];
 integer i, n, r0, w0, cycles=0, completed=0;
 logic [31:0] status, value;
 logic [31:0] prev_araddr,prev_awaddr,prev_wdata,prev_rdata;
 logic [1:0] prev_bresp,prev_rresp;
 logic ar_stall=0,aw_stall=0,w_stall=0,br_stall=0,rr_stall=0;
 always @(posedge clk) begin
   cycles<=cycles+1;
   if (cycles>2000000) $fatal(1,"Timeout");
   if (!reset) begin
     if (ar_stall && (!m_arvalid || m_araddr!=prev_araddr)) $fatal(1,"AR changed under stall");
     if (aw_stall && (!m_awvalid || m_awaddr!=prev_awaddr)) $fatal(1,"AW changed under stall");
     if (w_stall && (!m_wvalid || m_wdata!=prev_wdata)) $fatal(1,"W changed under stall");
     if (br_stall && (!s_bvalid || s_bresp!=prev_bresp)) $fatal(1,"B changed under stall");
     if (rr_stall && (!s_rvalid || s_rdata!=prev_rdata || s_rresp!=prev_rresp)) $fatal(1,"R changed under stall");
     if (dut.done && ram.b_okay<2) $fatal(1,"Premature DONE");
   end
   ar_stall<=!reset && m_arvalid && !m_arready; prev_araddr<=m_araddr;
   aw_stall<=!reset && m_awvalid && !m_awready; prev_awaddr<=m_awaddr;
   w_stall<=!reset && m_wvalid && !m_wready; prev_wdata<=m_wdata;
   br_stall<=!reset && s_bvalid && !s_bready; prev_bresp<=s_bresp;
   rr_stall<=!reset && s_rvalid && !s_rready; prev_rdata<=s_rdata; prev_rresp<=s_rresp;
 end
 task automatic write_reg(input [4:0] address,input [31:0] data,input [3:0] mask,input bit data_first,input [1:0] response);
   begin
     // Exercise the AW and W channels in both orders, with a stalled response.
     @(negedge clk);
     if (data_first) begin
       s_wdata=data;s_wstrb=mask;s_wvalid=1;
       do @(posedge clk); while (!s_wready);
       @(negedge clk);s_wvalid=0; repeat(3) @(negedge clk);
       s_awaddr=address;s_awvalid=1;
       do @(posedge clk); while (!s_awready);
       @(negedge clk);s_awvalid=0;
     end else begin
       s_awaddr=address;s_awvalid=1;
       do @(posedge clk); while (!s_awready);
       @(negedge clk);s_awvalid=0; repeat(2) @(negedge clk);
       s_wdata=data;s_wstrb=mask;s_wvalid=1;
       do @(posedge clk); while (!s_wready);
       @(negedge clk);s_wvalid=0;
     end
     wait(s_bvalid); repeat(4) @(negedge clk);
     if (s_bresp!=response) $fatal(1,"Wrong AXIL B response address=%h",address);
     s_bready=1; @(negedge clk);s_bready=0;
   end
 endtask
 task automatic read_reg(input [4:0] address,output [31:0] data,input [1:0] response);
   begin
     @(negedge clk); s_araddr=address;s_arvalid=1;
     do @(posedge clk); while (!s_arready);
     @(negedge clk);s_arvalid=0;
     wait(s_rvalid);repeat(3) @(negedge clk);
     if (s_rresp!=response) $fatal(1,"Wrong AXIL R response");
     data=s_rdata;s_rready=1;@(negedge clk);s_rready=0;
   end
 endtask
 task automatic descriptor(input [31:0] aa,bb,dd,ll);
   begin
     write_reg(8,aa,15,0,0);write_reg(12,bb,15,1,0);
     write_reg(16,dd,15,0,0);write_reg(20,ll,15,1,0);
   end
 endtask
 task automatic wait_terminal;
   begin
     status=1;
     while (status[0]) read_reg(4,status,0);
   end
 endtask
 task automatic invalid_job(input [31:0] aa,bb,dd,ll);
   begin
     descriptor(aa,bb,dd,ll);r0=ram.reads;w0=ram.writes;
     write_reg(0,3,15,1,0);wait_terminal;
     read_reg(24,value,0);
     if (status!=12 || value!=1 || !irq || ram.reads!=r0 || ram.writes!=w0)
       $fatal(1,"Invalid descriptor did not fail before DMA");
     write_reg(28,1,1,0,0); if (irq) $fatal(1,"IRQ ACK failed");
   end
 endtask
 initial begin
   s_awaddr=0;s_araddr=0;s_awvalid=0;s_wvalid=0;s_bready=0;
   s_wdata=0;s_wstrb=0;s_arvalid=0;s_rready=0;
   $readmemh("a.hex",a);$readmemh("b.hex",b);$readmemh("expected.hex",expected);
   $readmemh("square.hex",square);
   repeat(4) @(negedge clk);reset=0;
   for(i=0;i<256;i=i+1) begin ram.mem[8192+i]=a[i];ram.mem[8448+i]=b[i];end
   write_reg(8,32'h80000000,15,0,0);write_reg(8,32'h00008000,3,1,0);
   read_reg(8,value,0); if(value!=32'h80008000) $fatal(1,"Byte mask failed");
   write_reg(4,1,15,0,2);read_reg(1,value,2);
   for(n=1;n<=`TEST_MAX_LENGTH;n=n+1) begin
     descriptor(32'h80008000,32'h80008400,32'h80008800,n);
     r0=ram.reads;w0=ram.writes;
     write_reg(0,3,15,n[0],0);
     if(n>=8) begin
       write_reg(20,1,15,0,2);write_reg(0,1,15,1,2);
     end
     wait_terminal;
     if(status!=10 || !irq || {ram.mem[8705],ram.mem[8704]}!=expected[n-1])
       $fatal(1,"Arithmetic/status mismatch N=%d result=%h expected=%h",n,{ram.mem[8705],ram.mem[8704]},expected[n-1]);
     if(ram.reads-r0!=2*n || ram.writes-w0!=2) $fatal(1,"Wrong DMA transaction count");
     write_reg(28,1,1,0,0);if(irq) $fatal(1,"IRQ stuck");
     completed=completed+1;
   end
   // Read-only sources may alias. This also exercises a positive >32-bit sum.
   descriptor(32'h80008000,32'h80008000,32'h80008800,`TEST_MAX_LENGTH);
   write_reg(0,1,15,0,0);wait_terminal;
   if(status!=2 || {ram.mem[8705],ram.mem[8704]}!=square[`TEST_MAX_LENGTH-1])
     $fatal(1,"Source alias / wide accumulation failed");
   invalid_job(32'h80008000,32'h80008400,32'h80008800,0);
   invalid_job(32'h80008000,32'h80008400,32'h80008800,`TEST_MAX_LENGTH+1);
   invalid_job(32'h80008001,32'h80008400,32'h80008800,1);
   invalid_job(32'h80008000,32'h80008400,32'h80008804,1);
   invalid_job(32'h80007ffc,32'h80008400,32'h80008800,1);
   invalid_job(32'h8000bffc,32'h80008400,32'h80008800,2);
   invalid_job(32'hfffffffc,32'h80008400,32'h80008800,2);
   invalid_job(32'h80008000,32'h80008400,32'h80008000,4);
   descriptor(32'h80008000,32'h80008400,32'h80008800,1);
   inject_read=ram.reads+1; write_reg(0,3,15,0,0);wait_terminal;
   read_reg(24,value,0);if(status!=12 || value!=2) $fatal(1,"Read fault failed");
   inject_read=0;inject_write=ram.writes+2;write_reg(0,3,15,0,0);wait_terminal;
   read_reg(24,value,0);if(status!=12 || value!=3) $fatal(1,"Write fault failed");
   inject_write=0;
   descriptor(32'h80008000,32'h80008400,32'h80008800,`TEST_MAX_LENGTH);
   write_reg(0,3,15,0,0);repeat(10) @(negedge clk);
   reset=1;repeat(4) @(negedge clk);reset=0;
   read_reg(4,status,0);if(status!=0 || irq) $fatal(1,"Reset did not clear state");
   descriptor(32'h80008000,32'h80008400,32'h80008800,1);
   write_reg(0,1,15,0,0);wait_terminal;
   if(status!=2 || irq) $fatal(1,"Polling restart after reset failed");
   $display("PASS dotproduct: %0d lengths, AXIL ordering/strobes, DMA stalls/errors, window policy, IRQ/reset",completed);
   $finish;
 end
endmodule
