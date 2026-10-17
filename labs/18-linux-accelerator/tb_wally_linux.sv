// SPDX-License-Identifier: MIT
// Advanced RTL system fixture: real Wally SoC + accelerator, shared behavioral RAM.
`include "config.vh"
`include "BranchPredictorType.vh"
import cvw::*;
module tb_wally_linux;
  `include "parameter-defs.vh"
  function automatic cvw_t linux_config();
    cvw_t c;
    c=P;c.RESET_VECTOR=64'h1000;
    c.DCACHE_SUPPORTED=1;c.DTIM_SUPPORTED=0;c.IROM_SUPPORTED=0;
    c.UNCORE_RAM_SUPPORTED=1;c.UNCORE_RAM_RANGE=64'h0fffffff;c.UNCORE_RAM_PRELOAD=0;
    c.BOOTROM_SUPPORTED=1;c.BOOTROM_PRELOAD=0;
    c.EXT_MEM_SUPPORTED=1;c.EXT_MEM_BASE=64'h10080000;c.EXT_MEM_RANGE=64'h1f;
    c.GPIO_SUPPORTED=1; // Preserve the upstream GPIO at 0x10060000.
    c.PLIC_NUM_SRC=32;
    c.SV48_SUPPORTED=0;c.SV57_SUPPORTED=0; // Match the DT's Sv39 Linux profile.
    c.VPN_BITS=3*c.VPN_SEGMENT_BITS; // Recompute the derived width after changing modes.
    c.UART_PRESCALE=0; // 100 MHz / (16 * divisor 1) = 6,250,000 baud.
    return c;
  endfunction
  localparam cvw_t L=linux_config();
  logic clk=0,reset_ext=1,reset;
  always #5 clk=~clk;
  logic [63:0] hwdata,hrdata;
  logic [L.PA_BITS-1:0] haddr;
  logic [7:0] hwstrb;
  logic hready,hresp,hsel,hwrite,hclk,hresetn,hlock;
  logic [2:0] hsize,hburst;logic [3:0] hprot;logic [1:0] htrans;
  logic bridge_ready,bridge_error;logic [31:0] bridge_data;
  logic lane=0;
  logic [4:0] s_awaddr,s_araddr;
  logic s_awvalid,s_awready,s_wvalid,s_wready,s_bvalid,s_bready;
  logic [31:0] s_wdata,s_rdata;logic [3:0] s_wstrb;logic [1:0] s_bresp,s_rresp;
  logic s_arvalid,s_arready,s_rvalid,s_rready,irq;
  logic [31:0] m_araddr,m_rdata,m_awaddr,m_wdata;
  logic m_arvalid,m_arready,m_rvalid,m_rlast,m_rready;
  logic m_awvalid,m_awready,m_wvalid,m_wlast,m_wready,m_bvalid,m_bready;
  logic [3:0] m_arid,m_rid,m_awid,m_bid,m_wstrb;
  logic [7:0] m_arlen,m_awlen;logic [2:0] m_arsize,m_awsize;
  logic [1:0] m_arburst,m_awburst,m_rresp,m_bresp;
  logic m_arlock,m_awlock;logic [3:0] m_arcache,m_awcache,m_arqos,m_awqos;logic [2:0] m_arprot,m_awprot;
  dotproduct_axi #(.MAX_LENGTH(256),.DMA_BASE(32'h88000000),.DMA_LIMIT(33'h088004000)) dut(.*);
  assign hrdata={bridge_data,bridge_data};
  wallypipelinedsoc #(.P(L)) soc(
    .clk,.reset_ext,.reset,.HRDATAEXT(hrdata),.HREADYEXT(bridge_ready),.HRESPEXT(bridge_error),.HSELEXT(hsel),
    .ExternalStall(1'b0),.AcceleratorIRQ(irq),.HCLK(hclk),.HRESETn(hresetn),.HADDR(haddr),.HWDATA(hwdata),
    .HWSTRB(hwstrb),.HWRITE(hwrite),.HSIZE(hsize),.HBURST(hburst),.HPROT(hprot),.HTRANS(htrans),
    .HMASTLOCK(hlock),.HREADY(hready),.TIMECLK(clk),.GPIOIN(32'b0),.GPIOOUT(),.GPIOEN(),
    .UARTSin(1'b1),.UARTSout(),.SPIIn(1'b1),.SPIOut(),.SPICS(),.SPICLK(),
    .SDCIn(1'b1),.SDCCmd(),.SDCCS(),.SDCCLK(),.PWMGPIO());
  always @(posedge clk) if(hready && hsel && htrans[1])lane<=haddr[2];
  always @(posedge clk)
    if(!reset && htrans[1] && !$onehot(soc.uncoregen.uncore.HSELRegions))
      $fatal(1,"Overlapping Wally peripheral address decodes");
  ahb_to_axil bridge(.clk,.reset,.hsel,.hready,.haddr(haddr[31:0]),
    .hwdata(lane?hwdata[63:32]:hwdata[31:0]),.hwstrb(lane?hwstrb[7:4]:hwstrb[3:0]),
    .hwrite,.hsize,.htrans,.hrdata(bridge_data),.hreadyout(bridge_ready),.hresp(bridge_error),
    .s_awaddr,.s_awvalid,.s_awready,.s_wdata,.s_wstrb,.s_wvalid,.s_wready,.s_bresp,.s_bvalid,.s_bready,
    .s_araddr,.s_arvalid,.s_arready,.s_rdata,.s_rresp,.s_rvalid,.s_rready);
  `define RAM soc.uncoregen.uncore.ram.ram.memory.ram.RAM
  initial begin
    #1;$readmemh("bootrom.hex",soc.uncoregen.uncore.bootrom.bootrom.memory.ROM);
    $readmemh("ram.hex",`RAM);
    repeat(12) @(negedge clk);reset_ext=0;
  end
  logic aw_held=0,w_held=0;logic [31:0] address,data;logic [3:0] strobe;
  assign m_arready=!m_rvalid;
  assign m_awready=!aw_held && !m_bvalid;
  assign m_wready=!w_held && !m_bvalid;
  assign m_rresp=0,m_bresp=0,m_rid=0,m_bid=0,m_rlast=1;
  integer k;
  integer dma_reads=0;
  always @(posedge clk) begin
    if(reset)begin m_rvalid<=0;m_bvalid<=0;aw_held<=0;w_held<=0;end
    else begin
      if(m_rvalid&&m_rready)m_rvalid<=0;
      if(m_bvalid&&m_bready)m_bvalid<=0;
      if(m_arvalid&&m_arready)begin
        if(m_araddr<32'h88000000 || m_araddr>=32'h88004000 || m_araddr[1:0]!=0)$fatal(1,"DMA read range");
        m_rdata<=m_araddr[2]?`RAM[(m_araddr-32'h80000000)>>3][63:32]:`RAM[(m_araddr-32'h80000000)>>3][31:0];
        if(dma_reads<16)$display("WALLY_DMA_READ address=%h word=%h",m_araddr,`RAM[(m_araddr-32'h80000000)>>3]);
        dma_reads<=dma_reads+1;
        m_rvalid<=1;
      end
      if(m_awvalid&&m_awready)begin address<=m_awaddr;aw_held<=1;end
      if(m_wvalid&&m_wready)begin data<=m_wdata;strobe<=m_wstrb;w_held<=1;end
      if(aw_held&&w_held&&!m_bvalid)begin
        if(address<32'h88000000 || address>=32'h88004000 || address[1:0]!=0)$fatal(1,"DMA write range");
        for(k=0;k<4;k=k+1)if(strobe[k])`RAM[(address-32'h80000000)>>3][address[2]*32+k*8+:8]<=data[k*8+:8];
        $display("WALLY_DMA_WRITE address=%h data=%h strobe=%h",address,data,strobe);
        aw_held<=0;w_held<=0;m_bvalid<=1;
      end
    end
  end
  // Observe the UART's actual APB access phase, excluding DLAB divisor writes.
  logic dlab=0,previous_uart_commit=0;logic [7:0] character;string line="";
  wire uart_commit=soc.uncoregen.uncore.PSEL[3] && soc.uncoregen.uncore.PENABLE && soc.uncoregen.uncore.PWRITE && hready;
  integer progress;
  integer uart_writes=0;
  longint unsigned cycles=0,max_cycles=500000000;
  initial begin
    void'($value$plusargs("MAX_CYCLES=%d",max_cycles));
    progress=$fopen("progress.txt","w");
  end
  always @(posedge clk)begin
    cycles<=cycles+1;
    previous_uart_commit<=uart_commit;
    if(cycles%100000==0)begin
      $fdisplay(progress,"cycles=%0d pc=%h haddr=%h ready=%b",cycles,soc.core.ifu.PCF,haddr,hready);
      $fflush(progress);
    end
    if(cycles>=max_cycles)$fatal(1,"Wally Linux cycle limit PC=%h",soc.core.ifu.PCF);
    if(!reset && uart_commit && !previous_uart_commit)begin
      character=soc.uncoregen.uncore.PWDATA[7:0];
      if(uart_writes<40)begin
        $fdisplay(progress,"UART cycle=%0d pc=%h addr=%h data=%h",cycles,soc.core.ifu.PCF,soc.uncoregen.uncore.PADDR,character);
        $fflush(progress);uart_writes<=uart_writes+1;
      end
      if(soc.uncoregen.uncore.PADDR[2:0]==3)dlab=character[7];
      if(soc.uncoregen.uncore.PADDR[2:0]==0&&!dlab)begin
        // The pinned UART already echoes accepted THR writes to stdout.
        // Observe for checkpoints without printing each character a second time.
        if(character==10)begin
          $fflush();
          if(line=="WALLY_MMIO_SMOKE_PASS")begin
            if(!$test$plusargs("MMIO_SMOKE"))$fatal(1,"Unexpected preflight ROM in Linux run");
            $finish;
          end
          if(line=="WALLY_MMIO_SMOKE_FAIL")$fatal(1,"CPU/MMIO/DMA preflight failed");
          if(line=="HSD_LINUX_ACCEL_PASS")begin $display("WALLY_LINUX_ACCEL_PASS cycles=%0d",cycles);$finish;end
          if(line.substr(0,19)=="HSD_LINUX_ACCEL_FAIL")begin
            $display("WALLY_DMA_POOL a=%h b=%h result=%h",`RAM['h1000000],`RAM['h1000080],`RAM['h1000100]);
            $fatal(1,"Userspace regression failed");
          end
          line="";
        end else if(character!=13)line={line,string'(character)};
      end
    end
  end
endmodule
