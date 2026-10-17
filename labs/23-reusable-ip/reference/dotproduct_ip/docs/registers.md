# Generated register map

| Offset | Register | Access | Reset | Behavior |
| --- | --- | --- | --- | --- |
| 0x00 | CTRL | command/rw | 0 | Byte 0 only; START reads zero. CTRL writes while busy return SLVERR. START clears prior terminal state and latches a valid descriptor. |
| 0x04 | STATUS | ro | 0 | Read snapshot retained under R backpressure; writes return SLVERR. |
| 0x08 | SRC_A | rw | 0 | Byte-strobe merge when idle; writes while busy return SLVERR. |
| 0x0c | SRC_B | rw | 0 | Byte-strobe merge when idle; writes while busy return SLVERR. |
| 0x10 | DST | rw | 0 | Byte-strobe merge when idle; destination must be 8-byte aligned and non-overlapping with inputs. |
| 0x14 | LENGTH | rw | 0 | Byte-strobe merge when idle; accepted job length is 1 through MAX_LENGTH. |
| 0x18 | ERROR_CODE | ro | 0 | 0 none, 1 descriptor, 2 DMA read, 3 DMA write. Writes return SLVERR. |
| 0x1c | IRQ_ACK | w1c | 0 | Byte 0 bit 0 clears pending; reads zero; a simultaneous new terminal event wins. |
