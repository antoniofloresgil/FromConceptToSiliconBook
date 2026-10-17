module harness #(parameter BUG = 0, parameter QUIET = 0, parameter DRAIN = 0) (
  input wire clk, reset, in_valid, out_ready,
  input wire [7:0] in_data,
  output wire goal,
  output wire [1:0] occupancy,
  output wire in_ready, out_valid,
  output wire [7:0] out_data
);
  wire head, tail;
  wire [7:0] slot0, slot1;
  fifo2 #(.BUG(BUG)) dut (
    .clk(clk), .reset(reset), .in_valid(in_valid), .out_ready(out_ready),
    .in_data(in_data), .in_ready(in_ready), .out_valid(out_valid), .out_data(out_data),
    .f_count(occupancy), .f_head(head), .f_tail(tail),
    .f_slot0(slot0), .f_slot1(slot1)
  );
  wire ref_ready, ref_valid;
  wire [7:0] ref_data, first, second;
  wire [1:0] ref_count;
  shift_fifo2 reference (
    .clk(clk), .reset(reset), .in_valid(in_valid), .out_ready(out_ready),
    .in_data(in_data), .in_ready(ref_ready), .out_valid(ref_valid), .out_data(ref_data),
    .count(ref_count), .first(first), .second(second)
  );
  reg past_valid = 0;
  reg seen_full = 0, seen_exchange = 0, seen_drained = 0;
  wire push = in_valid && in_ready;
  wire pop = out_valid && out_ready;
  assign goal = seen_full && seen_exchange && seen_drained;
  always @(posedge clk) begin
    past_valid <= 1;
    // Only the first sampled edge must reset; later resets remain symbolic.
    if (!past_valid) assume(reset);
    // A producer owns and retains a pending request until acceptance or reset.
    if (past_valid && !$past(reset) && !reset && $past(in_valid && !in_ready)) begin
      assume(in_valid);
      assume(in_data == $past(in_data));
    end
    if (QUIET) assume(!in_valid); // Deliberate overconstraint experiment.
    if (DRAIN && seen_full && !reset) begin
      assume(!in_valid);
      assume(out_ready);
    end
    if (reset) begin
      seen_full <= 0;
      seen_exchange <= 0;
      seen_drained <= 0;
    end else begin
      if (occupancy == 2) seen_full <= 1;
      if (push && pop) seen_exchange <= 1;
      if (seen_full && occupancy == 0) seen_drained <= 1;
    end
    if (past_valid) begin
      // Safety and the inductive representation relation.
      assert(occupancy <= 2);
      assert(occupancy == ref_count);
      assert((head == tail) == (occupancy != 1));
      assert(in_ready == ref_ready);
      assert(out_valid == ref_valid);
      if (occupancy > 0) assert((head ? slot1 : slot0) == first);
      if (occupancy == 2) assert((head ? slot0 : slot1) == second);
      // Output data is observable only when valid; empty data is unspecified.
      if (out_valid) assert(out_data == ref_data);
      if (!$past(reset) && !reset && $past(out_valid && !out_ready)) begin
        assert(out_valid);
        assert(out_data == $past(out_data));
      end
      // Bounded progress: each ready/no-new-input edge removes one item.
      if (!$past(reset) && !reset && $past(out_ready && !in_valid)) begin
        if ($past(occupancy) > 0) assert(occupancy == $past(occupancy) - 1);
        else assert(occupancy == 0);
      end
    end
    cover(goal);
  end
endmodule
