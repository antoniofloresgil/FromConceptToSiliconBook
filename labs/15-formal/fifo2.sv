// Two-entry ready/valid FIFO. BUG selects the deliberately faulty revision.
module fifo2 #(parameter WIDTH = 8, parameter BUG = 0) (
  input wire clk, reset, in_valid, out_ready,
  input wire [WIDTH-1:0] in_data,
  output wire in_ready, out_valid,
  output wire [WIDTH-1:0] out_data
`ifdef FORMAL
  , output wire [1:0] f_count,
  output wire f_head, f_tail,
  output wire [WIDTH-1:0] f_slot0, f_slot1
`endif
);
  reg [WIDTH-1:0] slot0, slot1;
  reg head, tail;
  reg [1:0] count;
  wire push = in_valid && in_ready;
  wire pop = out_valid && out_ready;
  assign in_ready = !reset && count < 2;
  assign out_valid = !reset && count != 0;
  assign out_data = head ? slot1 : slot0;
  always @(posedge clk) begin
    if (reset) begin
      head <= 0;
      tail <= 0;
      count <= 0;
    end else begin
      if (push) begin
        if (tail) slot1 <= in_data;
        else slot0 <= in_data;
        tail <= !tail;
      end
      if (pop) head <= !head;
      // The faulty priority loses the simultaneous-pop contribution.
      if (BUG) begin
        if (push) count <= count + 1'b1;
        else if (pop) count <= count - 1'b1;
      end else begin
        case ({push, pop})
          2'b10: count <= count + 1'b1;
          2'b01: count <= count - 1'b1;
          default: count <= count;
        endcase
      end
    end
  end
`ifdef FORMAL
  assign f_count = count;
  assign f_head = head;
  assign f_tail = tail;
  assign f_slot0 = slot0;
  assign f_slot1 = slot1;
`endif
endmodule
