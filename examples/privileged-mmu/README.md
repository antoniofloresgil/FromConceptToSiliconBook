# RV32 privileged/Sv32 experiment

Original teaching program for the book's Privileged Architecture and the MMU chapter. It boots in M-mode, configures PMP/delegation, builds Sv32 tables, enters S-mode, checks virtual aliases and traps on a deliberately denied store. Five words record the checked outcomes. The final S-mode ecall is handled in M-mode and completes through Spike's HTIF convention.

Prerequisites: a RISC-V GCC/binutils cross toolchain and Spike supporting RV32, M/S/U, Zicsr and Sv32. The small automatic lab container does not provide Spike. From this directory:

```sh
set -e
riscv64-unknown-elf-gcc -march=rv32i_zicsr -mabi=ilp32 \
  -nostdlib -nostartfiles -mcmodel=medany -Wl,--no-relax \
  -T link.ld -o sv32.elf sv32.S
riscv64-unknown-elf-objdump -d sv32.elf > sv32.dump
rm -f spike.sig
timeout 20s spike --isa=rv32i_zicsr --priv=msu -m64 \
  +signature=spike.sig +signature-granularity=4 sv32.elf
diff -i expected.signature spike.sig
```

Checked on 2026-10-14 with GCC 13.2.0 and Spike 1.1.1-dev. Expected words: `11223344`, `55667788`, `0000000f`, `40001000`, `00000001`. Both simulator exit and comparison must succeed. The program deliberately has no stack, compressed instructions or nested interrupts. Its known denied store is skipped after cause/address/PC checks; this is not a general kernel trap entry or page-repair routine.

The identity-mapped supervisor region is intentionally broad for this trusted firmware exercise. It is not a security isolation profile. Wally execution requires its full privileged configuration, loader, memory map and supported termination mechanism; retain separate RTL evidence.
