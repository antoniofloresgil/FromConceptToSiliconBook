module pwm_teaching #(
  parameter int PERIOD = 1000,
  parameter int COUNT_W = $clog2(PERIOD)
) (
  input  logic             clk, reset, Enable,
  input  logic [COUNT_W:0]  Duty,
  output logic            PWMOut
);
  logic [COUNT_W-1:0] Counter;
  logic [COUNT_W:0] ActiveDuty, LimitedDuty;
  assign LimitedDuty = Duty > (COUNT_W+1)'(PERIOD)
                       ? (COUNT_W+1)'(PERIOD) : Duty;
  assign PWMOut = Enable && ({1'b0, Counter} < ActiveDuty);
  always_ff @(posedge clk) begin
    if (reset) begin
      Counter <= '0;
      ActiveDuty <= '0;
    end else if (!Enable || Counter == COUNT_W'(PERIOD-1)) begin
      Counter <= '0;
      ActiveDuty <= LimitedDuty;
    end else Counter <= Counter + 1'b1;
  end
endmodule
