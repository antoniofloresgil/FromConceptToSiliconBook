module ram_async(
  input  logic       clk, we,
  input  logic [9:0] addr,
  input  logic [7:0] din,
  output logic [7:0] dout);

  logic [7:0] mem [1024];

  always_ff @(posedge clk) if (we) mem[addr] <= din;
  assign dout = mem[addr]; // asynchronous read
endmodule
