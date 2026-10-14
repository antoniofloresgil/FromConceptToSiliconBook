module sample_pipeline #(parameter int WIDTH = 16)(
  input  logic             clk, reset, Enable,
  input  logic [WIDTH-1:0]  Sample,
  output logic [WIDTH-1:0]  StageOne, StageTwo);

  always_ff @(posedge clk) begin
    if (reset) begin
      StageOne <= '0;
      StageTwo <= '0;
    end else if (Enable) begin
      StageOne <= Sample;
      StageTwo <= StageOne;
    end
  end
endmodule
