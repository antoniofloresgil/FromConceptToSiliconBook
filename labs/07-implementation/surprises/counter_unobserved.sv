module counter_unobserved(
  input  logic       clk, rst,
  input  logic [7:0] a,
  output logic [7:0] y);

  logic [15:0] dbg; // free-running debug counter that no output observes

  always_ff @(posedge clk) begin
    if (rst) dbg <= '0;
    else     dbg <= dbg + 16'd1;
    y <= a;
  end
endmodule
