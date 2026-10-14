.option norvc
.section .text.entry
.globl _start
_start:
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop
    la sp, __stack_top
    csrw mie, zero
    la t0, trap_entry
    csrw mtvec, t0
    li s0, 0                 /* Expected fault index, held by trusted test code. */
    li t0, 0x20002000        /* NAPOT 8-byte secret at 0x80008000. */
    csrw pmpaddr0, t0
    li t0, 0x20ffffff        /* NAPOT 128 MiB QEMU RAM aperture. */
    csrw pmpaddr1, t0
    li t0, 0x1f18            /* Entry 0 deny; entry 1 RAM RWX; both unlocked. */
    csrw pmpcfg0, t0
    csrr t1, pmpcfg0
    bne t0, t1, fail
    la t0, user_entry
    csrw mepc, t0
    li t0, 0x1800
    csrc mstatus, t0         /* MPP=U. satp remains bare in this reset test. */
    mret

user_entry:
    li t0, 0x80008000
denied_load:
    ld t1, 0(t0)
denied_store:
    sd zero, 0(t0)
    ecall

.balign 4
trap_entry:
    csrr t1, mcause
    beqz s0, load_fault
    li t2, 1
    beq s0, t2, store_fault
    li t2, 8
    bne t1, t2, fail
    li t2, 2
    bne s0, t2, fail
    la t0, secret
    ld t1, 0(t0)             /* M-mode bypasses these unlocked permissions. */
    li t2, 0x123456789abcdef
    bne t1, t2, fail
    la a0, pass_text
    jal ra, puts_uart
    li t0, 0x100000
    li t1, 0x5555
    sw t1, 0(t0)
    j idle
load_fault:
    li t2, 5
    bne t1, t2, fail
    la t2, denied_load
    j check_fault
store_fault:
    li t2, 7
    bne t1, t2, fail
    la t2, denied_store
check_fault:
    csrr t3, mepc
    bne t2, t3, fail
    csrr t3, mtval
    li t2, 0x80008000
    bne t2, t3, fail
    addi s0, s0, 1
    csrr t2, mepc
    addi t2, t2, 4
    csrw mepc, t2
    mret
fail:
    la a0, fail_text
    jal ra, puts_uart
    li t0, 0x100000
    li t1, 0x13333
    sw t1, 0(t0)
idle:
    wfi
    j idle
puts_uart:
    li t0, 0x10000000
1:
    lbu t1, 0(a0)
    beqz t1, 3f
2:
    lbu t2, 5(t0)
    andi t2, t2, 0x20
    beqz t2, 2b
    sb t1, 0(t0)
    addi a0, a0, 1
    j 1b
3:
    ret
.section .rodata
pass_text: .asciz "PMP_PASS: U load/store faults, precise PC/address, secret unchanged, M bypass\n"
fail_text: .asciz "FAIL PMP isolation\n"
.section .secret,"aw"
.balign 8
secret: .dword 0x123456789abcdef
