`timescale 1ns/1ps
module tb_memory;
  logic clk=0;always #5 clk=~clk;
  logic reset=1,ReqValid=0,ReqWrite=0,ReqReady,RespValid,RespReady=0;
  logic[3:0]ReqAddress=0,ReqMask=0;
  logic[31:0]ReqData=0,RespData,reference[0:15];
  sync_memory #(.DEPTH(16)) dut(.*);
  integer seed,rc;
  task automatic access_word(input bit wr,input logic[3:0]address,input logic[31:0]data,input logic[3:0]mask,input bit initialized);
    logic[31:0]expected;
    expected=reference[address];
    @(negedge clk);ReqValid=1;ReqWrite=wr;ReqAddress=address;ReqData=data;ReqMask=mask;
    do @(posedge clk);while(!ReqReady);
    @(negedge clk);ReqValid=0;
    if(!RespValid)$fatal(1,"missing synchronous response");
    if(initialized&&RespData!==expected)$fatal(1,"read-first response");
    if(wr)for(int b=0;b<4;b++)if(mask[b])reference[address][8*b+:8]=data[8*b+:8];
    repeat(3)begin
      ReqAddress=4'($urandom);@(negedge clk);
      if(!RespValid||ReqReady||(initialized&&RespData!==expected))$fatal(1,"response not retained");
    end
    RespReady=1;@(negedge clk);RespReady=0;
    if(RespValid)$fatal(1,"duplicate response");
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge clk);reset=0;
    for(int a=0;a<16;a++)access_word(1,4'(a),32'(a),15,0);
    for(int n=0;n<500;n++)access_word(1'($urandom),4'($urandom),$urandom,4'($urandom),1);
    reset=1;repeat(2)@(negedge clk);reset=0;
    for(int a=0;a<16;a++)access_word(0,4'(a),0,0,1);
    $display("PASS memory: 500 random accesses, masks, read-first, stalls and reset persistence");$finish;
  end
  initial begin #100000;$fatal(1,"timeout");end
endmodule
