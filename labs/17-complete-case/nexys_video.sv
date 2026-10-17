// Serial boundary fixture; the accelerator RTL remains unchanged.
module nexys_video_case (input wire clk100, resetn, scan_data, scan_tick, apply, capture, output wire scan_out);
  wire clk; BUFG clock_buffer (.I(clk100), .O(clk));
  (* ASYNC_REG="TRUE" *) reg [1:0] rst_pipe = 0;
  (* ASYNC_REG="TRUE" *) reg [1:0] data_sync=0, tick_sync=0, apply_sync=0, capture_sync=0;
  reg tick_old=0, apply_old=0, capture_old=0;
  wire reset = !rst_pipe[1];
  reg [100:0] scan_inputs=0, active_inputs=0;
  reg [205:0] scan_outputs=0;
  wire [205:0] outputs;
  always @(posedge clk) begin
    rst_pipe <= {rst_pipe[0], resetn};
    data_sync <= {data_sync[0], scan_data}; tick_sync <= {tick_sync[0], scan_tick};
    apply_sync <= {apply_sync[0], apply}; capture_sync <= {capture_sync[0], capture};
    tick_old<=tick_sync[1]; apply_old<=apply_sync[1]; capture_old<=capture_sync[1];
    if (reset) begin scan_inputs<=0; active_inputs<=0; scan_outputs<=0; end
    else begin
      if (tick_sync[1] && !tick_old) begin scan_inputs<={scan_inputs[99:0],data_sync[1]}; scan_outputs<={1'b0,scan_outputs[205:1]}; end
      if (apply_sync[1] && !apply_old) active_inputs<=scan_inputs;
      if (capture_sync[1] && !capture_old) scan_outputs<=outputs;
    end
  end
  assign scan_out=scan_outputs[0];
  dotproduct_axi #(.MAX_LENGTH(256), .DMA_BASE(32'h80008000), .DMA_LIMIT(33'h08000c000)) dut (
    .clk(clk), .reset(reset),
    .s_awaddr(active_inputs[4:0]),
    .s_awvalid(active_inputs[5]),
    .s_wdata(active_inputs[37:6]),
    .s_wstrb(active_inputs[41:38]),
    .s_wvalid(active_inputs[42]),
    .s_bready(active_inputs[43]),
    .s_araddr(active_inputs[48:44]),
    .s_arvalid(active_inputs[49]),
    .s_rready(active_inputs[50]),
    .m_arready(active_inputs[51]),
    .m_rdata(active_inputs[83:52]),
    .m_rresp(active_inputs[85:84]),
    .m_rid(active_inputs[89:86]),
    .m_rvalid(active_inputs[90]),
    .m_rlast(active_inputs[91]),
    .m_awready(active_inputs[92]),
    .m_wready(active_inputs[93]),
    .m_bresp(active_inputs[95:94]),
    .m_bid(active_inputs[99:96]),
    .m_bvalid(active_inputs[100]),
    .s_awready(outputs[0]),
    .s_wready(outputs[1]),
    .s_bresp(outputs[3:2]),
    .s_bvalid(outputs[4]),
    .s_arready(outputs[5]),
    .s_rdata(outputs[37:6]),
    .s_rresp(outputs[39:38]),
    .s_rvalid(outputs[40]),
    .irq(outputs[41]),
    .m_araddr(outputs[73:42]),
    .m_arvalid(outputs[74]),
    .m_arid(outputs[78:75]),
    .m_arlen(outputs[86:79]),
    .m_arsize(outputs[89:87]),
    .m_arburst(outputs[91:90]),
    .m_arlock(outputs[92]),
    .m_arcache(outputs[96:93]),
    .m_arqos(outputs[100:97]),
    .m_arprot(outputs[103:101]),
    .m_rready(outputs[104]),
    .m_awaddr(outputs[136:105]),
    .m_awvalid(outputs[137]),
    .m_awid(outputs[141:138]),
    .m_awlen(outputs[149:142]),
    .m_awsize(outputs[152:150]),
    .m_awburst(outputs[154:153]),
    .m_awlock(outputs[155]),
    .m_awcache(outputs[159:156]),
    .m_awqos(outputs[163:160]),
    .m_awprot(outputs[166:164]),
    .m_wdata(outputs[198:167]),
    .m_wstrb(outputs[202:199]),
    .m_wvalid(outputs[203]),
    .m_wlast(outputs[204]),
    .m_bready(outputs[205])
  );
endmodule
