module latch_comb(
  input  logic       en,
  input  logic [3:0] d,
  output logic [3:0] q);

  always_comb if (en) q = d; // q is not assigned when en is low
endmodule
