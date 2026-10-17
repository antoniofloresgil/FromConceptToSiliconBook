module {
  hw.module @Accumulator(in %clock : !seq.clock, in %reset : i1, in %Clear : i1, in %Enable : i1, in %Operand : i16, out Sum : i16, out Valid : i1, out Overflow : i1) {
    %true = hw.constant true
    %false = hw.constant false
    %c0_i16 = hw.constant 0 : i16
    %sum = seq.firreg %12 clock %clock reset sync %reset, %c0_i16 {firrtl.random_init_start = 0 : ui64} : i16
    %valid = seq.firreg %6 clock %clock reset sync %reset, %false {firrtl.random_init_start = 16 : ui64} : i1
    %overflow = seq.firreg %9 clock %clock reset sync %reset, %false {firrtl.random_init_start = 17 : ui64} : i1
    %0 = comb.concat %false, %sum : i1, i16
    %1 = comb.concat %false, %Operand : i1, i16
    %2 = comb.add bin %0, %1 {sv.namehint = "extended"} : i17
    %3 = comb.xor bin %Enable, %true {sv.namehint = "_clearNow_T"} : i1
    %4 = comb.and bin %Clear, %3 {sv.namehint = "clearNow"} : i1
    %5 = comb.xor %4, %true : i1
    %6 = comb.and %5, %Enable : i1
    %7 = comb.extract %2 from 16 {sv.namehint = "_overflow_T"} : (i17) -> i1
    %8 = comb.xor %4, %true : i1
    %9 = comb.and %8, %Enable, %7 : i1
    %10 = comb.extract %2 from 0 {sv.namehint = "_sum_T"} : (i17) -> i16
    %11 = comb.mux bin %Enable, %10, %sum : i16
    %12 = comb.mux bin %4, %c0_i16, %11 : i16
    hw.output %sum, %valid, %overflow : i16, i1, i1
  }
  om.class @Accumulator_Class(%basepath: !om.basepath) {
  }
}
