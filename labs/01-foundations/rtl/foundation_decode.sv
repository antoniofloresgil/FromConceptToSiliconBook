module foundation_decode (
  input  logic [31:0] instruction,
  output logic legal,
  output logic uses_rs1, uses_rs2,
  output logic writes_rd,
  output logic load_word, store_word, branch_equal,
  output logic [2:0] immediate_kind
);
  always_comb begin
    legal = 1'b0;
    uses_rs1 = 1'b0;
    uses_rs2 = 1'b0;
    writes_rd = 1'b0;
    load_word = 1'b0;
    store_word = 1'b0;
    branch_equal = 1'b0;
    immediate_kind = 3'd0;
    case (instruction[6:0])
      7'b0110011: begin
        if (instruction[14:12] == 3'b000 &&
            instruction[31:25] == 7'b0000000) begin
          legal = 1'b1;
          uses_rs1 = 1'b1; uses_rs2 = 1'b1; writes_rd = 1'b1;
        end
      end
      7'b0010011: begin
        if (instruction[14:12] == 3'b000) begin
          legal = 1'b1; uses_rs1 = 1'b1; writes_rd = 1'b1;
        end
      end
      7'b0000011: begin
        if (instruction[14:12] == 3'b010) begin
          legal = 1'b1; uses_rs1 = 1'b1; writes_rd = 1'b1;
          load_word = 1'b1;
        end
      end
      7'b0100011: begin
        if (instruction[14:12] == 3'b010) begin
          legal = 1'b1; uses_rs1 = 1'b1; uses_rs2 = 1'b1;
          store_word = 1'b1; immediate_kind = 3'd1;
        end
      end
      7'b1100011: begin
        if (instruction[14:12] == 3'b000) begin
          legal = 1'b1; uses_rs1 = 1'b1; uses_rs2 = 1'b1;
          branch_equal = 1'b1; immediate_kind = 3'd2;
        end
      end
      7'b0110111: begin
        legal = 1'b1; writes_rd = 1'b1; immediate_kind = 3'd3;
      end
      default: begin end
    endcase
  end
endmodule
