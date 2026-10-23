module latch_star(
  input  logic       en,
  input  logic [3:0] d,
  output logic [3:0] q);

  always @* if (en) q = d; // the same mistake with the older construct
endmodule
