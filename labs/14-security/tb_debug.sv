module tb_debug;
  logic clk=0, reset=1, authenticated=0, lock_request=0, halt_request=1, bus_request=1;
  logic [1:0] lifecycle=0;
  logic halt_grant, bus_grant;
  debug_guard dut(.*);
  always #5 clk=~clk;
  task check(input logic expected);
    #1;
    if (halt_grant !== expected || bus_grant !== expected) $fatal(1,"Debug policy violation");
  endtask
  initial begin
    check(0);
    @(negedge clk);reset=0;check(0);
    lifecycle=1;check(0);authenticated=1;check(1);
    lock_request=1;check(0);
    @(negedge clk);lock_request=0;check(0);
    authenticated=0;check(0);authenticated=1;check(0);
    @(negedge clk);reset=1;lifecycle=2;check(0);
    @(negedge clk);reset=0;check(0);
    lifecycle=3;check(0);lifecycle=0;check(0);
    $display("PASS debug admission: auth, immediate/sticky lock, production reset and invalid lifecycle");
    $finish;
  end
endmodule
