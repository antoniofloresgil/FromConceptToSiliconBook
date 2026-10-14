module event_axil (
  input  logic        ACLK, ARESETn,
  input  logic [5:0]  AWADDR, ARADDR,
  input  logic [2:0]  AWPROT, ARPROT,
  input  logic        AWVALID, WVALID, BREADY,
  input  logic        ARVALID, RREADY,
  input  logic [31:0] WDATA,
  input  logic [3:0]  WSTRB,
  output logic       AWREADY, WREADY, BVALID,
  output logic       ARREADY, RVALID,
  output logic [1:0] BRESP, RRESP,
  output logic [31:0] RDATA, OutputValue,
  input  logic       EventPulse,
  output logic       Irq
);
  logic AddressFull, DataFull;
  logic [5:0] SavedAddress;
  logic [31:0] SavedData, EventCount;
  logic [3:0] SavedStrobe;
  logic Enable, Pending, WriteCommit, ClearPending;

  assign AWREADY = ARESETn && !AddressFull && !BVALID;
  assign WREADY  = ARESETn && !DataFull && !BVALID;
  assign ARREADY = ARESETn && !RVALID;
  assign WriteCommit = AddressFull && DataFull && !BVALID;
  assign ClearPending = WriteCommit && SavedAddress == 6'h08
                        && SavedStrobe[0] && SavedData[0];
  assign Irq = Enable && Pending;

  always_ff @(posedge ACLK or negedge ARESETn) begin
    if (!ARESETn) begin
      AddressFull <= 1'b0;
      DataFull <= 1'b0;
      SavedAddress <= '0;
      SavedData <= '0;
      SavedStrobe <= '0;
      BVALID <= 1'b0;
      BRESP <= 2'b00;
      RVALID <= 1'b0;
      RDATA <= '0;
      RRESP <= 2'b00;
      OutputValue <= '0;
      Enable <= 1'b0;
      Pending <= 1'b0;
      EventCount <= '0;
    end else begin
      if (AWVALID && AWREADY) begin
        SavedAddress <= AWADDR;
        AddressFull <= 1'b1;
      end
      if (WVALID && WREADY) begin
        SavedData <= WDATA;
        SavedStrobe <= WSTRB;
        DataFull <= 1'b1;
      end
      if (BVALID && BREADY) BVALID <= 1'b0;

      if (WriteCommit) begin
        AddressFull <= 1'b0;
        DataFull <= 1'b0;
        BVALID <= 1'b1;
        BRESP <= 2'b00;
        case (SavedAddress)
          6'h00: for (int i = 0; i < 4; i++)
            if (SavedStrobe[i])
              OutputValue[8*i +: 8] <= SavedData[8*i +: 8];
          6'h04: if (SavedStrobe[0]) Enable <= SavedData[0];
          6'h08: begin end // pending update below
          default: BRESP <= 2'b10;
        endcase
      end

      if (EventPulse) begin
        Pending <= 1'b1; // event wins over simultaneous clear
        EventCount <= EventCount + 32'd1;
      end else if (ClearPending) Pending <= 1'b0;

      if (RVALID && RREADY) RVALID <= 1'b0;
      if (ARVALID && ARREADY) begin
        RVALID <= 1'b1;
        RRESP <= 2'b00;
        case (ARADDR)
          6'h00: RDATA <= OutputValue;
          6'h04: RDATA <= {31'b0, Enable};
          6'h08: RDATA <= {31'b0, Pending};
          6'h0C: RDATA <= EventCount;
          default: begin
            RDATA <= '0;
            RRESP <= 2'b10;
          end
        endcase
      end
    end
  end
endmodule
