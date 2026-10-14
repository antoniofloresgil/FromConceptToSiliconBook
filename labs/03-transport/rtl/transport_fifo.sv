module transport_fifo #(
  parameter int WIDTH = 32,
  parameter int DEPTH = 4,
  localparam int PW = $clog2(DEPTH),
  localparam int CW = $clog2(DEPTH + 1)
) (
  input  logic clk, reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic [WIDTH-1:0] in_data,
  output logic out_valid,
  input  logic out_ready,
  output logic [WIDTH-1:0] out_data
);
  logic [WIDTH-1:0] storage [0:DEPTH-1];
  logic [PW-1:0] head, tail;
  logic [CW-1:0] count;
  logic push, pop;

  assign in_ready  = !reset && (count < CW'(DEPTH));
  assign out_valid = !reset && (count != '0);
  assign out_data  = storage[head];
  assign push = in_valid && in_ready;
  assign pop  = out_valid && out_ready;

  always_ff @(posedge clk) begin
    if (reset) begin
      head  <= '0;
      tail  <= '0;
      count <= '0;
    end else begin
      if (push) begin
        storage[tail] <= in_data;
        tail <= (tail == PW'(DEPTH-1)) ? '0 : tail + 1'b1;
      end
      if (pop)
        head <= (head == PW'(DEPTH-1)) ? '0 : head + 1'b1;
      case ({push, pop})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
