module delayed_memory #(
  parameter int AW = 6,
  parameter int DW = 32,
  parameter int IW = 8
) (
  input  logic clk, reset,
  input  logic req_valid,
  output logic req_ready,
  input  logic req_write,
  input  logic [AW-1:0] req_addr,
  input  logic [IW-1:0] req_id,
  input  logic [DW-1:0] req_data,
  input  logic [DW/8-1:0] req_strb,
  output logic rsp_valid,
  input  logic rsp_ready,
  output logic rsp_write,
  output logic [IW-1:0] rsp_id,
  output logic [DW-1:0] rsp_data
);
  logic [DW-1:0] memory [0:(1<<AW)-1];
  logic busy;
  logic [2:0] delay_left;

  assign req_ready = !reset && !busy && !rsp_valid;

  always_ff @(posedge clk) begin
    if (reset) begin
      busy       <= 1'b0;
      delay_left <= '0;
      rsp_valid  <= 1'b0;
      rsp_write  <= 1'b0;
      rsp_id     <= '0;
      rsp_data   <= '0;
    end else begin
      if (rsp_valid && rsp_ready) rsp_valid <= 1'b0;
      if (req_valid && req_ready) begin
        busy       <= 1'b1;
        delay_left <= {1'b0, req_addr[1:0]};
        rsp_write  <= req_write;
        rsp_id     <= req_id;
        if (req_write) begin
          rsp_data <= '0;
          for (int b = 0; b < DW/8; b++)
            if (req_strb[b])
              memory[req_addr][8*b +: 8] <= req_data[8*b +: 8];
        end else begin
          rsp_data <= memory[req_addr];
        end
      end else if (busy) begin
        if (delay_left == 0) begin
          busy      <= 1'b0;
          rsp_valid <= 1'b1;
        end else begin
          delay_left <= delay_left - 1'b1;
        end
      end
    end
  end
endmodule
