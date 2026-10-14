.option norvc
.option norelax
.section .text
.globl _start
_start:
    la   t0, values
    addi t1, zero, 4
    addi t2, zero, 0
loop:
    lw   t3, 0(t0)
    add  t2, t2, t3
    addi t0, t0, 4
    addi t1, t1, -1
    bne  t1, zero, loop
    la   t4, signature
    sw   t2, 0(t4)
    la   t0, values
    lb   t5, 0(t0)
    lbu  t6, 0(t0)
    sw   t5, 4(t4)
    sw   t6, 8(t4)
    addi zero, zero, 99
.globl stop
stop:
    jal  zero, stop

.section .data
.balign 4
values:
    .word -3, 7, 10, 2
.section .bss
.balign 4
.globl signature
signature:
    .space 12
