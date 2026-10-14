module iterative_product #(
  parameter int WIDTH = 32,
  localparam int CW = (WIDTH < 2) ? 1 : $clog2(WIDTH + 1)
) (
  input  logic clk, reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic [WIDTH-1:0] a, b,
  output logic out_valid,
  input  logic out_ready,
  output logic [2*WIDTH-1:0] product
);
  logic busy, result_pending;
  logic [CW-1:0] remaining;
  logic [WIDTH-1:0] multiplier;
  logic [2*WIDTH-1:0] shifted, accumulator, next_accumulator;

  assign in_ready = !reset && !busy && !result_pending;
  assign out_valid = !reset && result_pending;
  assign next_accumulator = accumulator +
                            (multiplier[0] ? shifted : '0);

  always_ff @(posedge clk) begin
    if (reset) begin
      busy <= 1'b0;
      result_pending <= 1'b0;
      remaining <= '0;
      multiplier <= '0;
      shifted <= '0;
      accumulator <= '0;
      product <= '0;
    end else begin
      if (result_pending && out_ready) result_pending <= 1'b0;
      if (in_valid && in_ready) begin
        busy <= 1'b1;
        remaining <= CW'(WIDTH);
        multiplier <= b;
        shifted <= {{WIDTH{1'b0}}, a};
        accumulator <= '0;
      end else if (busy) begin
        accumulator <= next_accumulator;
        shifted <= shifted << 1;
        multiplier <= multiplier >> 1;
        remaining <= remaining - 1'b1;
        if (remaining == 1) begin
          busy <= 1'b0;
          product <= next_accumulator;
          result_pending <= 1'b1;
        end
      end
    end
  end
endmodule
