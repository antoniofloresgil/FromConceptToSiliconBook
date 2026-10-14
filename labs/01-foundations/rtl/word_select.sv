module word_select #(parameter int WIDTH = 16)(
  input  logic [WIDTH-1:0] Left, Right,
  input  logic            UseRight,
  output logic [WIDTH-1:0] Selected);

  always_comb begin
    Selected = Left;
    if (UseRight) Selected = Right;
  end
endmodule
