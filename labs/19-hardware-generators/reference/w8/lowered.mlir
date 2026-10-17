module {
  hw.module @Accumulator(in %clock : !seq.clock, in %reset : i1, in %Clear : i1, in %Enable : i1, in %Operand : i8, out Sum : i8, out Valid : i1, out Overflow : i1) {
    %true = hw.constant true
    %false = hw.constant false
    %c0_i8 = hw.constant 0 : i8
    %sum = seq.firreg %10 clock %clock reset sync %reset, %c0_i8 {firrtl.random_init_start = 0 : ui64} : i8
    %valid = seq.firreg %4 clock %clock reset sync %reset, %false {firrtl.random_init_start = 8 : ui64} : i1
    %overflow = seq.firreg %7 clock %clock reset sync %reset, %false {firrtl.random_init_start = 9 : ui64} : i1
    %0 = comb.concat %false, %sum : i1, i8
    %1 = comb.concat %false, %Operand : i1, i8
    %2 = comb.add bin %0, %1 {sv.namehint = "extended"} : i9
    %3 = comb.xor %Clear, %true : i1
    %4 = comb.and %3, %Enable : i1
    %5 = comb.extract %2 from 8 {sv.namehint = "_overflow_T"} : (i9) -> i1
    %6 = comb.xor %Clear, %true : i1
    %7 = comb.and %6, %Enable, %5 : i1
    %8 = comb.extract %2 from 0 {sv.namehint = "_sum_T"} : (i9) -> i8
    %9 = comb.mux bin %Enable, %8, %sum : i8
    %10 = comb.mux bin %Clear, %c0_i8, %9 : i8
    hw.output %sum, %valid, %overflow : i8, i1, i1
  }
  om.class @Accumulator_Class(%basepath: !om.basepath) {
  }
}
