.text
.globl dot_rvv
.type dot_rvv, @function
/* a0=A, a1=B, a2=count; signed int16 inputs, signed int64 result in a0. */
dot_rvv:
    beqz a2, 2f
    vsetivli zero, 1, e64, m1, ta, ma
    vmv.s.x v16, zero
1:
    vsetvli t0, a2, e16, m1, ta, ma
    vle16.v v2, (a0)
    vle16.v v4, (a1)
    vwmul.vv v8, v2, v4       /* Signed 16x16 -> 32, destination EMUL=2. */
    vsetvli zero, t0, e32, m2, ta, ma
    vwredsum.vs v16, v8, v16  /* Signed 32 -> 64 reduction plus old seed. */
    slli t1, t0, 1
    add a0, a0, t1
    add a1, a1, t1
    sub a2, a2, t0
    bnez a2, 1b
    vsetivli zero, 1, e64, m1, ta, ma
    vmv.x.s a0, v16
    ret
2:
    li a0, 0
    ret
.size dot_rvv, .-dot_rvv

.globl positive_copy_rvv
.type positive_copy_rvv, @function
/* Copy positive input elements only. Nonpositive destinations stay unchanged. */
positive_copy_rvv:
    beqz a2, 2f
1:
    vsetvli t0, a2, e16, m1, ta, ma
    vle16.v v2, (a0)
    vmsgt.vx v0, v2, zero
    vse16.v v2, (a1), v0.t
    slli t1, t0, 1
    add a0, a0, t1
    add a1, a1, t1
    sub a2, a2, t0
    bnez a2, 1b
2:
    ret
.size positive_copy_rvv, .-positive_copy_rvv
