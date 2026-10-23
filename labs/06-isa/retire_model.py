#!/usr/bin/env python3
"""A software stand-in for a processor's retirement log (standard library only).

This is not RTL. It executes the RV64I base instructions of a statically linked ELF and writes one line per
retired instruction in the shape of Spike's --log-commits output, which is what a processor testbench logger
produces for a differential check. `--fault slt-unsigned` seeds a defect that the reference model does not
have: slt and slti compare as unsigned numbers.

Usage: python retire_model.py check.elf --log dut.log [--fault slt-unsigned]
                              [--signature dut.sig]   (words between begin_signature and end_signature)
"""
import argparse
from pathlib import Path
import struct

MASK = (1 << 64) - 1


def signed(value, bits=64):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


def sext(value, bits):
    return signed(value, bits) & MASK


class Elf:
    def __init__(self, data):
        if data[:4] != b"\x7fELF" or data[4] != 2:
            raise SystemExit("A 64-bit ELF file is required")
        self.entry, phoff, shoff = struct.unpack_from("<QQQ", data, 0x18)
        phentsize, phnum = struct.unpack_from("<HH", data, 0x36)
        shentsize, shnum = struct.unpack_from("<HH", data, 0x3A)
        self.memory = {}
        for index in range(phnum):
            kind, _flags, offset, vaddr, _paddr, filesz, memsz, _align = struct.unpack_from("<IIQQQQQQ", data, phoff + index * phentsize)
            if kind == 1:
                for position in range(memsz):
                    self.memory[vaddr + position] = data[offset + position] if position < filesz else 0
        self.symbols = {}
        sections = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + index * shentsize) for index in range(shnum)]
        for _name, kind, _flags, _addr, offset, size, link, _info, _align, entsize in sections:
            if kind == 2:  # symbol table
                strings = sections[link][4]
                for position in range(0, size, entsize):
                    name_offset, _info, _other, _shndx, value, _size = struct.unpack_from("<IBBHQQ", data, offset + position)
                    end = data.index(b"\0", strings + name_offset)
                    self.symbols[data[strings + name_offset:end].decode()] = value


