#include "Vaccumulator.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

#include <array>
#include <cstdint>
#include <iostream>

struct Stimulus {
    bool reset;
    bool clear;
    bool enable;
    std::uint16_t operand;
};

int main(int argc, char** argv) {
    VerilatedContext context;
    context.commandArgs(argc, argv);
    context.traceEverOn(true);
    Vaccumulator dut{&context};
    VerilatedVcdC trace;
    dut.trace(&trace, 3);
    trace.open("accumulator.vcd");
    if (!trace.isOpen()) {
        std::cerr << "Cannot open accumulator.vcd\n";
        dut.final();
        return 1;
    }

    dut.clk = 0;
    dut.reset = 1;
    dut.Clear = 0;
    dut.Enable = 0;
    dut.Operand = 0;

    // Each sample has a distinct timestamp: low, rising edge, falling edge.
    auto evaluate = [&]() {
        dut.eval();
        trace.dump(context.time());
        context.timeInc(5);
    };

    const std::array<Stimulus, 14> tests{{
        {true,  false, false,     0}, // Reset.
        {true,  false, true,     99}, // Reset wins over enable.
        {false, false, true,      5},
        {false, false, true,      9},
        {false, false, false, 12345}, // Hold sum; valid/overflow low.
        {false, true,  true,    100}, // Clear wins over enable.
        {false, false, true,  60000},
        {false, false, true,  10000}, // 70000 wraps to 4464.
        {false, false, false,     7}, // Overflow must not stay asserted.
        {false, false, true,  65535}, // Another wrap.
        {false, true,  false,     0},
        {false, false, true,  65535}, // Exact maximum; no overflow.
        {false, false, true,      1}, // Wrap to zero.
        {true,  false, true,      3}  // Reset nonzero/overflow state.
    }};

    std::uint32_t expected_sum = 0;
    unsigned failures = 0;
    unsigned cycle = 0;
    for (const auto& input : tests) {
        dut.reset = input.reset;
        dut.Clear = input.clear;
        dut.Enable = input.enable;
        dut.Operand = input.operand;
        dut.clk = 0;
        evaluate(); // Settle inputs before the active edge.

        bool expected_valid = false;
        bool expected_overflow = false;
        if (input.reset || input.clear) {
            expected_sum = 0;
        } else if (input.enable) {
            const std::uint32_t total = expected_sum + input.operand;
            expected_sum = total % 65536u;
            expected_overflow = total >= 65536u;
            expected_valid = true;
        }

        dut.clk = 1;
        evaluate(); // Commit the clocked updates before checking outputs.
        if (dut.Sum != expected_sum
            || static_cast<bool>(dut.Valid) != expected_valid
            || static_cast<bool>(dut.Overflow) != expected_overflow) {
            ++failures;
            std::cerr << "FAIL cycle " << cycle
                      << ": sum=" << dut.Sum << " expected=" << expected_sum
                      << ", valid=" << unsigned(dut.Valid)
                      << " expected=" << expected_valid
                      << ", overflow=" << unsigned(dut.Overflow)
                      << " expected=" << expected_overflow << '\n';
        }

        dut.clk = 0;
        evaluate();
        ++cycle;
    }

    dut.final();
    trace.close();
    if (failures != 0) return 1;
    std::cout << "PASS: " << cycle << " cycles checked\n";
    return 0;
}
