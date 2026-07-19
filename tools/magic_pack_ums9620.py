#!/usr/bin/env python3
"""Signature-preserving runtime patcher for the UMS9620 (T820) uboot.

On a fused T820 the SPL RSA-verifies uboot, so a modified+rehashed uboot is
rejected (confirmed on hardware). This tool applies the "magic" method from
unisoc_chipram_signcheck (Patch-Post-Verification): it keeps the original signed
payload byte-for-byte (so the SPL's RSA check still passes) and appends a small
AArch64 shellcode plus a patch table. At boot the SPL loads the image, verifies
the untouched payload, and jumps to a branch we place at the entry; the
shellcode copies the payload back into place, applies the patch words, then
jumps to the real _start.

Layout produced (matches magic64.cpp):

    0x000  sys_img_header (DHTB, 0x200)   mImgSize += 0x100
    0x200  jump code (0x10)               B -> shellcode
    0x210  payload (mImgSize bytes)       UNCHANGED (RSA stays valid)
    ...    shellcode (0x70) + patch_data + pad   (0xF0 total)
    ...    sprdsignedimageheader footer (0x60)   payload_offset=0x210, cert_offset+=0x100
    ...    cert / priv / dbg data
    then truncated back to the original partition size (drops only zero padding)

Patches are given as (code_offset, new_word) where code_offset is the offset
into the uboot payload (i.e. file offset - 0x200). The runtime address written
by the shellcode is LOAD_BASE + code_offset.

LOAD_BASE default 0xb5000000 was confirmed on hardware for this uboot (the
payload text base; PAC XML image base 0xb4fffe00 + 0x200 header). If a different
build relocates elsewhere, pass --load-base.

Requires aarch64-linux-gnu-as / -ld / -objcopy (binutils) to assemble the
size-dependent shellcode.

Usage:
    python3 tools/magic_pack_ums9620.py <orig_uboot.img> <out.img> \
        --patch 0xafe8=0xd503201f [--patch off=word ...] [--load-base 0xb5000000]

Known patches for this uboot (see docs/UMS9620_PORT.md):
    0xafe8=0xd503201f   remove unlock-warning message + 10s power-button timeout
    0x604c0=0xd503201f  force get_lock_status = UNLOCK
"""

import argparse
import struct
import subprocess
import sys
import tempfile

AS = "aarch64-linux-gnu-as"
LD = "aarch64-linux-gnu-ld"
OC = "aarch64-linux-gnu-objcopy"
DEFAULT_LOAD_BASE = 0xB5000000
ADD_LENGTH = 0x100        # (0x10 + 0x70 shellcode + 0xFF) & ~0xFF


def build_shellcode(size: int) -> bytes:
    """Assemble the magic64 relocation+patch shellcode for a given payload size."""
    asm = f""".section .text
.globl _start
_start :
ADRP X9, label_init
ADD X10, X9, #0x10
MOV X11, #{(size // 8) & 0xFFFF0000}
MOVK X11, #{(size // 8) & 0xFFFF}
MOV X12, #0
SUBS X13, X12, X11
B.CS . + 0x1C
LDR X13, [X10,X12,LSL#3]
STR X13, [X9,X12,LSL#3]
IC IALLUIS
ISB
ADD X12, X12, #1
B . - 0x1C
ADRP X9, label_patch
ADD X9, X9, #{(size + 0x80) & 0xFFF}
LDR W10, [X9],#4
CBZ X10, . + 0x2C
LDR W11, [X9],#4
MOV X12, #0
SUBS X13, X12, X11
B.CS . - 0x14
LDR W13, [X9],#4
STR W13, [X10],#4
IC IALLUIS
ISB
ADD X12, X12, #1
B . - 0x1C
B . - {size + 0x7C}
"""
    lds = f"""OUTPUT_FORMAT("elf64-littleaarch64")
OUTPUT_ARCH(aarch64)
ENTRY(_start)
SECTIONS {{
 . = 0x{size + 0x10:x};
 .text : {{ *(.text*) }}
 PROVIDE(label_init = 0);
 PROVIDE(label_patch = 0x{size + 0x80:x});
}}
"""
    t = tempfile.mkdtemp()
    open(f"{t}/m.s", "w").write(asm)
    open(f"{t}/m.lds", "w").write(lds)
    subprocess.check_call([AS, "-o", f"{t}/m.o", f"{t}/m.s"])
    subprocess.check_call([LD, "-o", f"{t}/m.elf", "-T", f"{t}/m.lds", f"{t}/m.o"])
    subprocess.check_call([OC, "-O", "binary", f"{t}/m.elf", f"{t}/m.bin"])
    shell = open(f"{t}/m.bin", "rb").read()
    if len(shell) != 0x70:
        raise RuntimeError(f"shellcode length 0x{len(shell):x} != 0x70")
    return shell


