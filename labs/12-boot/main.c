#include <stdint.h>

struct sbiret { long error; long value; };

static struct sbiret sbi(unsigned long eid, unsigned long fid,
                         unsigned long arg0, unsigned long arg1) {
    register unsigned long a0 __asm__("a0") = arg0;
    register unsigned long a1 __asm__("a1") = arg1;
    register unsigned long a2 __asm__("a2") = 0;
    register unsigned long a3 __asm__("a3") = 0;
    register unsigned long a4 __asm__("a4") = 0;
    register unsigned long a5 __asm__("a5") = 0;
    register unsigned long a6 __asm__("a6") = fid;
    register unsigned long a7 __asm__("a7") = eid;
    __asm__ volatile("ecall" : "+r"(a0), "+r"(a1)
                     : "r"(a2), "r"(a3), "r"(a4), "r"(a5), "r"(a6), "r"(a7)
                     : "memory");
    return (struct sbiret){(long)a0, (long)a1};
}

/* QEMU virt, one hart, byte-wide NS16550 registers, polling only. */
static void putc_uart(char ch) {
    volatile unsigned char *uart = (volatile unsigned char *)0x10000000UL;
    while (!(uart[5] & 0x20)) {}
    __asm__ volatile("fence iorw, iorw" ::: "memory");
    uart[0] = ch;
}
static void puts_uart(const char *s) {
    while (*s) putc_uart(*s++);
}
static void hex(unsigned long value) {
    puts_uart("0x");
    for (int shift = 60; shift >= 0; shift -= 4)
        putc_uart("0123456789abcdef"[(value >> shift) & 15]);
    putc_uart('\n');
}
static int available(unsigned long eid) {
    struct sbiret result = sbi(0x10, 3, eid, 0);
    return result.error == 0 && result.value != 0;
}

void boot_main(unsigned long hart, unsigned long dtb) {
    puts_uart("HSD supervisor payload\nhart="); hex(hart);
    puts_uart("dtb="); hex(dtb);
    unsigned long satp;
    __asm__ volatile("csrr %0, satp" : "=r"(satp));
    if (satp != 0 || dtb == 0 || (dtb & 7) != 0) {
        puts_uart("FAIL handoff\n"); return;
    }
    /* Read the big-endian FDT magic without assuming a host-endian struct. */
    volatile unsigned char *fdt = (volatile unsigned char *)dtb;
    if (fdt[0] != 0xd0 || fdt[1] != 0x0d || fdt[2] != 0xfe || fdt[3] != 0xed) {
        puts_uart("FAIL dtb magic\n"); return;
    }
    puts_uart("PASS handoff: satp=0, aligned FDT magic\n");
    struct sbiret version = sbi(0x10, 0, 0, 0);
    struct sbiret implementation = sbi(0x10, 1, 0, 0);
    if (version.error != 0 || implementation.error != 0 || implementation.value != 1) {
        puts_uart("FAIL SBI base\n"); return;
    }
    puts_uart("SBI specification="); hex(version.value);
    puts_uart("PASS SBI base: OpenSBI implementation\n");
    if (!available(0x54494d45) || !available(0x53525354)) {
        puts_uart("FAIL required extension\n"); return;
    }
    /* Clear timer pending state; interrupt delivery is a separate exercise. */
    if (sbi(0x54494d45, 0, ~0UL, 0).error != 0) {
        puts_uart("FAIL TIME\n"); return;
    }
    puts_uart("PASS TIME: timer disarmed\n");
    if (sbi(0x7fffffff, 0, 0, 0).error != -2) {
        puts_uart("FAIL unsupported extension\n"); return;
    }
    puts_uart("PASS unsupported extension: -2\nBOOT_PASS\n");
    /* SRST reset_type=0 (shutdown), reset_reason=0 (normal). */
    sbi(0x53525354, 0, 0, 0);
    puts_uart("FAIL SRST returned\n");
}
