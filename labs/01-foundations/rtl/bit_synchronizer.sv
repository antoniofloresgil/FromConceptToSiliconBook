module bit_synchronizer(
  input  logic clk, reset,
  input  logic AsyncIn,
  output logic SyncOut
);
  (* async_reg = "true" *) logic Meta, Sync;

  always_ff @(posedge clk) begin
    if (reset) begin
      Meta <= 1'b0;
      Sync <= 1'b0;
    end else begin
      Meta <= AsyncIn;
      Sync <= Meta;
    end
  end

  assign SyncOut = Sync;
endmodule
