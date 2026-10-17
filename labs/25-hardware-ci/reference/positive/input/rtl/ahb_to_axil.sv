// AHB-Lite, one 32-bit transfer at a time, to a 32-bit AXI4-Lite slave.
// This adapter is the control-plane fixture; DMA does not traverse it.
module ahb_to_axil (
 input logic clk, reset, hsel, hready,
 input logic [31:0] haddr, hwdata, input logic [3:0] hwstrb,
 input logic hwrite, input logic [2:0] hsize, input logic [1:0] htrans,
 output logic [31:0] hrdata, output logic hreadyout, hresp,
 output logic [4:0] s_awaddr, output logic s_awvalid, input logic s_awready,
 output logic [31:0] s_wdata, output logic [3:0] s_wstrb,
 output logic s_wvalid, input logic s_wready,
 input logic [1:0] s_bresp, input logic s_bvalid, output logic s_bready,
 output logic [4:0] s_araddr, output logic s_arvalid, input logic s_arready,
 input logic [31:0] s_rdata, input logic [1:0] s_rresp,
 input logic s_rvalid, output logic s_rready
);
 localparam IDLE=0, CAPTURE_DATA=1, WRITE=2, B=3, READ_ADDR=4,
            R=5, ERROR_WAIT=6, COMPLETE=7;
 logic [2:0] state;
 logic aw_sent,w_sent,error_latched;
 logic [4:0] address;
 logic [31:0] data, read_data;
 logic [3:0] strobe;
 assign s_awaddr=address, s_araddr=address, s_wdata=data, s_wstrb=strobe;
 assign s_awvalid=state==WRITE && !aw_sent;
 assign s_wvalid=state==WRITE && !w_sent;
 assign s_bready=state==B;
 assign s_arvalid=state==READ_ADDR;
 assign s_rready=state==R;
 assign hreadyout=state==IDLE || state==COMPLETE;
 assign hresp=(state==ERROR_WAIT || state==COMPLETE) && error_latched;
 assign hrdata=read_data;
 always_ff @(posedge clk) begin
   if(reset) begin
     state<=IDLE;aw_sent<=0;w_sent<=0;address<=0;data<=0;strobe<=0;
     read_data<=0;error_latched<=0;
   end else case(state)
     IDLE, COMPLETE: if(hsel && hready && htrans[1]) begin
       address<=haddr[4:0];error_latched<=0;aw_sent<=0;w_sent<=0;
       if(hsize!=2 || haddr[1:0]!=0) begin error_latched<=1;state<=ERROR_WAIT;end
       else state<=hwrite ? CAPTURE_DATA : READ_ADDR;
     end else state<=IDLE;
     CAPTURE_DATA: begin data<=hwdata;strobe<=hwstrb;state<=WRITE;end
     WRITE: begin
       if(s_awready) aw_sent<=1;
       if(s_wready) w_sent<=1;
       if((aw_sent || s_awready) && (w_sent || s_wready)) state<=B;
     end
     B: if(s_bvalid) begin
       error_latched<=s_bresp!=0;state<=s_bresp==0 ? COMPLETE : ERROR_WAIT;
     end
     READ_ADDR: if(s_arready) state<=R;
     R: if(s_rvalid) begin
       read_data<=s_rdata;error_latched<=s_rresp!=0;
       state<=s_rresp==0 ? COMPLETE : ERROR_WAIT;
     end
     ERROR_WAIT: state<=COMPLETE;
     default: state<=IDLE;
   endcase
 end
endmodule
