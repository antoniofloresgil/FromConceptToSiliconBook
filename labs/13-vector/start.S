.section .text.entry
.globl _start
_start:
    csrw mie, zero
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop
    la sp, __stack_top
    la t0, __bss_start
    la t1, __bss_end
1:
    bgeu t0, t1, 2f
    sd zero, 0(t0)
    addi t0, t0, 8
    j 1b
2:
    la t0, trap_entry
    csrw mtvec, t0
    li t0, 0x200              /* mstatus.VS=Initial; enable vector state. */
    csrs mstatus, t0
    csrw vstart, zero
    call vector_main
3:
    wfi
    j 3b

.balign 4
trap_entry:
    tail trap
