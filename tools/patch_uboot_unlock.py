#!/usr/bin/env python3
"""
Patch a Unisoc UMS512 uboot image to permanently act as bootloader-unlocked with AVB disabled.

Applies 7 binary patches to a stock uboot image:

    code offset  change                  effect
    -----------  ----------------------  -----------------------------------------
    0x78c98      cbz w0 -> b (always)    lock-state parser always writes 1 (unlocked)
    0x20330      adrp -> mov w0, #0      SKIP_VERIFY function neutered
    0x20334      stp prologue -> ret     (combined with above: func returns 0 immediately)
    0x20288      adrp -> nop             INFO_UNLOCK print call removed (1/3)
    0x2028c      add  -> nop             INFO_UNLOCK print call removed (2/3)
    0x20290      bl printf -> nop        INFO_UNLOCK print call removed (3/3)
    0x20fec      ldr w1 -> mov w1, #2    verifiedbootstate always "orange"

Net result after flashing:

    /proc/cmdline gets:
      androidboot.verifiedbootstate=orange
      androidboot.flash.locked=0
      androidboot.vbmeta.device_state=unlocked

    fastboot getvar:
      unlocked: yes
      is-userspace: yes

    uboot behavior:
      no SKIP VERIFY warning text
      no delay before boot
      AVB is skipped because uboot believes the bootloader is unlocked

Prerequisite: the device must have a patched SPL from tools/patch_spl.py installed.
Without that, SPL will RSA-verify this modified uboot and hang.

Usage:
    python3 patch_uboot_unlock.py <stock_uboot.img> <patched_uboot.img>
    python3 patch_uboot_unlock.py <stock_uboot.img> <patched_uboot.img> --dry-run

Exit codes:
    0  success
    1  a patch point did not match the expected original instruction
    2  input is not a DHTB image
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rehash import rehash


PATCHES = [
    (0x78c98, 0x34000060, 0x14000003, "force lock state parser to write 1 (unlocked)"),
    (0x20330, 0x90001080, 0x52800000, "SKIP_VERIFY func: replace adrp with mov w0, #0"),
    (0x20334, 0xA9BE7BFD, 0xD65F03C0, "SKIP_VERIFY func: replace prologue with ret"),
    (0x20288, 0xD00003A0, 0xD503201F, "INFO_UNLOCK print: adrp -> nop"),
    (0x2028c, 0x9118E400, 0xD503201F, "INFO_UNLOCK print: add -> nop"),
    (0x20290, 0x97FFBBA4, 0xD503201F, "INFO_UNLOCK print: bl printf -> nop"),
    (0x20fec, 0xB9400001, 0x52800041, "verifiedbootstate: mov w1, #2 (orange) instead of loading from global"),
]


def apply_patches(data: bytearray, dry_run: bool = False):
    if data[0:4] != b"DHTB":
        raise ValueError("Not a DHTB image")

    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    results = []

    for code_off, orig, new, desc in PATCHES:
        file_off = 0x200 + code_off
        if file_off + 4 > 0x200 + data_size:
            raise ValueError(f"Patch offset 0x{code_off:x} is past end of code")

        actual = struct.unpack_from("<I", data, file_off)[0]
        matched = actual == orig
        results.append({
            "code_off": code_off,
            "file_off": file_off,
            "expected_orig": orig,
            "actual": actual,
            "new": new,
            "desc": desc,
            "matched": matched,
        })

        if matched and not dry_run:
            struct.pack_into("<I", data, file_off, new)

    failed = [r for r in results if not r["matched"]]
    if failed:
        return results, failed

    if not dry_run:
        rh = rehash(data)
    else:
        rh = None

    return results, None


def main():
    ap = argparse.ArgumentParser(description="Patch UMS512 uboot for full unlock + AVB disable")
    ap.add_argument("input", help="Stock uboot image (DHTB-signed)")
    ap.add_argument("output", nargs="?", help="Output path for patched uboot (omit with --dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="Verify patches match, do not write")
    args = ap.parse_args()

    with open(args.input, "rb") as f:
        data = bytearray(f.read())

    try:
        results, failed = apply_patches(data, dry_run=args.dry_run)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"{'DRY RUN - ' if args.dry_run else ''}Applying {len(results)} patches:")
    for r in results:
        status = "ok" if r["matched"] else "MISMATCH"
        print(f"  0x{r['code_off']:05x}: {status:9s}  0x{r['expected_orig']:08x} -> 0x{r['new']:08x}  ({r['desc']})")
        if not r["matched"]:
            print(f"             (actual at this offset: 0x{r['actual']:08x})")

    if failed:
        print(f"\n{len(failed)} patch(es) failed pattern match. This uboot image may be")
        print("from a different firmware version. Aborting.")
        sys.exit(1)

    if args.dry_run:
        print("\nDry run complete. All patches match, no changes written.")
        return

    if not args.output:
        print("Error: output path required (unless --dry-run)", file=sys.stderr)
        sys.exit(2)

    with open(args.output, "wb") as f:
        f.write(data)

    # Get final hash for user reporting
    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    import hashlib
    final_hash = hashlib.sha256(bytes(data[0x200:0x200 + data_size])).hexdigest()

    print(f"\nPatched uboot written to: {args.output}")
    print(f"New DHTB hash:            {final_hash}")
    print("\nNext steps:")
    print("  1. Ensure SPL is already patched (tools/patch_spl.py + flash_spl.sh)")
    print(f"  2. Flash this uboot: ./scripts/flash_uboot.sh {args.output}")
    print("  3. adb reboot")


if __name__ == "__main__":
    main()
