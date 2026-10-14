`timescale 1ns/1ps
module tb_fifo_pwm;
  logic clk=0;always #5 clk=~clk;
  logic reset=1,PushValid=0,PushReady,PopValid,PopReady=0;
  logic[7:0]PushData=0,PopData,reference[0:8191];
  logic[3:0]Level;
  byte_fifo fifo(.*);
  logic Enable=0,PWMOut;
  logic[3:0]Duty=0;
  pwm_teaching #(.PERIOD(8)) pwm(.*);
  int head=0,tail=0,seed,rc;bit accepted=0;
  always @(posedge clk)begin
    accepted=0;
    if(reset)begin head=0;tail=0;end
    else begin
      if(PushValid&&PushReady)begin reference[tail]=PushData;tail++;accepted=1;end
      if(PopValid&&PopReady)begin if(PopData!==reference[head]||head>=tail)$fatal(1,"byte FIFO ordering");head++;end
    end
  end
  task automatic duty_test(input int d);
    int highs;
    @(negedge clk);Enable=0;Duty=4'(d);@(negedge clk);Enable=1;
    highs=0;
    repeat(8)begin #1;if(PWMOut)highs++;@(negedge clk);end
    if(highs!=(d>8?8:d))$fatal(1,"PWM duty %0d got %0d",d,highs);
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge clk);reset=0;
    for(int n=0;n<2000;n++)begin
      if(!PushValid||accepted)begin PushValid=1'($urandom);PushData=8'($urandom);end
      PopReady=1'($urandom);#1;
      if(Level!==4'(tail-head))$fatal(1,"byte FIFO level");
      @(negedge clk);
    end
    while(PushValid&&!accepted)begin PopReady=1;@(negedge clk);end
    PushValid=0;PopReady=1;wait(head==tail);
    duty_test(0);duty_test(1);duty_test(4);duty_test(8);duty_test(15);
    @(negedge clk);Enable=0;Duty=2;@(negedge clk);Enable=1;
    repeat(3)@(negedge clk);Duty=7;
    if(pwm.ActiveDuty!==2)$fatal(1,"midperiod duty changed");
    repeat(5)@(negedge clk);if(pwm.ActiveDuty!==7)$fatal(1,"boundary duty not applied");
    Enable=0;#1;if(PWMOut)$fatal(1,"disabled PWM");
    $display("PASS byte FIFO: 2000 cycles; PWM: duty endpoints, clamp and shadow update");$finish;
  end
  initial begin #100000;$fatal(1,"timeout");end
endmodule
