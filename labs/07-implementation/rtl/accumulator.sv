module accumulator (
    input  logic        Clk,
    input  logic        Reset,
    input  logic        Enable,
    input  logic        Clear,
    input  logic [15:0] A,
    input  logic [15:0] B,
    output logic [15:0] Sum,
    output logic        Valid,
    output logic        Overflow
);
  logic [16:0] next_sum;
  always_comb next_sum = {1'b0, Sum} + {1'b0, A} + {1'b0, B};
  always_ff @(posedge Clk) begin
    if (Reset || Clear) begin
      Sum      <= '0;
      Valid    <= 1'b0;
      Overflow <= 1'b0;
    end else if (Enable) begin
      Sum      <= next_sum[15:0];
      Valid    <= 1'b1;
      Overflow <= next_sum[16];
    end else begin
      Valid    <= 1'b0;
      Overflow <= 1'b0;
    end
  end
endmodule
