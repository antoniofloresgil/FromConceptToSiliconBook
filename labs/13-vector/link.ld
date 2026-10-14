OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { ram (rwx) : ORIGIN = 0x80000000, LENGTH = 1M }
SECTIONS {
    .text : { KEEP(*(.text.entry)) *(.text .text.*) } > ram
    .rodata : { *(.rodata .rodata.*) } > ram
    .data : { *(.data .data.*) *(.sdata .sdata.*) } > ram
    PROVIDE(__global_pointer$ = ADDR(.data) + 0x800);
    .bss (NOLOAD) : {
        . = ALIGN(8); __bss_start = .;
        *(.bss .bss.*) *(.sbss .sbss.*) *(COMMON)
        . = ALIGN(8); __bss_end = .;
    } > ram
    .stack (NOLOAD) : { . = ALIGN(16); . += 16384; __stack_top = .; } > ram
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
