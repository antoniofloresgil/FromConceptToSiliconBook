.section .text.init
.globl _start
_start:
  la sp, _stack_top
  la t0, _bss_start
  la t1, _bss_end
1: bgeu t0,t1,2f
  sw zero,0(t0)
  addi t0,t0,4
  j 1b
2: la t0, trap_failed
  csrw mtvec,t0
  call main
3: j 3b
.balign 4
trap_failed:
  csrr t0,mcause
  li t1,0x8000fff0
  sw t0,0(t1)
  j trap_failed
