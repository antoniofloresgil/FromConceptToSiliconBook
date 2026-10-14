OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { ram (rwx) : ORIGIN = 0x80000000, LENGTH = 1M }
SECTIONS {
    .text : { KEEP(*(.text.entry)) *(.text .text.*) } > ram
    .rodata : { *(.rodata .rodata.*) } > ram
    .data : { *(.data .data.*) *(.sdata .sdata.*) } > ram
    PROVIDE(__global_pointer$ = ADDR(.data) + 0x800);
    .secret 0x80008000 : { *(.secret) } > ram
    .stack (NOLOAD) : { . = ALIGN(16); . += 16384; __stack_top = .; } > ram
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
