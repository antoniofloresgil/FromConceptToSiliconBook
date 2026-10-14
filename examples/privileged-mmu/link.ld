OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
  . = 0x80000000;
  .text : { *(.text.init) *(.text .text.*) }
  ASSERT(. <= 0x80002000, "Code overlaps the signature")
  . = 0x80002000;
  .signature : { *(.signature) }
  . = 0x80003000;
  .tohost : { *(.tohost) }
  . = 0x80010000;
  .page_tables (NOLOAD) : { *(.page_tables) }
  . = 0x80012000;
  .page_data (NOLOAD) : { *(.page_data) }
}
