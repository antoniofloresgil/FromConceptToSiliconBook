module sync_memory #(
  parameter int WIDTH = 32,
  parameter int DEPTH = 256,
  parameter int ADDR_W = $clog2(DEPTH)
) (
  input  logic              clk, reset,
  input  logic              ReqValid, ReqWrite,
  output logic              ReqReady,
  input  logic [ADDR_W-1:0]  ReqAddress,
  input  logic [WIDTH-1:0]   ReqData,
  input  logic [WIDTH/8-1:0] ReqMask,
  output logic              RespValid,
  input  logic              RespReady,
  output logic [WIDTH-1:0]   RespData
);
  logic [WIDTH-1:0] Memory [0:DEPTH-1];
  logic Accept;
  assign ReqReady = !reset && !RespValid;
  assign Accept = ReqValid && ReqReady;

  always_ff @(posedge clk) begin
    if (reset) RespValid <= 1'b0;
    else begin
      if (RespValid && RespReady) RespValid <= 1'b0;
      if (Accept) RespValid <= 1'b1;
    end
  end

  // No reset on the array or the memory read-data register.
  always_ff @(posedge clk) begin
    if (Accept) begin
      RespData <= Memory[ReqAddress];
      if (ReqWrite)
        for (int b = 0; b < WIDTH/8; b++)
          if (ReqMask[b])
            Memory[ReqAddress][8*b +: 8] <= ReqData[8*b +: 8];
    end
  end
endmodule
