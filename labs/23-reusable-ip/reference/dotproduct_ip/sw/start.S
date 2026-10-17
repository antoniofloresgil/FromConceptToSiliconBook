#include "dotproduct_regs_asm.h"
.section .text.init
.globl _start
_start:
  la sp, _stack_top
  la t0, _bss_start
  la t1, _bss_end
1: bgeu t0, t1, 2f
  sw zero, 0(t0)
  addi t0, t0, 4
  j 1b
2: la t0, trap_handler
  csrw mtvec, t0
  call main
3: j 3b

.balign 4
trap_handler:
  addi sp, sp, -16
  sw t0, 0(sp)
  sw t1, 4(sp)
  sw t2, 8(sp)
  csrr t0, mcause
  li t1, 0x8000000b
  bne t0, t1, trap_failed
  la t0, irq_count
  lw t1, 0(t0)
  addi t1, t1, 1
  sw t1, 0(t0)
  li t0, 0x10080000 + DP_IRQ_ACK
  li t1, 1
  sw t1, 0(t0)
  fence iorw, iorw
  lw t0, 0(sp)
  lw t1, 4(sp)
  lw t2, 8(sp)
  addi sp, sp, 16
  mret
trap_failed:
  li t1, 0x8000fff0
  sw t0, 0(t1)
  j trap_failed
