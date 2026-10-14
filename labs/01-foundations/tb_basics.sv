`timescale 1ns/1ps
module tb_basics;
  logic clk=0;always #5 clk=~clk;
  logic reset=1,Enable=0,Start=0,Complete=0,Busy;
  logic[15:0]Sample=0,StageOne,StageTwo,Left=16'h1234,Right=16'habcd,Selected;
  logic UseRight=0,AsyncIn=0,SyncOut,ResetNAsync=0,ResetN;
  sample_pipeline pipeline(.*);request_control control(.*);
  word_select mux(.*);bit_synchronizer sync_bit(.*);reset_release release_reset(.*);
  logic rst_n=0,in_valid=0,in_ready,out_valid,out_ready=0;
  logic[31:0]in_data=0,out_data;
  rv_slice slice(.*);
  initial begin
    #1;if(Selected!==Left)$fatal(1,"mux left");UseRight=1;#1;
    if(Selected!==Right)$fatal(1,"mux right");
    repeat(2)@(negedge clk);reset=0;rst_n=1;ResetNAsync=1;
    Enable=1;Sample=16'h11;Start=1;AsyncIn=1;in_valid=1;in_data=32'h11;
    @(negedge clk);
    if(StageOne!==16'h11||StageTwo!==0||!Busy||SyncOut!==0||ResetN!==0)$fatal(1,"first edge");
    Start=0;Sample=16'h22;in_valid=0;
    @(negedge clk);
    if(StageOne!==16'h22||StageTwo!==16'h11||!SyncOut||!ResetN)$fatal(1,"second edge");
    if(!out_valid||out_data!==32'h11||in_ready)$fatal(1,"slice stall");
    Enable=0;Sample=16'h33;Complete=1;
    repeat(3)@(negedge clk);
    if(StageOne!==16'h22||StageTwo!==16'h11||Busy||out_data!==32'h11)$fatal(1,"hold/control");
    out_ready=1;in_valid=1;in_data=32'h22;
    @(negedge clk);if(!out_valid||out_data!==32'h22)$fatal(1,"slice replacement");
    in_valid=0;@(negedge clk);if(out_valid)$fatal(1,"slice drain");
    #1;rst_n=0;ResetNAsync=0;#1;
    if(out_valid||in_ready||ResetN)$fatal(1,"asynchronous assertion");
    $display("PASS basic RTL, enables, handshake and reset release (digital simulation)");$finish;
  end
  initial begin #10000;$fatal(1,"timeout");end
endmodule
