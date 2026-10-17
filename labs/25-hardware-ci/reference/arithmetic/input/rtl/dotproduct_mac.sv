// Exact arithmetic, independent of the transport and register protocols.
module dotproduct_mac (
 input logic signed [15:0] a,b,
 input logic signed [63:0] accumulator,
 output logic signed [63:0] next_sum
);
 logic signed [31:0] product;
 assign product = $unsigned(a) * $unsigned(b);
 assign next_sum = accumulator + {{32{product[31]}},product};
endmodule
