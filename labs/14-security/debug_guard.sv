// Admission policy only: trusted lifecycle/authentication inputs, no JTAG/DM.
module debug_guard (
  input logic clk, reset,
  input logic [1:0] lifecycle,
  input logic authenticated, lock_request, halt_request, bus_request,
  output logic halt_grant, bus_grant
);
  logic locked;
  always_ff @(posedge clk) begin
    if (reset) locked <= 0;
    else if (lock_request) locked <= 1;
  end
  logic permit;
  assign permit = !reset && lifecycle == 2'b01 && authenticated && !locked && !lock_request;
  assign halt_grant = permit && halt_request;
  assign bus_grant = permit && bus_request;
`ifdef FORMAL
  logic f_seen = 0;
  logic f_locked = 0;
  always @(posedge clk) begin
    f_seen <= 1;
    if (reset) f_locked <= 0;
    else if (lock_request) f_locked <= 1;
    if (f_seen && !reset) begin
      if (f_locked || lifecycle != 2'b01 || !authenticated || lock_request) begin
        assert(!halt_grant);
        assert(!bus_grant);
      end
    end
    if (reset) begin assert(!halt_grant); assert(!bus_grant); end
  end
`endif
endmodule
