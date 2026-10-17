#include <stdint.h>
#define REG(offset) (*(volatile uint32_t *)(uintptr_t)(0x10060000u+(offset)))
#define FINISH (*(volatile uint32_t *)(uintptr_t)0x8000fff0u)
volatile uint32_t irq_count;
static uint32_t a[256] __attribute__((section(".dma"),aligned(8)));
static uint32_t b[256] __attribute__((section(".dma"),aligned(8)));
static volatile uint32_t result[2] __attribute__((section(".dma"),aligned(8)));
static inline void fence(void) { __asm__ volatile("fence iorw, iorw" ::: "memory"); }
static inline uint32_t cycles(void) { uint32_t c; __asm__ volatile("csrr %0, mcycle":"=r"(c));return c; }
static void fail(uint32_t code) { FINISH=0xbad00000u|code;for (;;) {} }
static int64_t reference(unsigned n) {
    int64_t sum=0;
    for(unsigned i=0;i<n;i++) {
        // Explicit sign conversion, independent of RTL arithmetic.
        int32_t x=(int32_t)(a[i]&65535u), y=(int32_t)(b[i]&65535u);
        if(x>=32768) x-=65536;
        if(y>=32768) y-=65536;
        sum+=(int32_t)(x*y);
    }
    return sum;
}
static void launch(unsigned n, int interrupt) {
    REG(8)=(uint32_t)(uintptr_t)a; REG(12)=(uint32_t)(uintptr_t)b;
    REG(16)=(uint32_t)(uintptr_t)result; REG(20)=n;
    fence(); REG(0)=interrupt ? 3:1; fence();
}
int main(void) {
    for(unsigned i=0;i<256;i++) {
        a[i]=0xdead0000u | ((i*997u+32768u)&65535u);
        b[i]=0xbeef0000u | ((i*313u+32768u)&65535u);
    }
    // Metrics mailbox is outside the DMA window; simulator reads these words.
    volatile uint32_t *metrics=(volatile uint32_t *)(uintptr_t)0x8000fe00u;
    const unsigned sizes[]={1,8,32,128,256};
    for(unsigned k=0;k<5;k++) {
        unsigned n=sizes[k];uint32_t begin=cycles();
        int64_t expected=reference(n);
        uint32_t sw=cycles()-begin;begin=cycles();
        launch(n,0);
        unsigned timeout=200000;
        while((REG(4)&1u) && --timeout) {}
        if(!timeout || REG(4)!=2u) fail(1+k);
        fence();uint32_t hw=cycles()-begin;
        uint64_t got=((uint64_t)result[1]<<32)|result[0];
        if(got!=(uint64_t)expected) fail(10+k);
        metrics[k*3]=n;metrics[k*3+1]=sw;metrics[k*3+2]=hw;
    }
    // A real machine-external interrupt, handled by the RV32 firmware.
    __asm__ volatile("csrs mie, %0" :: "r"(1u<<11));
    __asm__ volatile("csrs mstatus, %0" :: "r"(1u<<3));
    launch(32,1);
    unsigned timeout=200000;
    while(!irq_count && --timeout) {}
    if(!timeout || irq_count!=1 || REG(4)!=2u) fail(20);
    fence();
    if((((uint64_t)result[1]<<32)|result[0])!=(uint64_t)reference(32)) fail(21);
    launch(0,0); // Invalid descriptor, no DMA, no success flag.
    if(REG(4)!=4u || REG(24)!=1u) fail(22);
    fence();FINISH=0x600d600du;
    for (;;) {}
}
