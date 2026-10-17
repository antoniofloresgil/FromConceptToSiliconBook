// SPDX-License-Identifier: MIT
module tb;
  parameter integer W=16;
  logic clock=0,reset,Clear,Enable;
  logic [W-1:0] Operand,sv_sum,chisel_sum,expected_sum;
  logic sv_valid,sv_overflow,chisel_valid,chisel_overflow;
  wire [15:0] original_sum;
  wire original_valid,original_overflow;
  if(W==16) begin
    accumulator original(.clk(clock),.reset,.Clear,.Enable,.Operand,
      .Sum(original_sum),.Valid(original_valid),.Overflow(original_overflow));
  end
  integer r,c,e,v,o,read_count,file,cycle=0;
  string vectors;
  accumulator_sv #(.W(W)) direct(.clock,.reset,.Clear,.Enable,.Operand,
    .Sum(sv_sum),.Valid(sv_valid),.Overflow(sv_overflow));
  Accumulator generated(.clock,.reset,.Clear,.Enable,.Operand,
    .Sum(chisel_sum),.Valid(chisel_valid),.Overflow(chisel_overflow));
  initial begin
    if(!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"Missing vectors");
    file=$fopen(vectors,"r");if(!file)$fatal(1,"Cannot open vectors");
    while(!$feof(file)) begin
      read_count=$fscanf(file,"%d %d %d %h %h %d %d\n",r,c,e,Operand,expected_sum,v,o);
      if(read_count!=7)$fatal(1,"Malformed vector");
      reset=r;Clear=c;Enable=e;
      #5;clock=1;#1;
      if({sv_sum,sv_valid,sv_overflow}!=={expected_sum,v[0],o[0]})
        $fatal(1,"DIRECT_MISMATCH cycle=%0d",cycle);
      if(W==16 && {original_sum,original_valid,original_overflow}!=={expected_sum,v[0],o[0]})
        $fatal(1,"ORIGINAL_MISMATCH cycle=%0d",cycle);
      if({chisel_sum,chisel_valid,chisel_overflow}!=={expected_sum,v[0],o[0]})
        $fatal(1,"GENERATED_MISMATCH cycle=%0d",cycle);
      #4;clock=0;cycle=cycle+1;
    end
    $fclose(file);$display("GENERATOR_COMPARISON_PASS width=%0d cycles=%0d",W,cycle);$finish;
  end
endmodule
