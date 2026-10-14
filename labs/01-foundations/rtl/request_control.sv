module request_control(input logic clk, reset, Start, Complete,
                       output logic Busy);
  typedef enum logic {Idle, Active} state_t;
  state_t State, NextState;

  always_ff @(posedge clk)
    if (reset) State <= Idle;
    else       State <= NextState;

  always_comb begin
    NextState = State;
    case (State)
      Idle:    if (Start) NextState = Active;
      Active:  if (Complete) NextState = Idle;
      default: NextState = Idle;
    endcase
  end

  assign Busy = (State == Active);
endmodule
