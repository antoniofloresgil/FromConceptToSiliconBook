// Closure candidate: register the product, then accumulate in a separate cycle.
// Same AXI interface and arithmetic; one extra cycle per element, no overlap.
module dotproduct_engine (
  input logic clk, reset, start,
  input logic [31:0] src_a, src_b, dst, length,
  output logic busy, done, failed,
  output logic [31:0] error_code,
  output logic [31:0] araddr,
  output logic arvalid, input logic arready,
  input logic [31:0] rdata, input logic [1:0] rresp,
  input logic rvalid, rlast, output logic rready,
  output logic [31:0] awaddr, wdata,
  output logic awvalid, input logic awready,
  output logic wvalid, input logic wready,
  input logic bvalid, input logic [1:0] bresp, output logic bready
);
  localparam IDLE=0, READ_A_ADDR=1, READ_A=2, READ_B_ADDR=3,
             READ_B=4, WRITE=5, RESPONSE=6, ACCUMULATE=7;
  logic [2:0] state;
  logic [31:0] index;
  logic signed [15:0] operand_a;
  logic signed [31:0] product_q;
  logic signed [63:0] next_sum;
  logic signed [63:0] accumulator;
  logic high_word, aw_sent, w_sent;
  assign next_sum = accumulator + {{32{product_q[31]}}, product_q};
  assign busy = state != IDLE;
  assign arvalid = state == READ_A_ADDR || state == READ_B_ADDR;
  assign araddr = (state == READ_A_ADDR ? src_a : src_b) + (index << 2);
  assign rready = state == READ_A || state == READ_B;
  assign awaddr = dst + (high_word ? 32'd4 : 32'd0);
  assign wdata = high_word ? accumulator[63:32] : accumulator[31:0];
  assign awvalid = state == WRITE && !aw_sent;
  assign wvalid = state == WRITE && !w_sent;
  assign bready = state == RESPONSE;
  always_ff @(posedge clk) begin
    if (reset) begin
      state <= IDLE; index <= 0; operand_a <= 0; accumulator <= 0; product_q <= 0;
      high_word <= 0; aw_sent <= 0; w_sent <= 0;
      done <= 0; failed <= 0; error_code <= 0;
    end else begin
      done <= 0; failed <= 0;
      case (state)
        IDLE: if (start) begin
          state <= READ_A_ADDR; index <= 0; accumulator <= 0;
          high_word <= 0; error_code <= 0;
        end
        READ_A_ADDR: if (arready) state <= READ_A;
        READ_B_ADDR: if (arready) state <= READ_B;
        READ_A, READ_B: if (rvalid) begin
          if (rresp != 0 || !rlast) begin
            failed <= 1; error_code <= 2; state <= IDLE;
          end else if (state == READ_A) begin
            operand_a <= rdata[15:0]; state <= READ_B_ADDR;
          end else begin
            product_q <= operand_a * $signed(rdata[15:0]);
            state <= ACCUMULATE;
          end
        end
        ACCUMULATE: begin
            accumulator <= next_sum;
            if (index + 1 == length) begin
              state <= WRITE; aw_sent <= 0; w_sent <= 0;
            end else begin index <= index + 1; state <= READ_A_ADDR; end
        end
        WRITE: begin
          if (awready) aw_sent <= 1;
          if (wready) w_sent <= 1;
          if ((aw_sent || awready) && (w_sent || wready)) state <= RESPONSE;
        end
        RESPONSE: if (bvalid) begin
          if (bresp != 0) begin
            failed <= 1; error_code <= 3; state <= IDLE;
          end else if (high_word) begin done <= 1; state <= IDLE; end
          else begin high_word <= 1; aw_sent <= 0; w_sent <= 0; state <= WRITE; end
        end
        default: state <= IDLE;
      endcase
    end
  end
`ifdef FORMAL
  logic f_past_valid=0;
  always @(posedge clk) begin
    f_past_valid<=1;
    if(f_past_valid && !reset && !$past(reset)) begin
      if($past(arvalid && !arready)) begin assert(arvalid); assert(araddr==$past(araddr)); end
      if($past(awvalid && !awready)) begin assert(awvalid); assert(awaddr==$past(awaddr)); end
      if($past(wvalid && !wready)) begin assert(wvalid); assert(wdata==$past(wdata)); end
      if(done) begin
        assert($past(state)==RESPONSE && $past(bvalid) && $past(bresp)==0 && $past(high_word));
      end
    end
  end
`endif
endmodule
