#!/usr/bin/env python3
"""
Patch Unisoc UMS512 SPL to NOP out all RSA signature verification call sites.

The SPL has a recurring verify pattern at multiple call sites:

    bl   0xa57c        # 940000xx (call to RSA verify function)
    cbz  w0, +0x60     # 34000060 (skip error handler if verify passed)
    mov  w0, #5        # 528000a0 (error code 5)
    bl   halt_infinite # 97ffffxx (halt/infinite-loop error handler)

This tool finds every occurrence of that 4-instruction pattern and replaces
all four instructions with NOPs (0xD503201F). It then calls rehash() to
update the DHTB SHA256 and the SIMGHDR data hash so that BootROM (which
checks DHTB hash but not RSA signature) will accept the modified SPL.

Usage:
    python3 patch_spl.py <stock_spl.img> <output.img>
    python3 patch_spl.py <stock_spl.img> <output.img> --dry-run
"""

import argparse
import hashlib
import os
import struct
import sys

# Allow importing rehash from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rehash import rehash


NOP = 0xD503201F
NOP_BYTES = struct.pack("<I", NOP)

# Pattern component values
CBZ_W0 = 0x34000060  # cbz w0, +12 bytes (skip error handler)
MOV_W0_5 = 0x528000A0  # mov w0, #5 (error code used at every verify call site)


def find_verify_sites(code: bytes, code_base: int = 0x200):
    """Yield offsets (within the file) of `cbz w0, +0x60` instructions that
    follow a `bl` and are followed by `mov w0, #<small>` and another `bl`.

    code_base: offset within the file where the code payload starts (0x200 for DHTB).
    """
    hits = []
    # Scan on instruction boundaries within the code payload
    for off in range(code_base + 4, len(code) - 12, 4):
        cbz = struct.unpack_from("<I", code, off)[0]
        if cbz != CBZ_W0:
            continue
        bl_before = struct.unpack_from("<I", code, off - 4)[0]
        # bl opcode: top 6 bits = 100101
        if (bl_before >> 26) != 0b100101:
            continue
        mov_inst = struct.unpack_from("<I", code, off + 4)[0]
        if mov_inst != MOV_W0_5:
            continue
        bl_after = struct.unpack_from("<I", code, off + 8)[0]
        if (bl_after >> 26) != 0b100101:
            continue
        hits.append(off - 4)  # report address of the leading bl
    return hits


def patch_spl(data: bytearray, dry_run: bool = False) -> dict:
    if data[0:4] != b"DHTB":
        raise ValueError("Input is not a DHTB image")

    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    code_end = 0x200 + data_size
    code_view = bytes(data[:code_end])

    sites = find_verify_sites(code_view, code_base=0x200)
    if not sites:
        raise ValueError("No verify call sites found - pattern did not match")

    patched_bytes = 0
    for bl_off in sites:
        if dry_run:
            continue
        # Replace 4 instructions (16 bytes): bl, cbz, mov, bl
        for i in range(4):
            data[bl_off + i * 4: bl_off + i * 4 + 4] = NOP_BYTES
            patched_bytes += 4

    result = {
        "sites": sites,
        "site_count": len(sites),
        "patched_bytes": patched_bytes,
        "dry_run": dry_run,
    }

    if not dry_run:
        rh = rehash(data)
        result["rehash"] = rh

    return result


def main():
    ap = argparse.ArgumentParser(description="Patch UMS512 SPL to skip RSA verify")
    ap.add_argument("input", help="Stock SPL image (DHTB-signed)")
    ap.add_argument("output", nargs="?", help="Output path for patched SPL (omit with --dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="Scan only, do not modify")
    args = ap.parse_args()

    with open(args.input, "rb") as f:
        data = bytearray(f.read())

    try:
        result = patch_spl(data, dry_run=args.dry_run)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {result['site_count']} RSA verify call sites in {args.input}:")
    for off in result["sites"]:
        code_off = off - 0x200
        print(f"  file 0x{off:04x}  (code offset 0x{code_off:04x})")

    if result["dry_run"]:
        print("\nDry run: no changes written.")
        return

    if not args.output:
        print("Error: output path required (unless --dry-run)", file=sys.stderr)
        sys.exit(2)

    with open(args.output, "wb") as f:
        f.write(data)

    rh = result["rehash"]
    print(f"\nPatched {result['patched_bytes']} bytes across {result['site_count']} sites.")
    print(f"New DHTB hash:    {rh['new_hash']}")
    print(f"Output:           {args.output}")
    print("\nNext steps:")
    print(f"  1. Push to device: adb push {args.output} /data/local/tmp/spl.img")
    print("  2. Disable write-protect: adb shell 'echo 0 > /sys/block/mmcblk0boot0/force_ro'")
    print("  3. Flash boot0:    adb shell 'dd if=/data/local/tmp/spl.img of=/dev/block/mmcblk0boot0 bs=4096'")
    print("  4. Flash boot1:    adb shell 'echo 0 > /sys/block/mmcblk0boot1/force_ro && dd if=/data/local/tmp/spl.img of=/dev/block/mmcblk0boot1 bs=4096'")
    print("  5. Reboot and enjoy unrestricted uboot modification.")


if __name__ == "__main__":
    main()
