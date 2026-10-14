module foundation_alu (
  input  logic [31:0] a, b,
  input  logic [3:0] operation,
  output logic [31:0] result,
  output logic operation_valid
);
  always_comb begin
    result = '0;
    operation_valid = 1'b1;
    case (operation)
      4'd0: result = a + b;
      4'd1: result = a - b;
      4'd2: result = a & b;
      4'd3: result = a | b;
      4'd4: result = a ^ b;
      4'd5: result = a << b[4:0];
      4'd6: result = a >> b[4:0];
      4'd7: result = $signed(a) >>> b[4:0];
      4'd8: result = {31'b0, ($signed(a) < $signed(b))};
      4'd9: result = {31'b0, (a < b)};
      default: operation_valid = 1'b0;
    endcase
  end
endmodule
