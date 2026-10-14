`timescale 1ns/1ps
module tb_implementation;
  logic Clk=0;always #5 Clk=~Clk;
  logic Reset=1,Enable=0,Clear=0,Valid,Overflow;
  logic[15:0]A=0,B=0,Sum;
  accumulator dut(.*);
  int seed,rc;longint unsigned total;logic[15:0]expected=0;bit v,overflow;
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(2)@(negedge Clk);
    for(int n=0;n<500;n++)begin
      Reset=(n%89==0);Clear=(n%37==0);Enable=1'($urandom);A=16'($urandom);B=16'($urandom);
      if(Reset||Clear)begin expected=0;v=0;overflow=0;end
      else if(Enable)begin total=longint'(expected)+longint'(A)+longint'(B);expected=16'(total);v=1;overflow=1'(total>>16);end
      else begin v=0;overflow=0;end
      @(negedge Clk);
      if(Sum!==expected||Valid!==v||Overflow!==overflow)$fatal(1,"implementation accumulator functional mismatch");
    end
    $display("PASS physical-flow accumulator: 500 functional cycles");$finish;
  end
endmodule
