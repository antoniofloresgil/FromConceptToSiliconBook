module byte_fifo #(
  parameter int DEPTH = 8,
  parameter int PTR_W = $clog2(DEPTH)
) (
  input  logic             clk, reset,
  input  logic             PushValid,
  output logic             PushReady,
  input  logic [7:0]       PushData,
  output logic             PopValid,
  input  logic             PopReady,
  output logic [7:0]       PopData,
  output logic [PTR_W:0]   Level
);
  logic [7:0] Storage [0:DEPTH-1];
  logic [PTR_W-1:0] WritePointer, ReadPointer;
  logic Push, Pop;
  assign PushReady = !reset && Level != (PTR_W+1)'(DEPTH);
  assign PopValid = !reset && Level != '0;
  assign PopData = Storage[ReadPointer];
  assign Push = PushValid && PushReady;
  assign Pop = PopValid && PopReady;

  always_ff @(posedge clk) begin
    if (reset) begin
      WritePointer <= '0;
      ReadPointer <= '0;
      Level <= '0;
    end else begin
      if (Push) begin
        Storage[WritePointer] <= PushData;
        WritePointer <= WritePointer + 1'b1;
      end
      if (Pop) ReadPointer <= ReadPointer + 1'b1;
      case ({Push, Pop})
        2'b10: Level <= Level + 1'b1;
        2'b01: Level <= Level - 1'b1;
        default: begin end
      endcase
    end
  end
endmodule
