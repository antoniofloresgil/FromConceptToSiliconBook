module accumulator(
  input  logic        clk, reset, Clear, Enable,
  input  logic [15:0] Operand,
  output logic [15:0] Sum,
  output logic        Valid, Overflow);

  logic [16:0] ExtendedSum;
  assign ExtendedSum = {1'b0, Sum} + {1'b0, Operand};

  always_ff @(posedge clk) begin
    if (reset || Clear) begin
      Sum      <= '0;
      Valid    <= 1'b0;
      Overflow <= 1'b0;
    end else begin
      Valid    <= Enable;
      Overflow <= Enable && ExtendedSum[16];
      if (Enable) Sum <= ExtendedSum[15:0];
    end
  end
endmodule
