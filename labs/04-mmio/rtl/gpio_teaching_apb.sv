module gpio_teaching_apb (
  input  logic        PCLK, PRESETn, PSEL, PENABLE, PWRITE,
  input  logic [7:0]  PADDR,
  input  logic [31:0] PWDATA,
  input  logic [3:0]  PSTRB,
  output logic [31:0] PRDATA,
  output logic       PREADY, PSLVERR,
  input  logic [7:0]  PinIn,
  output logic [7:0]  PinOut, PinEnable,
  output logic       Irq
);
  (* ASYNC_REG = "TRUE" *) logic [7:0] Meta, Sample;
  logic [7:0] Previous, InputEnable, OutputEnable, OutputValue;
  logic [7:0] RiseEnable, Pending, Rise, ClearMask;
  logic BadRead, BadWrite, WriteDone;
  assign PREADY = 1'b1;
  assign PSLVERR = PSEL && PENABLE &&
                  (PWRITE ? BadWrite : BadRead);
  assign WriteDone = PSEL && PENABLE && PWRITE && !PSLVERR;
  assign Rise = Sample & ~Previous & InputEnable;
  assign ClearMask = WriteDone && PADDR == 8'h1C && PSTRB[0]
                     ? PWDATA[7:0] : 8'b0;
  assign PinOut = OutputValue;
  assign PinEnable = OutputEnable;
  assign Irq = |(Pending & RiseEnable);

  always_comb begin
    PRDATA = '0;
    BadRead = 1'b0;
    BadWrite = 1'b0;
    case (PADDR)
      8'h00: begin
        PRDATA = {24'b0, Sample & InputEnable};
        BadWrite = 1'b1;
      end
      8'h04: PRDATA = {24'b0, InputEnable};
      8'h08: PRDATA = {24'b0, OutputEnable};
      8'h0C: PRDATA = {24'b0, OutputValue};
      8'h18: PRDATA = {24'b0, RiseEnable};
      8'h1C: PRDATA = {24'b0, Pending};
      8'h44, 8'h48: BadRead = 1'b1;
      default: begin BadRead = 1'b1; BadWrite = 1'b1; end
    endcase
  end

  always_ff @(posedge PCLK) begin
    if (!PRESETn) begin
      Meta <= '0;
      Sample <= '0;
      Previous <= '0;
      InputEnable <= '0;
      OutputEnable <= '0;
      OutputValue <= '0;
      RiseEnable <= '0;
      Pending <= '0;
    end else begin
      Meta <= PinIn;
      Sample <= Meta;
      Previous <= Sample;
      Pending <= (Pending & ~ClearMask) | Rise;
      if (WriteDone && PSTRB[0])
        case (PADDR)
          8'h04: InputEnable <= PWDATA[7:0];
          8'h08: OutputEnable <= PWDATA[7:0];
          8'h0C: OutputValue <= PWDATA[7:0];
          8'h18: RiseEnable <= PWDATA[7:0];
          8'h44: OutputValue <= OutputValue | PWDATA[7:0];
          8'h48: OutputValue <= OutputValue & ~PWDATA[7:0];
          default: begin end
        endcase
    end
  end
endmodule
