`timescale 1ns/1ps
module tb_apb;
  logic PCLK=0;always #5 PCLK=~PCLK;
  logic PRESETn=0,PSEL=0,PENABLE=0,PWRITE=0,PREADY,PSLVERR,Irq;
  logic[7:0]PADDR=0,PinIn=0,PinOut,PinEnable;
  logic[31:0]PWDATA=0,PRDATA;
  logic[3:0]PSTRB=0;
  gpio_teaching_apb dut(.*);
  integer seed,rc;
  task automatic write_reg(input logic[7:0]address,input logic[31:0]data,input logic[3:0]mask,input bit bad);
    @(negedge PCLK);PSEL=1;PWRITE=1;PADDR=address;PWDATA=data;PSTRB=mask;PENABLE=0;
    @(negedge PCLK);PENABLE=1;#1;
    if(!PREADY||PSLVERR!==bad)$fatal(1,"APB write error contract");
    @(negedge PCLK);PSEL=0;PENABLE=0;
  endtask
  task automatic read_reg(input logic[7:0]address,input logic[31:0]expected,input bit bad);
    @(negedge PCLK);PSEL=1;PWRITE=0;PADDR=address;PENABLE=0;
    @(negedge PCLK);PENABLE=1;#1;
    if(!PREADY||PSLVERR!==bad||PRDATA!==expected)$fatal(1,"APB read %h expected %h got %h",address,expected,PRDATA);
    @(negedge PCLK);PSEL=0;PENABLE=0;
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge PCLK);PRESETn=1;
    write_reg(8'h08,255,1,0);if(PinEnable!==255)$fatal(1,"output enable");
    for(int n=0;n<100;n++)begin
      logic[7:0]old_value,new_value;logic[3:0]mask;
      old_value=PinOut;new_value=8'($urandom);mask=4'($urandom);
      write_reg(8'h0c,{24'b0,new_value},mask,0);
      if(PinOut!==(mask[0]?new_value:old_value))$fatal(1,"GPIO byte mask");
    end
    read_reg(8'h0c,{24'b0,PinOut},0);
    write_reg(8'h00,255,15,1);read_reg(8'hff,0,1);
    write_reg(8'h04,1,1,0);write_reg(8'h18,1,1,0);
    PinIn=1;repeat(5)@(negedge PCLK);if(!Irq)$fatal(1,"rising event not retained");
    read_reg(8'h1c,1,0);write_reg(8'h1c,1,1,0);
    if(Irq)$fatal(1,"W1C did not clear");
    @(negedge PCLK);PRESETn=0;@(negedge PCLK);
    if(PinOut||PinEnable||Irq)$fatal(1,"GPIO reset");
    $display("PASS GPIO APB: masks, invalid offsets, synchronized event and W1C");$finish;
  end
  initial begin #50000;$fatal(1,"timeout");end
endmodule
