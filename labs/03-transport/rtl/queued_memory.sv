module queued_memory #(
  parameter int AW = 6,
  parameter int DW = 32,
  parameter int IW = 8,
  parameter int QDEPTH = 4,
  localparam int QW = 1 + AW + IW + DW + DW/8,
  localparam int RW = 1 + IW + DW
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
  logic [QW-1:0] q_payload;
  logic q_valid, q_ready, m_write;
  logic [AW-1:0] m_addr;
  logic [IW-1:0] m_id;
  logic [DW-1:0] m_data;
  logic [DW/8-1:0] m_strb;
  logic m_rsp_valid, m_rsp_ready, m_rsp_write;
  logic [IW-1:0] m_rsp_id;
  logic [DW-1:0] m_rsp_data;
  logic [RW-1:0] r_payload;

  transport_fifo #(.WIDTH(QW), .DEPTH(QDEPTH)) requests (
    .clk, .reset, .in_valid(req_valid), .in_ready(req_ready),
    .in_data({req_write, req_addr, req_id, req_data, req_strb}),
    .out_valid(q_valid), .out_ready(q_ready), .out_data(q_payload)
  );
  assign {m_write, m_addr, m_id, m_data, m_strb} = q_payload;

  delayed_memory #(.AW(AW), .DW(DW), .IW(IW)) service (
    .clk, .reset,
    .req_valid(q_valid), .req_ready(q_ready), .req_write(m_write),
    .req_addr(m_addr), .req_id(m_id), .req_data(m_data),
    .req_strb(m_strb), .rsp_valid(m_rsp_valid),
    .rsp_ready(m_rsp_ready), .rsp_write(m_rsp_write),
    .rsp_id(m_rsp_id), .rsp_data(m_rsp_data)
  );

  transport_fifo #(.WIDTH(RW), .DEPTH(QDEPTH)) responses (
    .clk, .reset,
    .in_valid(m_rsp_valid), .in_ready(m_rsp_ready),
    .in_data({m_rsp_write, m_rsp_id, m_rsp_data}),
    .out_valid(rsp_valid), .out_ready(rsp_ready),
    .out_data(r_payload)
  );
  assign {rsp_write, rsp_id, rsp_data} = r_payload;
endmodule
