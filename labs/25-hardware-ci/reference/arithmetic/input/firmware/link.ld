OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 64K }
SECTIONS {
 .text : { *(.text.init) *(.text*) *(.rodata*) } > RAM
 .data : { *(.data*) *(.sdata*) } > RAM
 .bss (NOLOAD) : {
   . = ALIGN(4); _bss_start = .; *(.bss*) *(.sbss*) *(COMMON)
   . = ALIGN(4); _bss_end = .;
 } > RAM
 ASSERT(_bss_end < 0x80007000, "Code/data collides with stack")
 _stack_top = 0x80007ff0;
 .dma 0x80008000 (NOLOAD) : { *(.dma*) } > RAM
 ASSERT(. <= 0x8000c000, "DMA buffers exceed trusted window")
 /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
