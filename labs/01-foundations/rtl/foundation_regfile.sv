module foundation_regfile (
  input  logic clk, reset,
  input  logic write_enable,
  input  logic [4:0] write_address,
  input  logic [31:0] write_data,
  input  logic [4:0] read_address_a, read_address_b,
  output logic [31:0] read_data_a, read_data_b
);
  logic [31:0] registers [0:31];

  always_ff @(posedge clk) begin
    if (!reset && write_enable && write_address != 0)
      registers[write_address] <= write_data;
  end

  always_comb begin
    read_data_a = '0;
    if (read_address_a != 0) begin
      if (!reset && write_enable && write_address == read_address_a)
        read_data_a = write_data;
      else read_data_a = registers[read_address_a];
    end
    read_data_b = '0;
    if (read_address_b != 0) begin
      if (!reset && write_enable && write_address == read_address_b)
        read_data_b = write_data;
      else read_data_b = registers[read_address_b];
    end
  end
endmodule
