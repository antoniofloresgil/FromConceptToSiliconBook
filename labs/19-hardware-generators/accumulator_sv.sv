// SPDX-License-Identifier: MIT
// Parameterized form of the book's directly written 16-bit accumulator.
module accumulator_sv #(parameter integer W=16)(
  input logic clock, reset, Clear, Enable,
  input logic [W-1:0] Operand,
  output logic [W-1:0] Sum,
  output logic Valid, Overflow
);
  logic [W:0] extended;
  assign extended={1'b0,Sum}+{1'b0,Operand};
  always_ff @(posedge clock) begin
    if(reset || Clear) begin Sum<='0;Valid<=0;Overflow<=0;end
    else begin
      Valid<=Enable;
      Overflow<=Enable && extended[W];
      if(Enable) Sum<=extended[W-1:0];
    end
  end
endmodule
