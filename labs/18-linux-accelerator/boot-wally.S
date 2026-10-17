/* SPDX-License-Identifier: MIT: RV64 reset handoff to generic OpenSBI dynamic. */
.section .text
.globl _start
_start:
  auipc t0,0
  addi a2,t0,64
  csrr a0,mhartid
  ld a1,32(t0)
  ld t1,40(t0)
  jr t1
  .org 32
  .quad 0x87000000
  .quad 0x80000000
  .org 64
  .quad 0x4942534f,2,0x80200000,1,0,0
