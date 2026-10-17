// SPDX-License-Identifier: MIT
import chisel3._
import circt.stage.ChiselStage
import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets.UTF_8

class Accumulator(width: Int, badClearPriority: Boolean = false) extends RawModule {
  require(width >= 1 && width <= 32)
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool())) // Synchronous active-high reset.
  val Clear = IO(Input(Bool()))
  val Enable = IO(Input(Bool()))
  val Operand = IO(Input(UInt(width.W)))
  val Sum = IO(Output(UInt(width.W)))
  val Valid = IO(Output(Bool()))
  val Overflow = IO(Output(Bool()))
  withClockAndReset(clock, reset) {
    val sum = RegInit(0.U(width.W))
    val valid = RegInit(false.B)
    val overflow = RegInit(false.B)
    val extended = sum +& Operand // Explicit carry bit; '+' would keep the width.
    val clearNow = if (badClearPriority) Clear && !Enable else Clear
    when(clearNow) {
      sum := 0.U
      valid := false.B
      overflow := false.B
    }.otherwise {
      valid := Enable
      overflow := Enable && extended(width)
      when(Enable) { sum := extended(width - 1, 0) }
    }
    Sum := sum
    Valid := valid
    Overflow := overflow
  }
}

object Emit extends App {
  require(args.length == 1, "Usage: Emit output-directory")
  for ((width, bad) <- Seq((8, false), (16, false), (32, false), (16, true))) {
    val directory = Paths.get(args(0), if (bad) "fault-w16" else s"w$width")
    Files.createDirectories(directory)
    val firrtl = ChiselStage.emitCHIRRTL(new Accumulator(width, bad))
    Files.write(directory.resolve("Accumulator.fir"), firrtl.getBytes(UTF_8))
  }
}
