#include <stdint.h>
#include "vectors.h"
static volatile uint32_t observed[PAIRS][4];
#define FINISH (*(volatile uint32_t *)(uintptr_t)0x8000fff0u)
static uint64_t cycle64(void) {
    uint32_t a,b,c;
    do {
        __asm__ volatile("csrr %0, mcycleh":"=r"(a));
        __asm__ volatile("csrr %0, mcycle":"=r"(b));
        __asm__ volatile("csrr %0, mcycleh":"=r"(c));
    } while(a!=c);
    return ((uint64_t)a<<32)|b;
}
static uint64_t instret64(void) {
    uint32_t a,b,c;
    do {
        __asm__ volatile("csrr %0, minstreth":"=r"(a));
        __asm__ volatile("csrr %0, minstret":"=r"(b));
        __asm__ volatile("csrr %0, minstreth":"=r"(c));
    } while(a!=c);
    return ((uint64_t)a<<32)|b;
}
int main(void) {
    uint64_t c0=cycle64(),i0=instret64();
    for(unsigned i=0;i<PAIRS;i++) {
        uint32_t a=operands[i][0],b=operands[i][1],q,r,uq,ur;
        __asm__ volatile("div %0, %1, %2":"=r"(q):"r"(a),"r"(b));
        __asm__ volatile("rem %0, %1, %2":"=r"(r):"r"(a),"r"(b));
        __asm__ volatile("divu %0, %1, %2":"=r"(uq):"r"(a),"r"(b));
        __asm__ volatile("remu %0, %1, %2":"=r"(ur):"r"(a),"r"(b));
        observed[i][0]=q;observed[i][1]=r;observed[i][2]=uq;observed[i][3]=ur;
    }
    uint64_t c1=cycle64(),i1=instret64();
    uint32_t checksum=2166136261u;
    for(unsigned i=0;i<PAIRS;i++) for(unsigned j=0;j<4;j++) {
        uint32_t value=observed[i][j];
        if(value!=expected[i][j]) { FINISH=0xbad00000u|(i*4+j);for (;;) {} }
        checksum=(checksum^value)*16777619u;
    }
    if(checksum!=EXPECTED_CHECKSUM) { FINISH=0xbad10000u;for (;;) {} }
    volatile uint32_t *m=(volatile uint32_t *)(uintptr_t)0x8000fe00u;
    m[0]=(uint32_t)(c1-c0);m[1]=(uint32_t)((c1-c0)>>32);
    m[2]=(uint32_t)(i1-i0);m[3]=(uint32_t)((i1-i0)>>32);
    m[4]=checksum;m[5]=PAIRS;
    __asm__ volatile("fence iorw, iorw" ::: "memory");
    FINISH=0x600d600du;
    for (;;) {}
}
