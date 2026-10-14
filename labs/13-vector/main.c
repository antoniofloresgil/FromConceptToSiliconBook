#include <stdint.h>
#include <stddef.h>

#define MAX_N 1025
static int16_t a[MAX_N], b[MAX_N], output[MAX_N + 2];
int64_t dot_rvv(const int16_t *, const int16_t *, size_t);
void positive_copy_rvv(const int16_t *, int16_t *, size_t);

static void puts_uart(const char *text) {
    volatile unsigned char *uart = (volatile unsigned char *)0x10000000UL;
    while (*text) { while (!(uart[5] & 0x20)) {} uart[0] = *text++; }
}
static void hex(uint64_t value) {
    for (int shift = 60; shift >= 0; shift -= 4)
        { char text[2] = {"0123456789abcdef"[(value >> shift) & 15], 0}; puts_uart(text); }
    puts_uart("\n");
}
static void finish(int success) {
    __asm__ volatile("fence iorw, iorw" ::: "memory");
    *(volatile uint32_t *)0x100000UL = success ? 0x5555 : 0x3333;
    for (;;) __asm__ volatile("wfi");
}
void trap(void) {
    unsigned long cause, pc;
    __asm__ volatile("csrr %0, mcause" : "=r"(cause));
    __asm__ volatile("csrr %0, mepc" : "=r"(pc));
    puts_uart("FAIL trap cause="); hex(cause);
    puts_uart("pc="); hex(pc);
    finish(0);
}
static int64_t scalar_dot(size_t n) {
    int64_t total = 0;
    for (size_t i = 0; i < n; ++i) total += (int64_t)a[i] * (int64_t)b[i];
    return total;
}
static void check(size_t n) {
    if (dot_rvv(a, b, n) != scalar_dot(n)) { puts_uart("FAIL dot length="); hex(n); finish(0); }
    for (size_t i = 0; i < MAX_N + 2; ++i) output[i] = -12345;
    positive_copy_rvv(a, output + 1, n);
    if (output[0] != -12345 || output[n + 1] != -12345) {
        puts_uart("FAIL store guard\n"); finish(0);
    }
    for (size_t i = 0; i < n; ++i) {
        int16_t expected = a[i] > 0 ? a[i] : -12345;
        if (output[i + 1] != expected) { puts_uart("FAIL masked store\n"); finish(0); }
    }
}
void vector_main(void) {
    unsigned long bytes;
    __asm__ volatile("csrr %0, vlenb" : "=r"(bytes));
    puts_uart("VLEN_BITS="); hex(bytes * 8);
    /* Empty calls must not dereference their deliberately invalid pointers. */
    if (dot_rvv((const int16_t *)1, (const int16_t *)1, 0) != 0) finish(0);
    positive_copy_rvv((const int16_t *)1, (int16_t *)1, 0);
    uint32_t state = 2026;
    for (size_t i = 0; i < MAX_N; ++i) {
        state = state * 1664525U + 1013904223U;
        a[i] = (int16_t)((int32_t)(state & 65535U) - 32768);
        state = state * 1664525U + 1013904223U;
        b[i] = (int16_t)((int32_t)(state & 65535U) - 32768);
    }
    for (size_t n = 0; n <= 257; ++n) check(n);
    const size_t large[] = {511, 512, 513, 1023, 1024, 1025};
    for (size_t i = 0; i < sizeof(large) / sizeof(large[0]); ++i) check(large[i]);
    for (size_t i = 0; i < MAX_N; ++i) a[i] = b[i] = -32768;
    check(MAX_N);
    puts_uart("PASS signed extremes and 64-bit reduction\n");
    for (size_t i = 0; i < MAX_N; ++i) { a[i] = i & 1 ? -32768 : 32767; b[i] = 32767; }
    check(MAX_N);
    for (size_t i = 0; i < MAX_N; ++i) a[i] = b[i] = 0;
    check(MAX_N);
    puts_uart("PASS empty, chunk boundaries, masks and guarded stores\nRVV_PASS\n");
    finish(1);
}
