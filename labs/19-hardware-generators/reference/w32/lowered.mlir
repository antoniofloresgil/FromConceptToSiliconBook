module {
  hw.module @Accumulator(in %clock : !seq.clock, in %reset : i1, in %Clear : i1, in %Enable : i1, in %Operand : i32, out Sum : i32, out Valid : i1, out Overflow : i1) {
    %true = hw.constant true
    %false = hw.constant false
    %c0_i32 = hw.constant 0 : i32
    %sum = seq.firreg %10 clock %clock reset sync %reset, %c0_i32 {firrtl.random_init_start = 0 : ui64} : i32
    %valid = seq.firreg %4 clock %clock reset sync %reset, %false {firrtl.random_init_start = 32 : ui64} : i1
    %overflow = seq.firreg %7 clock %clock reset sync %reset, %false {firrtl.random_init_start = 33 : ui64} : i1
    %0 = comb.concat %false, %sum : i1, i32
    %1 = comb.concat %false, %Operand : i1, i32
    %2 = comb.add bin %0, %1 {sv.namehint = "extended"} : i33
    %3 = comb.xor %Clear, %true : i1
    %4 = comb.and %3, %Enable : i1
    %5 = comb.extract %2 from 32 {sv.namehint = "_overflow_T"} : (i33) -> i1
    %6 = comb.xor %Clear, %true : i1
    %7 = comb.and %6, %Enable, %5 : i1
    %8 = comb.extract %2 from 0 {sv.namehint = "_sum_T"} : (i33) -> i32
    %9 = comb.mux bin %Enable, %8, %sum : i32
    %10 = comb.mux bin %Clear, %c0_i32, %9 : i32
    hw.output %sum, %valid, %overflow : i32, i1, i1
  }
  om.class @Accumulator_Class(%basepath: !om.basepath) {
  }
}
