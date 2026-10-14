`timescale 1ns/1ps
module tb_foundations;
  logic clk=0;
  always #5 clk=~clk;
  logic [31:0] instruction=0, immediate;
  logic [2:0] kind=0;
  logic format_valid;
  rv32_immediate imm(.*);
  logic [31:0] a=0,b=0,result;
  logic [3:0] operation=0;
  logic operation_valid;
  foundation_alu alu(.*);
  logic legal,uses_rs1,uses_rs2,writes_rd,load_word,store_word,branch_equal;
  logic [2:0] immediate_kind;
  foundation_decode decoder(.*);
  logic reset=1,write_enable=0;
  logic [4:0] write_address=0,read_address_a=0,read_address_b=0;
  logic [31:0] write_data=0,read_data_a,read_data_b;
  foundation_regfile registers(.*);
  logic [31:0] reference[0:31], expected;
  logic [100:0] alu_row;
  logic [67:0] imm_row;
  logic expected_valid;
  integer file_id,rows,rc,seed;
  task automatic decode_case(input logic[31:0] ins,input logic[9:0] exp);
    instruction=ins;#1;
    if({legal,uses_rs1,uses_rs2,writes_rd,load_word,store_word,branch_equal,immediate_kind}!==exp)
      $fatal(1,"decoder mismatch %h",ins);
  endtask
  initial begin
    seed=2026;rc=$value$plusargs("SEED=%d",seed);rc=$urandom(seed);
    file_id=$fopen("alu-vectors.hex","r");if(!file_id)$fatal(1,"missing ALU vectors");
    rc=$fscanf(file_id,"%d\n",rows);
    for(int n=0;n<rows;n++)begin
      if($fscanf(file_id,"%h\n",alu_row)!=1)$fatal(1,"short ALU vectors");
      {operation,a,b,expected,expected_valid}=alu_row;#1;
      if(result!==expected||operation_valid!==expected_valid)$fatal(1,"ALU vector %0d",n);
    end
    $fclose(file_id);
    file_id=$fopen("immediate-vectors.hex","r");if(!file_id)$fatal(1,"missing immediate vectors");
    rc=$fscanf(file_id,"%d\n",rows);
    for(int n=0;n<rows;n++)begin
      if($fscanf(file_id,"%h\n",imm_row)!=1)$fatal(1,"short immediate vectors");
      {kind,instruction,expected,expected_valid}=imm_row;#1;
      if(immediate!==expected||format_valid!==expected_valid)$fatal(1,"immediate vector %0d",n);
    end
    $fclose(file_id);
    decode_case(32'h002081b3,10'b1111000000);
    decode_case(32'hfff08193,10'b1101000000);
    decode_case(32'h0040a183,10'b1101100000);
    decode_case(32'h0030a223,10'b1110010001);
    decode_case(32'h00208263,10'b1110001010);
    decode_case(32'h123451b7,10'b1001000011);
    decode_case(32'h0000a003,10'b1101100000);
    decode_case(32'h402081b3,0);decode_case(32'h00408183,0);
    decode_case(32'h00209263,0);decode_case(32'h00109193,0);decode_case(32'h0000006f,0);
    @(negedge clk);reset=0;reference[0]=0;
    for(int r=1;r<32;r++)begin
      write_enable=1;write_address=5'(r);write_data=32'(r);
      @(negedge clk);reference[r]=32'(r);
    end
    for(int n=0;n<3000;n++)begin
      write_enable=1'($urandom);write_address=5'($urandom);write_data=$urandom;
      read_address_a=5'($urandom);read_address_b=5'($urandom);reset=(n%113==0);#1;
      expected=read_address_a==0?0:((!reset&&write_enable&&write_address==read_address_a)?write_data:reference[read_address_a]);
      if(read_data_a!==expected)$fatal(1,"register A/bypass");
      expected=read_address_b==0?0:((!reset&&write_enable&&write_address==read_address_b)?write_data:reference[read_address_b]);
      if(read_data_b!==expected)$fatal(1,"register B/bypass");
      @(posedge clk);
      if(!reset&&write_enable&&write_address!=0)reference[write_address]=write_data;
      @(negedge clk);
    end
    $display("PASS foundations: vectors, decoder, 3000 register cycles");$finish;
  end
  initial begin #1000000;$fatal(1,"timeout");end
endmodule
