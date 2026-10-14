OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { payload (rwx) : ORIGIN = 0x80200000, LENGTH = 1M }
SECTIONS {
    .text : { KEEP(*(.text.entry)) *(.text .text.*) } > payload
    .rodata : { *(.rodata .rodata.*) } > payload
    .data : { *(.data .data.*) *(.sdata .sdata.*) } > payload
    PROVIDE(__global_pointer$ = ADDR(.data) + 0x800);
    .bss (NOLOAD) : {
        . = ALIGN(8); __bss_start = .;
        *(.bss .bss.*) *(.sbss .sbss.*) *(COMMON)
        . = ALIGN(8); __bss_end = .;
    } > payload
    .stack (NOLOAD) : {
        . = ALIGN(16); . += 16384; __stack_top = .;
    } > payload
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
