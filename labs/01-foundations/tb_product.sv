`timescale 1ns/1ps
module tb_product;
  localparam int W=`TEST_WIDTH;
  logic clk=0;
  always #5 clk=~clk;
  logic reset=1,in_valid=0,in_ready,out_valid,out_ready=0;
  logic[W-1:0]a=0,b=0;
  logic[2*W-1:0]product;
  iterative_product #(.WIDTH(W)) dut(.*);
  integer seed,rc,checks=0;
  task automatic multiply(input logic[W-1:0]x,y);
    logic[2*W-1:0]expected;
    int edges;
    expected={{W{1'b0}},x}*{{W{1'b0}},y};
    @(negedge clk);in_valid=1;a=x;b=y;out_ready=0;
    do @(posedge clk);while(!in_ready);
    @(negedge clk);in_valid=0;edges=0;
    while(!out_valid)begin @(negedge clk);edges++;end
    if(edges!=W||product!==expected)$fatal(1,"product/latency W=%0d",W);
    repeat(3)begin @(negedge clk);if(!out_valid||product!==expected||in_ready)$fatal(1,"retention");end
    out_ready=1;@(negedge clk);out_ready=0;
    if(out_valid)$fatal(1,"duplicate result");checks++;
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge clk);reset=0;
    multiply(0,0);multiply('1,'1);multiply(1,'1);multiply('1,1);
    if(W==8)for(int x=0;x<256;x++)for(int y=0;y<256;y++)multiply(W'(x),W'(y));
    else for(int n=0;n<200;n++)multiply(W'($urandom),W'($urandom));
    @(negedge clk);in_valid=1;a='1;b='1;
    @(negedge clk);in_valid=0;reset=1;
    repeat(2)@(negedge clk);reset=0;
    repeat(W+3)@(negedge clk);if(out_valid)$fatal(1,"aborted work reappeared");
    multiply('1,'1);$display("PASS iterative product W=%0d cases=%0d",W,checks);$finish;
  end
  initial begin #20000000;$fatal(1,"timeout");end
endmodule
