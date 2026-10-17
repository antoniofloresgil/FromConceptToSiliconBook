// SPDX-License-Identifier: MIT
// Power-of-two, fall-through FIFO. Common asynchronous reset flushes BOTH sides.
// Original teaching RTL; registered Gray pointers with local flag comparison.
module async_fifo #(
  parameter integer DATA_W = 8,
  parameter integer ADDR_BITS = 2
) (
  input  logic wclk, rclk, arst_n,
  input  logic w_valid,
  output logic w_ready,
  input  logic [DATA_W-1:0] w_data,
  output logic r_valid,
  input  logic r_ready,
  output logic [DATA_W-1:0] r_data
);
  localparam integer DEPTH = 1 << ADDR_BITS;
  localparam integer PTR_W = ADDR_BITS + 1;
  // For ADDR_BITS=1 this is 2'b11; no negative-width part-select is needed.
  localparam logic [PTR_W-1:0] FULL_MASK = {2'b11, {(ADDR_BITS-1){1'b0}}};
  if (DATA_W < 1 || ADDR_BITS < 1) begin : bad_parameters
    initial $fatal(1, "DATA_W>=1 and ADDR_BITS>=1 are required");
  end

  (* ASYNC_REG = "TRUE", async_reg = "true", keep = "true" *)
  logic [1:0] w_release, r_release;
  wire wrst_n = w_release[1];
  wire rrst_n = r_release[1];
  always_ff @(posedge wclk or negedge arst_n)
    if (!arst_n) w_release <= 0;
    else         w_release <= {w_release[0], 1'b1};
  always_ff @(posedge rclk or negedge arst_n)
    if (!arst_n) r_release <= 0;
    else         r_release <= {r_release[0], 1'b1};

  logic [PTR_W-1:0] w_bin, w_gray, r_bin, r_gray;
  logic [PTR_W-1:0] w_bin_next, w_gray_next, r_bin_next, r_gray_next;
  (* ASYNC_REG = "TRUE", async_reg = "true", keep = "true" *)
  logic [PTR_W-1:0] wq1_rgray, wq2_rgray, rq1_wgray, rq2_wgray;
  logic w_full, r_empty;
  wire w_take = w_valid && w_ready;
  wire r_take = r_valid && r_ready;
  assign w_ready = wrst_n && !w_full;
  assign r_valid = rrst_n && !r_empty;
  assign w_bin_next = w_bin + {{(PTR_W-1){1'b0}}, w_take};
  assign r_bin_next = r_bin + {{(PTR_W-1){1'b0}}, r_take};
  assign w_gray_next = w_bin_next;
  assign r_gray_next = (r_bin_next >> 1) ^ r_bin_next;

  always_ff @(posedge wclk or negedge wrst_n) begin
    if (!wrst_n) begin wq1_rgray <= 0; wq2_rgray <= 0; end
    else begin wq1_rgray <= r_gray; wq2_rgray <= wq1_rgray; end
  end
  always_ff @(posedge rclk or negedge rrst_n) begin
    if (!rrst_n) begin rq1_wgray <= 0; rq2_wgray <= 0; end
    else begin rq1_wgray <= w_gray; rq2_wgray <= rq1_wgray; end
  end
  always_ff @(posedge wclk or negedge wrst_n) begin
    if (!wrst_n) begin w_bin <= 0; w_gray <= 0; w_full <= 0; end
    else begin
      w_bin <= w_bin_next;
      w_gray <= w_gray_next;
      w_full <= (w_gray_next == (wq2_rgray ^ FULL_MASK));
    end
  end
  always_ff @(posedge rclk or negedge rrst_n) begin
    if (!rrst_n) begin r_bin <= 0; r_gray <= 0; r_empty <= 1; end
    else begin
      r_bin <= r_bin_next;
      r_gray <= r_gray_next;
      r_empty <= (r_gray_next == rq2_wgray);
    end
  end

  // Deliberately no array reset. Validity is established by pointer publication.
  // This asynchronous read is a small register/LUTRAM teaching implementation,
  // not a portable synchronous BRAM or characterized ASIC SRAM wrapper.
  logic [DATA_W-1:0] mem [0:DEPTH-1];
  always_ff @(posedge wclk)
    if (w_take) mem[w_bin[ADDR_BITS-1:0]] <= w_data;
  assign r_data = r_valid ? mem[r_bin[ADDR_BITS-1:0]] : '0;
endmodule
