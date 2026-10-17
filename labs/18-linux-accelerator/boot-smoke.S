/* SPDX-License-Identifier: MIT
 * Real RV64 CPU preflight for the Linux fixture, before its expensive OS boot.
 * Checks both register lanes, current read responses and actual RTL DMA.
 */
.section .text
.globl _start
_start:
  li t0,0x88000000
  li t1,0xdead8000
  sw t1,0(t0)
  li t1,0xbeef8000
  sw t1,1024(t0)
  li s1,0x88000800
  sd zero,0(s1)
  fence iorw,iorw
  // Preserve GPIO output enables at reset, exercise its independent output-value register.
  li s2,0x10060000
  li t3,0xa5
  sw t3,12(s2)
  fence iorw,iorw
  lwu t1,12(s2)
  fence i,r
  bne t1,t3,failed
  lwu t1,8(s2)
  fence i,r
  bnez t1,failed
  li t2,0x10080000
  sw t0,8(t2)
  fence iorw,iorw
  addi t1,t0,1024
  sw t1,12(t2)
  fence iorw,iorw
  sw s1,16(t2)
  fence iorw,iorw
  li t1,1
  sw t1,20(t2)
  fence iorw,iorw
  lwu t1,8(t2)
  fence i,r
  bne t1,t0,failed
  lwu t1,12(t2)
  fence i,r
  addi t3,t0,1024
  bne t1,t3,failed
  lwu t1,16(t2)
  fence i,r
  bne t1,s1,failed
  lwu t1,20(t2)
  fence i,r
  li t3,1
  bne t1,t3,failed
  sw t3,0(t2)
  fence iorw,iorw
  li t4,10000
wait_done:
  lwu t1,4(t2)
  fence i,r
  andi t3,t1,4
  bnez t3,failed
  andi t3,t1,7
  li t5,2
  beq t3,t5,completed
  addi t4,t4,-1
  bnez t4,wait_done
  j failed
completed:
  lwu t1,24(t2)
  fence i,r
  bnez t1,failed
  fence r,r
  ld t1,0(s1)
  li t3,0x40000000
  bne t1,t3,failed
  // Accelerator traffic must not change GPIO state.
  lwu t1,12(s2)
  fence i,r
  li t3,0xa5
  bne t1,t3,failed
  lwu t1,8(s2)
  fence i,r
  bnez t1,failed
  sw zero,12(s2)
  fence iorw,iorw
  la a0,pass_text
  j puts
failed:
  la a0,fail_text
puts:
  li t2,0x10000000
next_character:
  lbu t1,0(a0)
  beqz t1,halt
wait_uart:
  lbu t3,5(t2)
  fence i,r
  andi t3,t3,32
  beqz t3,wait_uart
  sb t1,0(t2)
  fence iorw,iorw
  addi a0,a0,1
  j next_character
halt:
  j halt
pass_text: .asciz "WALLY_MMIO_SMOKE_PASS\n"
fail_text: .asciz "WALLY_MMIO_SMOKE_FAIL\n"
