# Original teaching example: S-mode aliases, Sv32 and a delegated store fault.
.option norvc
.option norelax
.section .text.init
.globl _start
_start:
    csrw mie, zero
    csrw mstatus, zero
    la t0, machine_trap
    csrw mtvec, t0
    la t0, supervisor_trap
    csrw stvec, t0
    li t0, (1 << 15)
    csrw medeleg, t0
    csrr t1, medeleg
    and t1, t1, t0
    beqz t1, fail
    csrw mideleg, zero

    # Unlocked TOR region [0, 0x80400000), RWX for the experiment.
    li t0, 0x20100000
    csrw pmpaddr0, t0
    li t0, 0x0f
    csrw pmpcfg0, t0

    la t0, root_table
    li t1, 2048
1:  sw zero, 0(t0)
    addi t0, t0, 4
    addi t1, t1, -1
    bnez t1, 1b

    # Root[512]: identity-map 0x80000000..0x803fffff as a 4 MiB leaf.
    la t0, root_table
    li t1, 0x200000cf
    li t2, 2048
    add t2, t0, t2
    sw t1, 0(t2)
    # Root[256]: point to the lower-level table at 0x80011000.
    la t1, leaf_table
    srli t1, t1, 12
    slli t1, t1, 10
    ori t1, t1, 1
    sw t1, 1024(t0)
    # Two virtual pages share one physical page, with different permissions.
    la t0, leaf_table
    la t1, data_page
    srli t1, t1, 12
    slli t1, t1, 10
    ori t2, t1, 0xc7
    sw t2, 0(t0)
    ori t2, t1, 0x43
    sw t2, 4(t0)

    la t0, data_page
    li t1, 0x11223344
    sw t1, 0(t0)
    la t0, begin_signature
    li t1, 5
2:  sw zero, 0(t0)
    addi t0, t0, 4
    addi t1, t1, -1
    bnez t1, 2b

    la t0, root_table
    srli t0, t0, 12
    li t1, 0x80000000
    or t0, t0, t1
    csrw satp, t0
    csrr t2, satp
    bne t2, t0, fail
    sfence.vma zero, zero
    la t0, supervisor_start
    csrw mepc, t0
    li t0, (1 << 11)    # MPP = S; MPRV, SUM and MXR remain clear.
    csrs mstatus, t0
    mret

.section .text
.balign 4
supervisor_start:
    li t0, 0x40000000
    lw t1, 0(t0)
    li t2, 0x11223344
    bne t1, t2, fail
    la t3, begin_signature
    sw t1, 0(t3)
    li t1, 0x55667788
    sw t1, 0(t0)

    li t0, 0x40001000
    li t1, 0xdeadbeef
.globl denied_store
denied_store:
    sw t1, 0(t0)       # Expected scause=15, stval=0x40001000.
    la t3, begin_signature
    lw t1, 16(t3)
    li t2, 1
    bne t1, t2, fail
    li t0, 0x40001000
    lw t1, 0(t0)
    li t2, 0x55667788
    bne t1, t2, fail   # The denied store must not change shared data.
    sw t1, 4(t3)
    li a0, 0
    ecall             # S-mode ecall (9) is intentionally not delegated.
    j fail

.balign 4
supervisor_trap:
    csrr t0, scause
    li t1, 15
    bne t0, t1, fail
    la t2, begin_signature
    sw t0, 8(t2)
    csrr t0, stval
    li t1, 0x40001000
    bne t0, t1, fail
    sw t0, 12(t2)
    csrr t0, sepc
    la t1, denied_store
    bne t0, t1, fail
    addi t0, t0, 4
    csrw sepc, t0
    li t0, 1
    sw t0, 16(t2)
    sret

.balign 4
machine_trap:
    csrr t0, mcause
    li t1, 9
    bne t0, t1, fail
    bnez a0, fail
    li t0, 1
    j finish
fail:
    li t0, 3
finish:
    la t1, tohost
    sw zero, 4(t1)
    sw t0, 0(t1)
3:  j 3b

.section .signature,"aw",@progbits
.balign 4
.globl begin_signature, end_signature
begin_signature:
    .word 0, 0, 0, 0, 0
end_signature:

.section .tohost,"aw",@progbits
.balign 64
.globl tohost, fromhost
tohost: .dword 0
.balign 64
fromhost: .dword 0

.section .page_tables,"aw",@nobits
.balign 4096
root_table: .space 4096
leaf_table: .space 4096
.section .page_data,"aw",@nobits
.balign 4096
data_page: .space 4096
