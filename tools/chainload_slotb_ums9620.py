#!/usr/bin/env python3
"""Example: build a UMS9620 (T820) slot-A uboot that chainloads slot B on VOL-UP.

This is a DESIGN EXAMPLE built on the signature-preserving magic64 method (see
docs/SLOT_B_CHAINLOAD.md and docs/MAGIC64_EXPLAINED.md). It takes the stock
uboot that boots in the active slot (slot A on a device that ships everything on
A, e.g. GammaOS), keeps the signed payload byte-for-byte so the fused SPL still
accepts it, and installs a small runtime trampoline. On every boot the trampoline
reads the volume keys; if VOLUME-UP is held it loads the `uboot_b` partition to
0xb5000000 and jumps to it, otherwise it continues the normal boot untouched.

Because slot A loads slot B (not the SPL), slot B needs no signing and can be any
uboot you put in the uboot_b partition.

Optionally (default on) it also applies the four unlock NOPs, so the chain-starter
A image is itself a silent unlocked boot.

WARNING: this is not hardware-validated. A wrong dead-region choice or a bad
offset will brick the boot. Prototype behind a diagnostic build and test on the
target (RG406H) before using a production image. See docs/SLOT_B_CHAINLOAD.md
"Open items before building".

All addresses are for the stock RG406H uboot (load base 0xb5000000,
mImgSize 0x108870) and were reverse-engineered + verified against the
disassembly. If your build differs, re-derive them (the tool verifies the hook
word and the unlock words before writing, and refuses to run on a mismatch).

Usage:
    python3 tools/chainload_slotb_ums9620.py <stock_uboot.img> <out.img>
    python3 tools/chainload_slotb_ums9620.py <stock_uboot.img> <out.img> \
        --no-unlock --tramp-addr 0xb50aff84 --load-base 0xb5000000
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_pack_ums9620 import build_shellcode, DEFAULT_LOAD_BASE

# ---- pinned stock-uboot addresses (RG406H, load base 0xb5000000) -------------
HOOK_VADDR   = 0xB5005F90    # bl 0xb5005eec  ("ANDROID: Booting slot%s" logger)
HOOK_ORIG    = 0x97FFFFD7    # the original word we replace with a branch to tramp
SLOTLOG_FN   = 0xB5005EEC    # the logger we displaced (trampoline replays it)
RETURN_VADDR = 0xB5005F94    # continue normal boot here (bl get-cached-bootmode)
READ_VOLKEYS = 0xB50767F0    # int read_volkeys(void): w0 = 0/0x72/0x73/0xE5/<0
READ_PART    = 0xB503E184    # read_partition_by_name(name,x1=count,x2=off,x3=dst)
FLUSH_RANGE  = 0xB500417C    # flush_dcache_range(start, end)
CLEANUP      = 0xB500B414    # cleanup_before_linux()
VOL_UP       = 0x73          # read_volkeys() return code for VOLUME-UP held

DEFAULT_TRAMP_ADDR = 0xB50AFF84   # 130 bytes of inter-function .text zero padding

UBOOT_B_NAME = b"uboot_b\x00"     # partition to chainload
UBOOT_B_OFF  = 0x200              # skip its DHTB header so the payload lands at base
UBOOT_B_SIZE = 0x2FF000           # bytes to read (kept <= partition size - offset)

NOP = 0xD503201F
# (code_off, stock_word, mask) - same points/masks as patch_uboot_unlock_ums9620
UNLOCK_PATCHES = [
    (0x604C0, 0x35000160, 0xFF00001F),   # get_lock_status -> UNLOCK
    (0xAFE8,  0x54000180, 0xFF00001F),   # remove INFO_UNLOCK line + 10s timeout
    (0xB2A4,  0x9400A21C, 0xFC000000),   # remove SKIP VERIFY (uart)
    (0xB2AC,  0x9401E7A2, 0xFC000000),   # remove SKIP VERIFY (screen)
]

ADD_ALIGN = 0x100


# ---- a tiny deterministic AArch64 encoder (only what the trampoline needs) ----
def movz(rd, imm16, shift=0, sf=1):
    return (0xD2800000 if sf else 0x52800000) | ((shift // 16) << 21) \
        | ((imm16 & 0xFFFF) << 5) | (rd & 31)

def movk(rd, imm16, shift=0, sf=1):
    return (0xF2800000 if sf else 0x72800000) | ((shift // 16) << 21) \
        | ((imm16 & 0xFFFF) << 5) | (rd & 31)

def add_imm(rd, rn, imm12, lsl12=False, sf=1):
    return (0x91000000 if sf else 0x11000000) | ((1 if lsl12 else 0) << 22) \
        | ((imm12 & 0xFFF) << 10) | ((rn & 31) << 5) | (rd & 31)

def cmp_imm(rn, imm12, sf=0):   # subs (w)zr, Rn, #imm12
    return (0xF1000000 if sf else 0x71000000) | ((imm12 & 0xFFF) << 10) \
        | ((rn & 31) << 5) | 31

def bl(pc, target):
    return 0x94000000 | (((target - pc) >> 2) & 0x03FFFFFF)

def b(pc, target):
    return 0x14000000 | (((target - pc) >> 2) & 0x03FFFFFF)

def b_cond(pc, target, cond):
    return 0x54000000 | ((((target - pc) >> 2) & 0x7FFFF) << 5) | (cond & 0xF)

def cbnz(pc, target, rt, sf=0):
    return (0xB5000000 if sf else 0x35000000) \
        | ((((target - pc) >> 2) & 0x7FFFF) << 5) | (rt & 31)

def adr(pc, target, rd):
    imm = target - pc
    return 0x10000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7FFFF) << 5) | (rd & 31)

COND_NE = 0x1
DSB_SY  = 0xD5033F9F
ISB     = 0xD5033FDF
BR_X0   = 0xD61F0000


def build_trampoline(tramp_addr):
    """Assemble the VOL-UP chainloader trampoline at runtime address tramp_addr.

    Layout (each entry is one 32-bit word unless noted):
      idx  instruction
       0   bl   read_volkeys
       1   cmp  w0, #0x73                 ; VOLUME-UP?
       2   b.ne .normal
       3   adr  x0, name                  ; "uboot_b"
       4   movz w1, #0xf000
       5   movk w1, #0x2f, lsl #16        ; x1 = UBOOT_B_SIZE (0x2ff000)
       6   movz x2, #0x200                ; skip DHTB header
       7   movz x3, #0xb500, lsl #16      ; x3 = 0xb5000000
       8   bl   read_partition_by_name
       9   cbnz w0, .normal               ; read failed -> normal boot (fail-safe)
      10   movz x0, #0xb500, lsl #16      ; start
      11   movz x1, #0xb500, lsl #16
      12   add  x1, x1, #0x2ff, lsl #12   ; end = 0xb52ff000
      13   bl   flush_dcache_range
      14   bl   cleanup_before_linux
      15   movz x0, #0xb500, lsl #16      ; entry = 0xb5000000
      16   dsb  sy
      17   isb
      18   br   x0
      19   .normal: bl SLOTLOG_FN         ; replay displaced slot log
      20   b    RETURN_VADDR              ; continue normal boot
      21   name: "uboot_b\0"              ; 8 bytes = 2 words
    """
    assert UBOOT_B_SIZE & 0xFFFF == 0xF000 and (UBOOT_B_SIZE >> 16) == 0x2F
    NIDX_NORMAL = 19
    NIDX_NAME = 21
    def pc(i):
        return tramp_addr + i * 4
    words = [
        bl(pc(0), READ_VOLKEYS),
        cmp_imm(0, VOL_UP),
        b_cond(pc(2), pc(NIDX_NORMAL), COND_NE),
        adr(pc(3), pc(NIDX_NAME), 0),
        movz(1, UBOOT_B_SIZE & 0xFFFF, 0, sf=0),
        movk(1, (UBOOT_B_SIZE >> 16) & 0xFFFF, 16, sf=0),
        movz(2, UBOOT_B_OFF),
        movz(3, 0xB500, 16),
        bl(pc(8), READ_PART),
        cbnz(pc(9), pc(NIDX_NORMAL), 0),
        movz(0, 0xB500, 16),
        movz(1, 0xB500, 16),
        add_imm(1, 1, 0x2FF, lsl12=True),
        bl(pc(13), FLUSH_RANGE),
        bl(pc(14), CLEANUP),
        movz(0, 0xB500, 16),
        DSB_SY,
        ISB,
        BR_X0,
        bl(pc(NIDX_NORMAL), SLOTLOG_FN),
        b(pc(20), RETURN_VADDR),
    ]
    blob = struct.pack("<%dI" % len(words), *words) + UBOOT_B_NAME
    assert len(blob) % 4 == 0
    return blob


def pack(data, tramp_addr, load_base, with_unlock):
    if data[0:4] != b"DHTB":
        raise ValueError("not a DHTB image")
    size = struct.unpack_from("<I", data, 0x30)[0]

    foot_off = 0x200 + size
    footer = bytearray(data[foot_off:foot_off + 0x60])
    if footer[0:7] != b"SIMGHDR":
        raise ValueError("SIMGHDR footer not found")
    if struct.unpack_from("<Q", footer, 0x18)[0] != 0x200:
        raise ValueError("image already magic-patched")

    # verify the hook site matches the stock word before we touch it
    hook_off = HOOK_VADDR - load_base
    actual = struct.unpack_from("<I", data, 0x200 + hook_off)[0]
    if actual != HOOK_ORIG:
        raise ValueError("hook site 0x%x = 0x%08x, expected 0x%08x; this uboot "
                         "build differs, re-derive the offsets"
                         % (HOOK_VADDR, actual, HOOK_ORIG))

    # verify the dead region is genuinely empty so we never clobber real code
    tramp = build_trampoline(tramp_addr)
    tramp_off = tramp_addr - load_base
    if tramp_off < 0 or tramp_off + len(tramp) > size:
        raise ValueError("trampoline address 0x%x is outside the payload" % tramp_addr)
    region = data[0x200 + tramp_off:0x200 + tramp_off + len(tramp)]
    if any(region):
        raise ValueError("dead region at 0x%x (%d bytes) is not empty; pick "
                         "another with --tramp-addr" % (tramp_addr, len(tramp)))

    # build the patch table: trampoline blob, then the hook branch, then unlock
    tramp_words = len(tramp) // 4
    patch_data = struct.pack("<II", tramp_addr, tramp_words) + tramp
    patch_data += struct.pack("<III", HOOK_VADDR, 1, b(HOOK_VADDR, tramp_addr))
    if with_unlock:
        for code_off, stock, mask in UNLOCK_PATCHES:
            got = struct.unpack_from("<I", data, 0x200 + code_off)[0]
            if (got & mask) != (stock & mask):
                raise ValueError("unlock site 0x%x = 0x%08x != 0x%08x; re-derive"
                                 % (code_off, got, stock))
            patch_data += struct.pack("<III", load_base + code_off, 1, NOP)
    patch_data += struct.pack("<I", 0)   # zero-address terminator

    add_length = (0x80 + len(patch_data) + ADD_ALIGN - 1) & ~(ADD_ALIGN - 1)

    shell = build_shellcode(size)
    out = bytearray()
    hdr = bytearray(data[0:0x200])
    struct.pack_into("<I", hdr, 0x30, size + add_length)
    out += hdr
    jump = 0x14000000 | (((size + 0x10) // 4) & 0x03FFFFFF)
    out += struct.pack("<I", jump) + b"\x00" * 0x0C
    out += data[0x200:0x200 + size]              # signed payload, unchanged
    magic = bytearray(add_length - 0x10)
    magic[0:0x70] = shell
    magic[0x70:0x70 + len(patch_data)] = patch_data
    out += magic
    struct.pack_into("<Q", footer, 0x18, 0x210)  # payload_offset marker
    for so, oo in [(0x20, 0x28), (0x30, 0x38), (0x40, 0x48), (0x50, 0x58)]:
        if struct.unpack_from("<Q", footer, so)[0]:
            struct.pack_into("<Q", footer, oo,
                             struct.unpack_from("<Q", footer, oo)[0] + add_length)
    out += footer
    out += data[foot_off + 0x60:]

    # keep within the original partition size (drops only trailing zero padding)
    part_size = len(data)
    if any(out[part_size:]):
        raise ValueError("packing would overflow the partition with non-zero data "
                         "(0x%x > 0x%x); the magic region does not fit"
                         % (len(out), part_size))
    return bytes(out[:part_size]), add_length, len(tramp)


def main():
    ap = argparse.ArgumentParser(
        description="Example: VOL-UP chainload slot B, magic64-delivered on T820",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="stock uboot image (DHTB-signed)")
    ap.add_argument("output", help="output uboot image (== partition size)")
    ap.add_argument("--tramp-addr", type=lambda x: int(x, 0),
                    default=DEFAULT_TRAMP_ADDR,
                    help="runtime address of the dead region to host the "
                         "trampoline (default 0x%x)" % DEFAULT_TRAMP_ADDR)
    ap.add_argument("--load-base", type=lambda x: int(x, 0),
                    default=DEFAULT_LOAD_BASE)
    ap.add_argument("--no-unlock", action="store_true",
                    help="do not also apply the four unlock NOPs")
    args = ap.parse_args()

    data = bytearray(open(args.input, "rb").read())
    try:
        out, add_length, tramp_len = pack(data, args.tramp_addr, args.load_base,
                                          not args.no_unlock)
    except ValueError as e:
        print("Error: %s" % e, file=sys.stderr)
        sys.exit(2)
    open(args.output, "wb").write(out)

    print("wrote %s (%d bytes, == partition size)" % (args.output, len(out)))
    print("  load base   : 0x%x" % args.load_base)
    print("  hook         : 0x%x  %08x -> b 0x%x" %
          (HOOK_VADDR, HOOK_ORIG, args.tramp_addr))
    print("  trampoline   : 0x%x  (%d bytes) VOL-UP -> load uboot_b -> 0xb5000000"
          % (args.tramp_addr, tramp_len))
    print("  unlock NOPs  : %s" % ("no" if args.no_unlock else "yes (4 sites)"))
    print("  magic region : 0x%x bytes" % add_length)
    print()
    print("Flash to the ACTIVE slot's uboot partition (slot A). Put the uboot you")
    print("want as the alternate boot into the uboot_b partition (it needs no")
    print("signing). Hold VOLUME-UP at power-on to boot it. NOT hardware-tested;")
    print("validate on the target first. See docs/SLOT_B_CHAINLOAD.md")


if __name__ == "__main__":
    main()
