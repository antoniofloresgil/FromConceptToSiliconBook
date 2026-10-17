// SPDX-License-Identifier: MIT
module tb_async_fifo;
  timeunit 1ns;
  timeprecision 1ps;
  parameter integer DATA_W=8, ADDR_BITS=2;
  localparam integer DEPTH=1<<ADDR_BITS, PTR_W=ADDR_BITS+1;
  logic wclk=0,rclk=0,arst_n=1,w_valid=0,w_ready,r_valid,r_ready=0;
  logic [DATA_W-1:0] w_data=0,r_data;
  bit w_run=0,r_run=0,produce=0,consume=0,random_mode=0;
  integer wh=5,rh=7,rphase=2,seed=2026;
  integer tail=0,head=0,dropped=0,epochs=0,write_wraps=0,read_wraps=0;
  integer write_stalls=0,read_stalls=0,read_jumps=0,write_jumps=0;
  integer simultaneous=0;
  time last_write=0,last_read=0;
  logic [DATA_W-1:0] expected[0:65535];
  logic [31:0] wrng,rrng,serial=0;
  bit write_taken=0,w_stalled=0,r_stalled=0;
  logic [DATA_W-1:0] prev_wdata,prev_rdata;
  logic [PTR_W-1:0] previous_wsync=0,previous_rsync=0;
  async_fifo #(.DATA_W(DATA_W),.ADDR_BITS(ADDR_BITS)) dut(.*);

  function automatic [31:0] next_rng(input [31:0] s);
    logic [31:0] x;
    begin x=s^(s<<13); x=x^(x>>17); next_rng=x^(x<<5); end
  endfunction
  function automatic bit onehot0(input [PTR_W-1:0] x);
    onehot0 = (x & (x-1'b1)) == 0;
  endfunction
  initial begin
    if($value$plusargs("WH=%d",wh)) begin end
    if($value$plusargs("RH=%d",rh)) begin end
    if($value$plusargs("PHASE=%d",rphase)) begin end
    if($value$plusargs("SEED=%d",seed)) begin end
    wrng=seed|1;rrng=(seed^32'hb5297a4d)|1;
    forever begin #(wh); if(w_run) wclk=~wclk; else wclk=0; end
  end
  initial begin
    #0; // plusargs are read before the phase delay.
    #(rphase);
    forever begin #(rh); if(r_run) rclk=~rclk; else rclk=0; end
  end
  initial begin #500000; $fatal(1,"TIMEOUT"); end

  always @(negedge arst_n) begin
    dropped=dropped+(tail-head);head=tail;epochs=epochs+1;
  end
  always @(negedge wclk or negedge arst_n) begin
    if(!arst_n) begin w_valid=0;w_data=0; end
    else if(!w_valid || write_taken) begin
      wrng=next_rng(wrng);
      w_valid=produce && (!random_mode || wrng[1:0]!=0);
      if(w_valid) begin w_data=serial^(serial<<5)^wrng;serial=serial+1;end
    end
  end
  always @(negedge rclk or negedge arst_n) begin
    if(!arst_n) r_ready=0;
    else begin rrng=next_rng(rrng);r_ready=consume && (!random_mode || rrng[2:0]<5); end
  end

  // Both monitors sample before the DUT's NBA updates. The independent queue
  // stores accepted input payloads, never the DUT's internal memory or pointers.
  always @(posedge wclk or negedge arst_n) begin : write_monitor
    logic [PTR_W-1:0] old_bin,old_gray;
    bit take;
    if(!arst_n) begin write_taken=0;w_stalled=0;previous_wsync=0;end
    else begin
      if(w_stalled && (!w_valid || w_data!==prev_wdata)) $fatal(1,"SOURCE_STABILITY");
      write_taken=w_valid && w_ready;
      if(write_taken) begin
        if(tail-head>=DEPTH) $fatal(1,"OVERFLOW");
        if(tail>=65536) $fatal(1,"SCOREBOARD_LIMIT");
        expected[tail]=w_data;tail=tail+1;last_write=$time;
        if(last_read==$time) simultaneous=simultaneous+1;
        if(dut.w_bin[ADDR_BITS-1:0]==DEPTH-1) write_wraps=write_wraps+1;
      end
      w_stalled=w_valid && !w_ready;prev_wdata=w_data;
      if(w_stalled) write_stalls=write_stalls+1;
      // A destination may skip source states: multi-bit Gray differences here
      // are COVERAGE, never a one-bit assertion on the synchronized bus.
      if(!onehot0(dut.wq2_rgray^previous_wsync)) write_jumps=write_jumps+1;
      previous_wsync=dut.wq2_rgray;
      old_bin=dut.w_bin;old_gray=dut.w_gray;take=write_taken;
      #0.001;
      if(dut.wrst_n && arst_n) begin
        if(dut.w_bin!==(old_bin+take)) $fatal(1,"WRITE_ADVANCE");
        if(!onehot0(dut.w_gray^old_gray)) $fatal(1,"GRAY_SOURCE");
        if(dut.w_gray!==((dut.w_bin>>1)^dut.w_bin)) $fatal(1,"GRAY_ENCODING");
      end
    end
  end
  always @(posedge rclk or negedge arst_n) begin : read_monitor
    logic [PTR_W-1:0] old_bin,old_gray;
    bit take;
    if(!arst_n) begin r_stalled=0;previous_rsync=0;end
    else begin
      if(r_stalled && (!r_valid || r_data!==prev_rdata)) $fatal(1,"OUTPUT_STABILITY");
      take=r_valid && r_ready;
      if(take) begin
        if(head>=tail) $fatal(1,"UNDERFLOW");
        if(r_data!==expected[head]) $fatal(1,"ORDER_OR_DATA");
        head=head+1;last_read=$time;
        if(last_write==$time) simultaneous=simultaneous+1;
        if(dut.r_bin[ADDR_BITS-1:0]==DEPTH-1) read_wraps=read_wraps+1;
      end
      r_stalled=r_valid && !r_ready;prev_rdata=r_data;
      if(r_stalled) read_stalls=read_stalls+1;
      if(!onehot0(dut.rq2_wgray^previous_rsync)) read_jumps=read_jumps+1;
      previous_rsync=dut.rq2_wgray;
      old_bin=dut.r_bin;old_gray=dut.r_gray;
      #0.001;
      if(dut.rrst_n && arst_n) begin
        if(dut.r_bin!==(old_bin+take)) $fatal(1,"READ_ADVANCE");
        if(!onehot0(dut.r_gray^old_gray)) $fatal(1,"GRAY_SOURCE");
        if(dut.r_gray!==((dut.r_bin>>1)^dut.r_bin)) $fatal(1,"GRAY_ENCODING");
      end
    end
  end

  task automatic drain;
    begin
      produce=0;consume=1;random_mode=0;
      wait(!w_valid);wait(head==tail);repeat(8)@(negedge rclk);
      if(r_valid) $fatal(1,"NOT_EMPTY_AFTER_DRAIN");
    end
  endtask
  task automatic stopped_reset;
    begin
      #0.137;arst_n=0;
      #0.137;w_run=0;r_run=0;
      #30;
      if(w_ready!==0 || r_valid!==0 || dut.wrst_n!==0 || dut.rrst_n!==0)
        $fatal(1,"ASYNC_ASSERT");
      arst_n=1;
      #30;
      if(w_ready!==0 || r_valid!==0 || dut.wrst_n!==0 || dut.rrst_n!==0)
        $fatal(1,"RELEASE_WITH_STOPPED_CLOCK");
    end
  endtask
  initial begin
    stopped_reset();
    w_run=1;wait(dut.wrst_n);produce=1;
    // Writer may fill storage while the reader's clock is still stopped.
    wait(dut.w_full);#0.001;
    if(tail-head!=DEPTH || dut.rrst_n!==0) $fatal(1,"CAPACITY");
    repeat(6)@(negedge wclk);
    r_run=1;drain();
    random_mode=1;produce=1;consume=1;
    repeat(1200)@(negedge wclk);
    drain();

    consume=0;produce=1;
    wait(dut.w_full);repeat(3)@(negedge wclk);
    produce=0;consume=0;stopped_reset();
    // Reader releases first in the new epoch: stale array words stay invalid.
    r_run=1;consume=1;
    repeat(12)@(negedge rclk);
    if(r_valid || head!=tail || dut.wrst_n!==0) $fatal(1,"STALE_AFTER_RESET");
    w_run=1;random_mode=1;produce=1;
    repeat(1200)@(negedge wclk);
    // A further common flush while both clocks are running.
    #0.137;arst_n=0;#1.337;arst_n=1;
    repeat(600)@(negedge wclk);
    drain();
    if(tail!=head || dropped<DEPTH || epochs!=3 || write_wraps<4 || read_wraps<4)
      $fatal(1,"MISSING_COVERAGE");
    $display("METRIC writes=%0d reads=%0d dropped=%0d epochs=%0d wwrap=%0d rwrap=%0d wstall=%0d rstall=%0d wjump=%0d rjump=%0d simultaneous=%0d",
      tail,head-dropped,dropped,epochs,write_wraps,read_wraps,write_stalls,read_stalls,write_jumps,read_jumps,simultaneous);
    $display("PASS asynchronous FIFO width=%0d depth=%0d WH=%0d RH=%0d phase=%0d seed=%0d",DATA_W,DEPTH,wh,rh,rphase,seed);
    $finish;
  end
endmodule
