# Adaptation template for Vivado, NOT executed by the digital lab.
# Bind pin collections after synthesis. There is deliberately no guessed glob.
# Each Q/D collection must identify every bit and exactly one pointer direction.
foreach name {W_GRAY_Q R_SYNC1_D R_GRAY_Q W_SYNC1_D PTR_BITS W_BOUND_NS R_BOUND_NS} {
  if {![info exists $name]} { error "Integrator must supply $name" }
}
foreach name {W_GRAY_Q R_SYNC1_D R_GRAY_Q W_SYNC1_D} {
  if {[llength [set $name]] != $PTR_BITS} { error "Wrong pin count: $name" }
}
set_max_delay -datapath_only $W_BOUND_NS -from $W_GRAY_Q -to $R_SYNC1_D
set_max_delay -datapath_only $R_BOUND_NS -from $R_GRAY_Q -to $W_SYNC1_D
set_bus_skew $W_BOUND_NS -from $W_GRAY_Q -to $R_SYNC1_D
set_bus_skew $R_BOUND_NS -from $R_GRAY_Q -to $W_SYNC1_D
# Choose margins so each bound is below the corresponding minimum SOURCE period.
# Audit exception precedence. A broad asynchronous clock-group exception can
# override max-delay checks; applying this file alone does not constrain the SoC.
# Keep first-to-second synchronizer-stage paths timed in the DESTINATION domain.
# Review raw array-to-read data paths and reset recovery/removal separately.
