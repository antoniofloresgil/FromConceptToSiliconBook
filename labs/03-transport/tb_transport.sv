`timescale 1ns/1ps
module tb_transport;
  localparam int D=`TEST_DEPTH;
  logic clk=0;always #5 clk=~clk;
  logic reset=1,req_valid=0,req_ready,req_write=0;
  logic[3:0]req_addr=0,req_strb=0;
  logic[15:0]req_id=0,rsp_id;
  logic[31:0]req_data=0,rsp_data;
  logic rsp_valid,rsp_ready=0,rsp_write;
  queued_memory #(.AW(4),.IW(16),.QDEPTH(D)) dut(.*);
  logic frst=1,fv=0,fi_ready,fo_valid,fo_ready=0;
  logic[31:0]fi_data=0,fo_data;
  transport_fifo #(.DEPTH(D)) fifo(.clk,.reset(frst),.in_valid(fv),.in_ready(fi_ready),
    .in_data(fi_data),.out_valid(fo_valid),.out_ready(fo_ready),.out_data(fo_data));
  logic[31:0]reference_mem[0:15],fifo_expected[0:8191];
  logic[48:0]expected[0:2047],previous_response;
  logic[31:0]previous_head;
  int accepted=0,consumed=0,fh=0,ft=0,max_out=0,cycles=0,seed,rc;
  bit fifo_accepted=0,mem_done=0,fifo_done=0,prev_rsp_stall=0,prev_fifo_stall=0,pause_sink=0;
  always @(posedge clk)begin
    cycles++;
    if(reset)begin accepted=0;consumed=0;prev_rsp_stall=0;end
    else begin
      if(prev_rsp_stall&&(!rsp_valid||{rsp_write,rsp_id,rsp_data}!==previous_response))$fatal(1,"response changed under stall");
      if(req_valid&&req_ready)begin
        if(req_write)begin
          for(int b=0;b<4;b++)if(req_strb[b])reference_mem[req_addr][8*b+:8]=req_data[8*b+:8];
          expected[accepted]={1'b1,req_id,32'b0};
        end else expected[accepted]={1'b0,req_id,reference_mem[req_addr]};
        accepted++;
      end
      if(rsp_valid&&rsp_ready)begin
        if(consumed>=accepted||{rsp_write,rsp_id,rsp_data}!==expected[consumed])$fatal(1,"memory correspondence");
        consumed++;
      end
      if(accepted-consumed>2*D+1)$fatal(1,"outstanding overflow");
      if(accepted-consumed>max_out)max_out=accepted-consumed;
      prev_rsp_stall=rsp_valid&&!rsp_ready;previous_response={rsp_write,rsp_id,rsp_data};
    end
    fifo_accepted=0;
    if(frst)begin fh=0;ft=0;prev_fifo_stall=0;end
    else begin
      if(prev_fifo_stall&&(!fo_valid||fo_data!==previous_head))$fatal(1,"FIFO unstable head");
      if(fv&&fi_ready)begin fifo_expected[ft]=fi_data;ft++;fifo_accepted=1;end
      if(fo_valid&&fo_ready)begin
        if(fh>=ft||fo_data!==fifo_expected[fh])$fatal(1,"FIFO order");fh++;
      end
      if(ft-fh>D||ft<fh)$fatal(1,"FIFO occupancy");
      prev_fifo_stall=fo_valid&&!fo_ready;previous_head=fo_data;
    end
    if(cycles>60000)$fatal(1,"timeout");
  end
  always @(negedge clk)rsp_ready=!pause_sink&&($urandom_range(0,3)!=0);
  task automatic request(input bit wr,input logic[3:0]addr,input logic[15:0]tag,input logic[31:0]data,input logic[3:0]mask);
    @(negedge clk);req_valid=1;req_write=wr;req_addr=addr;req_id=tag;req_data=data;req_strb=mask;
    do @(posedge clk);while(!req_ready);
    @(negedge clk);req_valid=0;
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    repeat(3)@(negedge clk);reset=0;
    for(int a=0;a<16;a++)request(1,4'(a),16'(a),32'(a*17),15);
    wait(accepted==consumed);pause_sink=1;
    fork
      begin for(int n=0;n<20;n++)request(0,4'(n),16'(100+n),0,0);end
      begin repeat(300)@(negedge clk);if(max_out!=2*D+1)$fatal(1,"capacity not exercised");pause_sink=0;end
    join
    for(int n=0;n<500;n++)request(1'($urandom),4'($urandom),16'(200+n),$urandom,4'($urandom));
    wait(accepted==consumed);
    pause_sink=1;request(1,3,2000,32'h1234abcd,15);wait(dut.service.busy);
    @(negedge clk);reset=1;repeat(2)@(negedge clk);reset=0;pause_sink=0;
    request(0,3,2001,0,0);wait(accepted==consumed);mem_done=1;
  end
  initial begin
    repeat(3)@(negedge clk);frst=0;
    for(int n=0;n<5000;n++)begin
      @(negedge clk);
      if(!fv||fifo_accepted)begin fv=($urandom_range(0,3)!=0);fi_data=$urandom;end
      fo_ready=(n%73<15)?0:($urandom_range(0,2)!=0);
    end
    @(negedge clk);while(fv&&!fifo_accepted)@(negedge clk);
    fv=0;fo_ready=1;wait(fh==ft);
    @(negedge clk);fo_ready=0;fv=1;fi_data=32'hdeadbeef;
    @(negedge clk);fv=0;@(negedge clk);frst=1;
    repeat(2)@(negedge clk);frst=0;fo_ready=1;
    repeat(3)@(negedge clk);if(fo_valid)$fatal(1,"reset did not discard");fifo_done=1;
  end
  initial begin
    wait(mem_done&&fifo_done);
    $display("PASS transport depth=%0d: 500 memory operations, 5000 FIFO cycles, capacity=%0d",D,max_out);$finish;
  end
endmodule
