module reset_release(
  input  logic clk,
  input  logic ResetNAsync,
  output logic ResetN
);
  (* async_reg = "true" *) logic [1:0] Release;

  always_ff @(posedge clk or negedge ResetNAsync) begin
    if (!ResetNAsync) Release <= 2'b00;
    else              Release <= {Release[0], 1'b1};
  end

  assign ResetN = Release[1];
endmodule
