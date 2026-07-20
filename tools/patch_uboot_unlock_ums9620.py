#!/usr/bin/env python3
"""Patch a Unisoc UMS9620 (T820) uboot to boot silently as bootloader-unlocked.

This is the UMS9620 counterpart to ``patch_uboot_unlock.py`` (UMS512 / T618).
It gives the same user-visible result: the device reports unlocked and boots
with no warning text and no timeout. The difference is how the patch is
delivered.

On a fused T820 the stock SPL RSA-verifies uboot, so a modified + rehashed
uboot is rejected (confirmed on hardware). Instead of editing the payload in
place, this tool keeps the signed uboot payload byte-for-byte and delivers the
edits with the signature-preserving ``magic64`` method (see
``magic_pack_ums9620.py`` / docs/UMS9620_PORT.md): the stock SPL still verifies
the untouched payload, then a small appended shellcode applies the patches at
runtime before jumping to the real ``_start``.

Patches applied (code offsets are relative to the uboot DHTB payload; see
docs/UMS9620_PORT.md for the reverse-engineering):

    code offset  change                    effect
    -----------  ------------------------  ------------------------------------
    0x604c0      cbnz w0 -> nop            get_lock_status always reports UNLOCK
    0xafe8       b.eq   -> nop             remove INFO_UNLOCK line + 10s timeout
    0xb2a4       bl     -> nop             remove SKIP_VERIFY line (UART print)
    0xb2ac       bl     -> nop             remove SKIP_VERIFY line (screen print)

Each patch point is verified against the stock instruction with a bitmask
(same idea as the T618 tool) before anything is written, so an image from a
different UMS9620 build that no longer matches is rejected rather than silently
mis-patched. The masks ignore only the fields that legitimately drift between
builds (branch targets, condition-branch offsets), so minor firmware variants
still apply while a genuinely different layout aborts.

Usage:
    python3 patch_uboot_unlock_ums9620.py <stock_uboot.img> <patched_uboot.img>
    python3 patch_uboot_unlock_ums9620.py <stock_uboot.img> --dry-run
    python3 patch_uboot_unlock_ums9620.py <stock_uboot.img> out.img \
        --load-base 0xb5000000

Exit codes:
    0  success
    1  a patch point did not match the expected stock instruction
    2  input is not a DHTB image / other structural error
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magic_pack_ums9620 import pack, DEFAULT_LOAD_BASE

NOP = 0xD503201F

# (code_off, stock, new, desc, mask)
#   mask 0xFF00001F : match opcode byte + Rt/cond, ignore imm19 (cbnz / b.cond)
#   mask 0xFC000000 : match bl opcode only, ignore branch target
PATCHES = [
    (0x604c0, 0x35000160, NOP,
     "force get_lock_status = UNLOCK (cbnz w0 -> nop)", 0xFF00001F),
    (0xafe8, 0x54000180, NOP,
     "remove INFO_UNLOCK line + 10s timeout (b.eq -> nop)", 0xFF00001F),
    (0xb2a4, 0x9400a21c, NOP,
     "remove SKIP_VERIFY line, UART print (bl -> nop)", 0xFC000000),
    (0xb2ac, 0x9401e7a2, NOP,
     "remove SKIP_VERIFY line, screen print (bl -> nop)", 0xFC000000),
]


def verify(data: bytearray):
    """Check every patch point against the stock instruction. Returns
    (results, failed) where results is a list of dicts and failed is the subset
    that did not match."""
    if data[0:4] != b"DHTB":
        raise ValueError("Not a DHTB image")
    size = struct.unpack_from("<I", data, 0x30)[0]

    results = []
    for code_off, stock, new, desc, mask in PATCHES:
        file_off = 0x200 + code_off
        if file_off + 4 > 0x200 + size:
            raise ValueError(f"patch offset 0x{code_off:x} is past end of code")
        actual = struct.unpack_from("<I", data, file_off)[0]
        matched = (actual & mask) == (stock & mask)
        results.append({
            "code_off": code_off, "stock": stock, "actual": actual,
            "new": new, "desc": desc, "mask": mask, "matched": matched,
            "fuzzy": matched and actual != stock,
        })
    failed = [r for r in results if not r["matched"]]
    return results, failed


def main():
    ap = argparse.ArgumentParser(
        description="Patch UMS9620/T820 uboot for silent unlocked boot "
                    "(signature-preserving)")
    ap.add_argument("input", help="Stock uboot image (DHTB-signed)")
    ap.add_argument("output", nargs="?",
                    help="Output path (omit with --dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Verify patch points match, do not write")
    ap.add_argument("--load-base", type=lambda x: int(x, 0),
                    default=DEFAULT_LOAD_BASE,
                    help=f"uboot runtime load base (default 0x{DEFAULT_LOAD_BASE:x})")
    args = ap.parse_args()

    data = bytearray(open(args.input, "rb").read())
    try:
        results, failed = verify(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"{'DRY RUN - ' if args.dry_run else ''}Verifying {len(results)} patch points:")
    for r in results:
        status = "MISMATCH" if not r["matched"] else ("ok~" if r["fuzzy"] else "ok")
        print(f"  0x{r['code_off']:05x}: {status:9s} 0x{r['stock']:08x} -> "
              f"0x{r['new']:08x}  ({r['desc']})")
        if r["fuzzy"]:
            print(f"             (stock here: 0x{r['actual']:08x}, matched via "
                  f"mask 0x{r['mask']:08x})")
        elif not r["matched"]:
            print(f"             (found: 0x{r['actual']:08x})")

    if failed:
        print(f"\n{len(failed)} patch point(s) did not match. This uboot is from a "
              "different UMS9620 build; re-derive the offsets before patching "
              "(see docs/UMS9620_PORT.md). Aborting.")
        sys.exit(1)

    if args.dry_run:
        print("\nDry run complete. All patch points match, no changes written.")
        return
    if not args.output:
        print("Error: output path required (unless --dry-run)", file=sys.stderr)
        sys.exit(2)

    patches = [(r["code_off"], r["new"]) for r in results]
    try:
        out = pack(data, patches, args.load_base)
    except ValueError as e:
        print(f"Error packing: {e}", file=sys.stderr)
        sys.exit(2)
    open(args.output, "wb").write(out)

    print(f"\nSignature-preserving patched uboot written to: {args.output}")
    print(f"  load base: 0x{args.load_base:x}  size: {len(out)} bytes (== partition size)")
    print("\nNext steps:")
    print("  1. Keep the STOCK SPL (do not modify it on a fused T820).")
    print(f"  2. Flash this image to the uboot partition.")
    print("  3. Reboot. The device boots unlocked with no warning text or delay.")


if __name__ == "__main__":
    main()
