.section .text.init
.globl _start
_start:
    li t0, 28
    li t1, 9
    add a0, t0, t1
    li a1, 0
    li t0, 1
    li t1, 7
loop:
    add a1, a1, t0
    addi t0, t0, 1
    blt t0, t1, loop
    li t0, -1
    slti a2, t0, 1
    la t2, begin_signature
    sd a0, 0(t2)
    sd a1, 8(t2)
    sd a2, 16(t2)
    li t0, 37
    bne a0, t0, failed
    li t0, 21
    bne a1, t0, failed
    li t0, 1
    bne a2, t0, failed
    li t0, 1
    j finish
failed:
    li t0, 3
finish:
    la t1, tohost
    sd t0, 0(t1)
halt:
    j halt

.section .tohost,"aw",@progbits
.balign 8
.globl tohost, fromhost
tohost: .dword 0
fromhost: .dword 0

.section .data
.balign 8
.globl begin_signature, end_signature
begin_signature:
    .dword 0, 0, 0
end_signature:
