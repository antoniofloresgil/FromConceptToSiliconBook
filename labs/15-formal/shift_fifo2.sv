// Independent shift-register implementation of the same cycle-level contract.
module shift_fifo2 #(parameter WIDTH = 8) (
  input wire clk, reset, in_valid, out_ready,
  input wire [WIDTH-1:0] in_data,
  output wire in_ready, out_valid,
  output wire [WIDTH-1:0] out_data,
  output reg [1:0] count,
  output reg [WIDTH-1:0] first, second
);
  wire push = in_valid && in_ready;
  wire pop = out_valid && out_ready;
  assign in_ready = !reset && count < 2;
  assign out_valid = !reset && count != 0;
  assign out_data = first;
  always @(posedge clk) begin
    if (reset) count <= 0;
    else begin
      case ({push, pop})
        2'b10: begin
          if (count == 0) first <= in_data;
          else second <= in_data;
          count <= count + 1'b1;
        end
        2'b01: begin first <= second; count <= count - 1'b1; end
        2'b11: first <= in_data; // Only reachable at occupancy one.
        default: count <= count;
      endcase
    end
  end
endmodule