class Hart:
    def __init__(self, elf, fault):
        self.memory, self.pc, self.fault = dict(elf.memory), elf.entry, fault
        self.x = [0] * 32

    def load(self, address, size):
        return sum(self.memory.get(address + index, 0) << (8 * index) for index in range(size))

    def store(self, address, size, value):
        for index in range(size):
            self.memory[address + index] = (value >> (8 * index)) & 0xFF

    def step(self):
        """Execute one instruction; return (pc, encoding, rd, value, memory access)."""
        pc = self.pc
        insn = self.load(pc, 4)
        opcode, rd, funct3, rs1, rs2, funct7 = insn & 0x7F, (insn >> 7) & 31, (insn >> 12) & 7, (insn >> 15) & 31, (insn >> 20) & 31, insn >> 25
        a, b = self.x[rs1], self.x[rs2]
        imm_i = signed(insn >> 20, 12)
        imm_s = signed(((insn >> 25) << 5) | ((insn >> 7) & 31), 12)
        imm_b = signed(((insn >> 31) << 12) | (((insn >> 7) & 1) << 11) | (((insn >> 25) & 63) << 5) | (((insn >> 8) & 15) << 1), 13)
        imm_u = signed(insn & 0xFFFFF000, 32)
        imm_j = signed(((insn >> 31) << 20) | (((insn >> 12) & 255) << 12) | (((insn >> 20) & 1) << 11) | (((insn >> 21) & 1023) << 1), 21)
        next_pc, result, access = pc + 4, None, None
        less = (lambda x, y: (x & MASK) < (y & MASK)) if self.fault == "slt-unsigned" else (lambda x, y: signed(x) < signed(y))
        if opcode == 0x37:
            result = imm_u & MASK
        elif opcode == 0x17:
            result = (pc + imm_u) & MASK
        elif opcode == 0x6F:
            result, next_pc = pc + 4, (pc + imm_j) & MASK
        elif opcode == 0x67:
            result, next_pc = pc + 4, (a + imm_i) & ~1 & MASK
        elif opcode == 0x63:
            take = {0: a == b, 1: a != b, 4: signed(a) < signed(b), 5: signed(a) >= signed(b),
                    6: a < b, 7: a >= b}[funct3]
            if take:
                next_pc = (pc + imm_b) & MASK
        elif opcode == 0x03:
            size = 1 << (funct3 & 3)
            address = (a + imm_i) & MASK
            raw = self.load(address, size)
            result = raw if funct3 >= 4 else sext(raw, 8 * size)
            access = (address, None)
        elif opcode == 0x23:
            size = 1 << funct3
            address = (a + imm_s) & MASK
            value = b & ((1 << (8 * size)) - 1)
            self.store(address, size, value)
            access = (address, value, size)
        elif opcode in (0x13, 0x33):
            y = imm_i if opcode == 0x13 else b
            shift = y & 63
            sub = opcode == 0x33 and funct7 == 0x20
            if funct3 == 0:
                result = (a - y if sub else a + y) & MASK
            elif funct3 == 1:
                result = (a << shift) & MASK
            elif funct3 == 2:
                result = int(less(a, y))
            elif funct3 == 3:
                result = int((a & MASK) < (y & MASK))
            elif funct3 == 4:
                result = (a ^ y) & MASK
            elif funct3 == 5:
                arithmetic = (insn >> 30) & 1
                result = (signed(a) >> shift) & MASK if arithmetic else (a & MASK) >> shift
            elif funct3 == 6:
                result = (a | y) & MASK
            else:
                result = (a & y) & MASK
        elif opcode in (0x1B, 0x3B):
            y = imm_i if opcode == 0x1B else b
            shift = y & 31
            sub = opcode == 0x3B and funct7 == 0x20
            if funct3 == 0:
                result = sext(a - y if sub else a + y, 32)
            elif funct3 == 1:
                result = sext((a << shift) & 0xFFFFFFFF, 32)
            else:
                word = a & 0xFFFFFFFF
                result = sext(signed(word, 32) >> shift if (insn >> 30) & 1 else word >> shift, 32)
        else:
            raise SystemExit(f"Unsupported instruction 0x{insn:08x} at pc 0x{pc:x}")
        if result is not None and rd:
            self.x[rd] = result & MASK
        self.pc = next_pc
        return pc, insn, (rd if result is not None and rd else None), result, access


def log_line(pc, insn, rd, value, access):
    text = f"core   0: 3 0x{pc:016x} (0x{insn:08x})"
    if rd:
        text += f" x{rd:<2d} 0x{value & MASK:016x}"
    if access:
        text += f" mem 0x{access[0]:016x}" + (f" 0x{access[1]:0{access[2] * 2}x}" if access[1] is not None else "")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("elf")
    parser.add_argument("--log", required=True)
    parser.add_argument("--signature")
    parser.add_argument("--fault", choices=["none", "slt-unsigned"], default="none")
    parser.add_argument("--limit", type=int, default=100000)
    args = parser.parse_args()
    elf = Elf(Path(args.elf).read_bytes())
    hart, lines = Hart(elf, args.fault), []
    for _ in range(args.limit):
        pc, insn, rd, value, access = hart.step()
        lines.append(log_line(pc, insn, rd, value, access))
        if insn == 0x0000006F:  # jal x0, 0: the program's halt loop
            break
    else:
        raise SystemExit("The program did not reach its halt loop")
    Path(args.log).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.signature:
        begin, end = elf.symbols["begin_signature"], elf.symbols["end_signature"]
        words = [f"{hart.load(address, 8):016x}" for address in range(begin, end, 8)]
        Path(args.signature).write_text("\n".join(words) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
