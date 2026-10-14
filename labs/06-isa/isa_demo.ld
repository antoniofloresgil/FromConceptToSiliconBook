ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 0x2000 }
SECTIONS {
  .text 0x80000000 : { *(.text*) } > RAM
  .data 0x80001000 : { *(.data*) } > RAM
  .bss  0x80001100 (NOLOAD) : { *(.bss*) *(COMMON) } > RAM
}
