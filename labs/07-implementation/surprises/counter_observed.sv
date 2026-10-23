module counter_observed(
  input  logic        clk, rst,
  input  logic [7:0]  a,
  output logic [7:0]  y,
  output logic [15:0] dbg_o);

  logic [15:0] dbg;

  always_ff @(posedge clk) begin
    if (rst) dbg <= '0;
    else     dbg <= dbg + 16'd1;
    y <= a;
  end
  assign dbg_o = dbg;
endmodule
