module tb_regression;
  reg clk = 0;
  always #5 clk = !clk;
  reg reset = 1, in_valid = 0, out_ready = 0;
  reg [7:0] in_data = 0;
  wire in_ready, out_valid;
  wire [7:0] out_data;
`ifdef FAULTY
  localparam BUG = 1;
`else
  localparam BUG = 0;
`endif
  fifo2 #(.BUG(BUG)) dut (.*);
  task drive(input reg valid, ready, input reg [7:0] data);
    @(negedge clk);
    in_valid = valid; out_ready = ready; in_data = data;
    @(posedge clk); #1;
  endtask
  initial begin
    repeat (2) @(negedge clk);
    reset = 0;
    drive(1, 0, 8'h31); // Occupancy 0 -> 1.
    if (!out_valid || out_data != 8'h31) $fatal(1, "first item missing");
    drive(1, 1, 8'ha7); // Replace oldest; occupancy must stay one.
    if (!out_valid || out_data != 8'ha7) $fatal(1, "replacement incorrect");
    drive(0, 1, 0); // Remove replacement; queue must now be empty.
    if (out_valid) $fatal(1, "simultaneous push/pop created a phantom item");
    $display("PASS FIFO regression: exchange then drain, no phantom item");
    $finish;
  end
  initial begin #1000; $fatal(1, "timeout"); end
endmodule
