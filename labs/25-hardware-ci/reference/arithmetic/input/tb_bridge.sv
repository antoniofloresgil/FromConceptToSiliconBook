module tb_bridge;
 logic clk=0,reset=1;
 always #5 clk=~clk;
 `include "axi_connections.svh"
 logic [31:0] haddr=0,hwdata=0,hrdata;
 logic [3:0] hwstrb=15;
 logic hwrite=0,hready,hresp;
 logic [2:0] hsize=2;
 logic [1:0] htrans=0;
 integer cycles=0,error_waits;
 logic [31:0] value;
 ahb_to_axil bridge (
   .clk(clk),.reset(reset),.hsel(1'b1),.hready(hready),.haddr(haddr),
   .hwdata(hwdata),.hwstrb(hwstrb),.hwrite(hwrite),.hsize(hsize),.htrans(htrans),
   .hrdata(hrdata),.hreadyout(hready),.hresp(hresp),
   .s_awaddr(s_awaddr),.s_awvalid(s_awvalid),.s_awready(s_awready),
   .s_wdata(s_wdata),.s_wstrb(s_wstrb),.s_wvalid(s_wvalid),.s_wready(s_wready),
   .s_bresp(s_bresp),.s_bvalid(s_bvalid),.s_bready(s_bready),
   .s_araddr(s_araddr),.s_arvalid(s_arvalid),.s_arready(s_arready),
   .s_rdata(s_rdata),.s_rresp(s_rresp),.s_rvalid(s_rvalid),.s_rready(s_rready)
 );
 always @(posedge clk) begin cycles<=cycles+1;if(cycles>1000) $fatal(1,"Bridge timeout");end
 task automatic transfer(input bit write,input [31:0] address,data,input [2:0] size,
                         input bit expect_error,output [31:0] returned);
   begin
     @(negedge clk);htrans=2;haddr=address;hwrite=write;hsize=size;hwdata=32'hbad0bad0;
     @(posedge clk); // Address phase; data still deliberately poisoned.
     @(negedge clk);htrans=0;hwdata=data;error_waits=0;
     do begin
       @(posedge clk);
       if(hresp && !hready) error_waits=error_waits+1;
     end while(!hready);
     returned=hrdata;
     if(hresp!=expect_error || error_waits!=(expect_error ? 1:0))
       $fatal(1,"AHB response must have exactly one stalled error cycle");
   end
 endtask
 initial begin
   repeat(4) @(negedge clk);reset=0;
   transfer(1,32'h10060008,32'h80008000,2,0,value);
   transfer(0,32'h10060008,0,2,0,value);
   if(value!=32'h80008000) $fatal(1,"Bridge captured address-phase write data");
   transfer(1,32'h10060004,1,2,1,value);
   transfer(0,32'h10060009,0,2,1,value);
   transfer(0,32'h10060008,0,1,1,value);
   transfer(0,32'h10060008,0,2,0,value);
   if(value!=32'h80008000) $fatal(1,"Bridge did not recover after errors");
   $display("PASS AHB bridge: following data phase, reads, two-cycle errors and recovery");$finish;
 end
endmodule
