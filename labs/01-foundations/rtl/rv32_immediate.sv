module rv32_immediate (
  input  logic [31:0] instruction,
  input  logic [2:0] kind,
  output logic [31:0] immediate,
  output logic format_valid
);
  always_comb begin
    immediate = '0;
    format_valid = 1'b1;
    case (kind)
      3'd0: immediate = {{20{instruction[31]}}, instruction[31:20]};
      3'd1: immediate = {{20{instruction[31]}}, instruction[31:25],
                         instruction[11:7]};
      3'd2: immediate = {{19{instruction[31]}}, instruction[31],
                         instruction[7], instruction[30:25],
                         instruction[11:8], 1'b0};
      3'd3: immediate = {instruction[31:12], 12'b0};
      3'd4: immediate = {{11{instruction[31]}}, instruction[31],
                         instruction[19:12], instruction[20],
                         instruction[30:21], 1'b0};
      default: format_valid = 1'b0;
    endcase
  end
endmodule
