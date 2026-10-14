`timescale 1ns/1ps
module tb_axil;
  logic ACLK=0;always #5 ACLK=~ACLK;
  logic ARESETn=0,AWVALID=0,WVALID=0,BREADY=0,ARVALID=0,RREADY=0;
  logic AWREADY,WREADY,BVALID,ARREADY,RVALID,EventPulse=0,Irq;
  logic[5:0]AWADDR=0,ARADDR=0;
  logic[2:0]AWPROT=0,ARPROT=0;
  logic[31:0]WDATA=0,RDATA,OutputValue;
  logic[3:0]WSTRB=0;
  logic[1:0]BRESP,RRESP;
  event_axil dut(.*);
  logic[31:0]reference=0;
  integer seed,rc;
  task automatic send_address(input logic[5:0]address);
    @(negedge ACLK);AWADDR=address;AWVALID=1;
    do @(posedge ACLK);while(!AWREADY);
    @(negedge ACLK);AWVALID=0;
  endtask
  task automatic send_data(input logic[31:0]data,input logic[3:0]mask);
    @(negedge ACLK);WDATA=data;WSTRB=mask;WVALID=1;
    do @(posedge ACLK);while(!WREADY);
    @(negedge ACLK);WVALID=0;
  endtask
  task automatic write_reg(input logic[5:0]address,input logic[31:0]data,input logic[3:0]mask,input bit data_first,input bit collision);
    if(data_first)begin send_data(data,mask);send_address(address);end
    else begin send_address(address);send_data(data,mask);end
    EventPulse=collision;
    @(negedge ACLK);EventPulse=0;
    if(!BVALID||BRESP!==((address==0||address==4||address==8)?2'b00:2'b10))$fatal(1,"write join/response");
    repeat(4)begin @(negedge ACLK);if(!BVALID||AWREADY||WREADY)$fatal(1,"B retention");end
    if(address==0)for(int b=0;b<4;b++)if(mask[b])reference[8*b+:8]=data[8*b+:8];
    if(OutputValue!==reference)$fatal(1,"AXI byte mask");
    BREADY=1;@(negedge ACLK);BREADY=0;
    if(BVALID)$fatal(1,"duplicate B");
  endtask
  task automatic read_reg(input logic[5:0]address,input logic[31:0]expected,input bit bad);
    @(negedge ACLK);ARADDR=address;ARVALID=1;
    do @(posedge ACLK);while(!ARREADY);
    @(negedge ACLK);ARVALID=0;
    repeat(4)begin
      ARADDR=6'($urandom);@(negedge ACLK);
      if(!RVALID||RDATA!==expected||RRESP!==(bad?2'b10:2'b00))$fatal(1,"R snapshot/retention");
    end
    RREADY=1;@(negedge ACLK);RREADY=0;
    if(RVALID)$fatal(1,"duplicate R");
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge ACLK);ARESETn=1;
    for(int n=0;n<100;n++)write_reg(0,$urandom,4'($urandom),n%2,0);
    read_reg(0,reference,0);write_reg(1,32'hffffffff,15,0,0);
    write_reg(12,1,15,1,0);read_reg(3,0,1);
    write_reg(4,1,1,0,0);
    @(negedge ACLK);EventPulse=1;@(negedge ACLK);EventPulse=0;
    if(!Irq)$fatal(1,"event lost");read_reg(8,1,0);
    write_reg(8,1,1,0,1);if(!Irq)$fatal(1,"new event must win clear");
    read_reg(12,2,0);write_reg(8,1,1,1,0);
    if(Irq)$fatal(1,"pending clear");
    @(negedge ACLK);ARESETn=0;@(negedge ACLK);
    if(BVALID||RVALID||OutputValue||Irq)$fatal(1,"reset");
    $display("PASS AXI-Lite: AW/W ordering, masks, stalled responses, errors and clear/event race");$finish;
  end
  initial begin #100000;$fatal(1,"timeout");end
endmodule
