import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge


@cocotb.test(timeout_time=20, timeout_unit="us")
async def accumulator_matches_reference(dut):
    dut.clk.value = 0
    dut.reset.value = 1
    dut.Clear.value = 0
    dut.Enable.value = 0
    dut.Operand.value = 0
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # reset, clear, enable, operand
    vectors = [
        (1, 0, 0, 0),
        (1, 0, 1, 99),
        (0, 0, 1, 5),
        (0, 0, 1, 9),
        (0, 0, 0, 12345),
        (0, 1, 1, 100),
        (0, 0, 1, 60000),
        (0, 0, 1, 10000),
        (0, 0, 0, 7),
        (0, 0, 1, 65535),
        (0, 1, 0, 0),
        (0, 0, 1, 65535),
        (0, 0, 1, 1),
        (1, 0, 1, 3),
    ]
    rng = random.Random(2026)
    for _ in range(100):
        vectors.append(
            (int(rng.random() < 0.05), int(rng.random() < 0.1),
             rng.randrange(2), rng.randrange(65536))
        )

    expected_sum = 0
    for cycle, (reset, clear, enable, operand) in enumerate(vectors):
        await FallingEdge(dut.clk)
        dut.reset.value = reset
        dut.Clear.value = clear
        dut.Enable.value = enable
        dut.Operand.value = operand

        if reset or clear:
            expected_sum, expected_valid, expected_overflow = 0, 0, 0
        elif enable:
            total = expected_sum + operand
            expected_sum = total % 65536
            expected_valid = 1
            expected_overflow = int(total >= 65536)
        else:
            expected_valid, expected_overflow = 0, 0

        await RisingEdge(dut.clk)
        await ReadOnly()  # Wait until clocked updates and combinational logic settle.
        actual = (
            int(dut.Sum.value), int(dut.Valid.value), int(dut.Overflow.value)
        )
        expected = (expected_sum, expected_valid, expected_overflow)
        assert actual == expected, (
            f"cycle={cycle}, stimulus={(reset, clear, enable, operand)}, "
            f"actual={actual}, expected={expected}"
        )

    dut._log.info("PASS: %d cycles checked (seed=2026)", len(vectors))
