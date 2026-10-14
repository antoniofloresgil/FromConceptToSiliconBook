module rv_slice #(
  parameter int DATA_WIDTH = 32
) (
  input  logic clk, rst_n,
  input  logic in_valid,
  output logic in_ready,
  input  logic [DATA_WIDTH-1:0] in_data,
  output logic out_valid,
  input  logic out_ready,
  output logic [DATA_WIDTH-1:0] out_data
);
  logic full_q;
  logic [DATA_WIDTH-1:0] data_q;

  assign in_ready = rst_n && (!full_q || out_ready);
  assign out_valid = rst_n && full_q;
  assign out_data = data_q;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      full_q <= 1'b0;
      data_q <= '0;
    end else if (in_ready) begin
      full_q <= in_valid;
      if (in_valid) data_q <= in_data;
    end
  end
endmodule
