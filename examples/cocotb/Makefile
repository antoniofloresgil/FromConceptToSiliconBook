SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(abspath ../verilator/accumulator.sv)
COCOTB_TOPLEVEL = accumulator
COCOTB_TEST_MODULES = test_accumulator
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

ifeq ($(SIM),icarus)
COMPILE_ARGS += -g2012
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