def pack(data: bytearray, patches, load_base: int) -> bytes:
    if data[0:4] != b"DHTB":
        raise ValueError("not a DHTB image")
    size = struct.unpack_from("<I", data, 0x30)[0]
    if struct.unpack_from("<I", data, 0x30)[0] == \
       struct.unpack_from("<I", data, size + 0x210)[0]:
        raise ValueError("image already magic-patched")

    shell = build_shellcode(size)

    foot_off = 0x200 + size
    footer = bytearray(data[foot_off:foot_off + 0x60])
    if footer[0:7] != b"SIMGHDR":
        raise ValueError("SIMGHDR footer not found")

    # patch_data: [addr, len_words, word...] per entry, then zero terminator
    patch_data = b""
    for off, word in patches:
        patch_data += struct.pack("<III", load_base + off, 1, word)
    patch_data += struct.pack("<I", 0)
    if len(patch_data) > 0x80:
        raise ValueError(f"patch_data 0x{len(patch_data):x} exceeds 0x80; "
                         f"increase add_length (not implemented)")

    out = bytearray()
    hdr = bytearray(data[0:0x200])
    struct.pack_into("<I", hdr, 0x30, size + ADD_LENGTH)
    out += hdr
    jump = 0x14000000 | (((size + 0x10) // 4) & 0x3FFFFFF)
    out += struct.pack("<I", jump) + b"\x00" * 0x0C
    out += data[0x200:0x200 + size]                       # payload, unchanged
    magic = bytearray(ADD_LENGTH - 0x10)                  # 0xF0
    magic[0:0x70] = shell
    magic[0x70:0x70 + len(patch_data)] = patch_data
    out += magic
    struct.pack_into("<Q", footer, 0x18, 0x210)           # payload_offset
    for so, oo in [(0x20, 0x28), (0x30, 0x38), (0x40, 0x48), (0x50, 0x58)]:
        if struct.unpack_from("<Q", footer, so)[0]:
            struct.pack_into("<Q", footer, oo,
                             struct.unpack_from("<Q", footer, oo)[0] + ADD_LENGTH)
    out += footer
    out += data[foot_off + 0x60:]                         # cert + trailing padding

    # keep within the original partition size (drops only zero padding)
    part_size = len(data)
    if any(out[part_size:]):
        raise ValueError("packing would overflow the partition with non-zero data")
    return bytes(out[:part_size])


def parse_patch(s):
    off, _, word = s.partition("=")
    return (int(off, 0), int(word, 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--patch", action="append", required=True, metavar="OFF=WORD",
                    help="payload code offset = new 32-bit word (hex), repeatable")
    ap.add_argument("--load-base", type=lambda x: int(x, 0), default=DEFAULT_LOAD_BASE)
    args = ap.parse_args()

    patches = [parse_patch(p) for p in args.patch]
    data = bytearray(open(args.input, "rb").read())
    out = pack(data, patches, args.load_base)
    open(args.output, "wb").write(out)
    print(f"load base: 0x{args.load_base:x}")
    for off, word in patches:
        print(f"  patch @ code 0x{off:x} (runtime 0x{args.load_base + off:x}) = 0x{word:08x}")
    print(f"wrote {args.output} ({len(out)} bytes, == partition size)")


if __name__ == "__main__":
    main()
