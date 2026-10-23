module latch_fixed(
  input  logic       en,
  input  logic [3:0] d,
  output logic [3:0] q);

  always_comb begin
    q = '0;            // default assignment on every path
    if (en) q = d;
  end
endmodule
