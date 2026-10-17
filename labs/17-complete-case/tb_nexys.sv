`timescale 1ns/1ps
module BUFG(input I, output O); assign O=I; endmodule
module tb_nexys;
  reg clk100=0; always #5 clk100=~clk100;
  reg resetn=0, scan_data=0, scan_tick=0, apply=0, capture=0;
  wire scan_out;
  nexys_video_case board(.*);
  reg [100:0] value;
  reg [205:0] snapshot;
  integer j;
  task settle; begin repeat(8) @(negedge clk100); end endtask
  task load_inputs(input [100:0] v);
    integer i;
    begin
      for(i=100;i>=0;i=i-1) begin
        scan_data=v[i]; settle; scan_tick=1; settle; scan_tick=0; settle;
      end
      apply=1; settle; apply=0; settle;
    end
  endtask
  task read_outputs;
    integer i;
    begin
      capture=1; settle; capture=0; settle;
      for(i=0;i<206;i=i+1) begin
        snapshot[i]=scan_out; scan_tick=1; settle; scan_tick=0; settle;
      end
    end
  endtask
  initial begin
    settle; resetn=1; settle;
    value=0;
      value[0 +: 5]=5'd8;
      value[5 +: 1]=1'b1;
      value[6 +: 32]=32'h80008000;
      value[38 +: 4]=4'hf;
      value[42 +: 1]=1'b1;
    load_inputs(value); read_outputs;
    if(snapshot[4]!==1 || snapshot[2 +: 2]!==0) $fatal(1,"Serial fixture write response");
    value=0;
      value[43 +: 1]=1'b1;
    load_inputs(value);
    value=0;
      value[44 +: 5]=5'd8;
      value[49 +: 1]=1'b1;
    load_inputs(value); read_outputs;
    if(snapshot[40]!==1 || snapshot[6 +: 32]!==32'h80008000 || snapshot[38 +: 2]!==0) $fatal(1,"Serial fixture register readback");
    resetn=0; settle; resetn=1; settle;
    if(board.active_inputs!==0 || board.scan_inputs!==0 || board.scan_outputs!==0) $fatal(1,"Serial fixture reset");
    $display("PASS Nexys fixture: serial load/apply, AXI write/read, output capture/shift and reset");
    $finish;
  end
  initial begin #1000000; $fatal(1,"Timeout"); end
endmodule
