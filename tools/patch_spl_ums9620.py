#!/usr/bin/env python3
"""Patch a Unisoc UMS9620 (T820) SPL to skip image signature verification.

This is the UMS9620 counterpart to ``patch_spl.py`` (which targets UMS512 /
T618). The T618 tool scans for a uniform ``bl / cbz w0,+0x60 / mov w0,#5 / bl``
verify pattern; the UMS9620 SPL does not use that shape (its verify guards use
``cbz w0,+0x54/+0x58`` with varied error codes), so a different approach is
needed.

On UMS9620 the SPL routes every image check through a single verify dispatcher
at code offset ``0x045b4``. It is called with an image index in ``w0`` and
returns ``0`` on success; there are 9 call sites and each one gates on
``cbz w0`` immediately after the call. Neutering the dispatcher prologue to::

    movz w0, #0     0x52800000
    ret             0xd65f03c0

makes every one of those 9 gates take the success path, so no image
(sml/teecfg/trustos/uboot/...) is actually verified. The DHTB/SIMGHDR hashes
are then regenerated with ``rehash.py`` so BootROM (which checks the DHTB hash,
not the RSA signature) accepts the modified SPL.

Same rationale as the T618 flow: BootROM verifies only the DHTB SHA256, so a
modified-then-rehashed SPL loads, and the patched SPL no longer RSA-verifies
anything downstream. See docs/UMS9620_PORT.md for the full port status.

STATUS: does NOT work on a fused (production) T820. Unlike T618, the T820 SPL
is cryptographically verified (its DHTB hash is not SHA256(payload) and the
SIMGHDR carries an RSA cert), so a modified + rehashed SPL is rejected by
BootROM and the device returns to download mode (confirmed on hardware). This
tool is kept only for reference / un-fused devices. On a fused T820 you must
keep the stock SPL and patch the uboot with a signature-preserving method
(magic64 + difftool, or bsp_sign_fxxker). See docs/UMS9620_PORT.md.

Usage:
    python3 patch_spl_ums9620.py <stock_spl.img> <patched_spl.img>
    python3 patch_spl_ums9620.py <stock_spl.img> --dry-run
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rehash import rehash

VERIFY_DISPATCHER = 0x045b4          # code offset of the verify dispatcher
# stock prologue: adrp x1, <page> ; add x1, x1, #<imm>
STOCK_W0_MASK = 0x9F00001F           # adrp opcode + Rd, ignore imm
STOCK_W0_VAL = 0x90000001            # adrp x1, ...
STOCK_W1_MASK = 0xFFC003FF           # add x1,x1,#imm : opcode+regs, ignore imm12
STOCK_W1_VAL = 0x91000021            # add x1, x1, #...
NEW_W0 = 0x52800000                  # movz w0, #0
NEW_W1 = 0xD65F03C0                  # ret


def patch(data: bytearray, dry_run: bool = False):
    if data[0:4] != b"DHTB":
        raise ValueError("Not a DHTB image")
    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    off = 0x200 + VERIFY_DISPATCHER
    if off + 8 > 0x200 + data_size:
        raise ValueError("verify dispatcher offset past end of code")
    w0 = struct.unpack_from("<I", data, off)[0]
    w1 = struct.unpack_from("<I", data, off + 4)[0]
    already = (w0 == NEW_W0 and w1 == NEW_W1)
    matches = ((w0 & STOCK_W0_MASK) == STOCK_W0_VAL and
               (w1 & STOCK_W1_MASK) == STOCK_W1_VAL)
    info = {"offset": VERIFY_DISPATCHER, "actual": (w0, w1),
            "already_patched": already, "matched": matches}
    if already:
        return info, None
    if not matches:
        return info, "MISMATCH"
    if not dry_run:
        struct.pack_into("<I", data, off, NEW_W0)
        struct.pack_into("<I", data, off + 4, NEW_W1)
        info["rehash"] = rehash(data)
    return info, None


def main():
    ap = argparse.ArgumentParser(description="Patch UMS9620 SPL to skip verify")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = bytearray(open(args.input, "rb").read())
    try:
        info, err = patch(data, args.dry_run)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    a0, a1 = info["actual"]
    print(f"verify dispatcher @ code 0x{info['offset']:05x}: {a0:08x} {a1:08x}")
    if info["already_patched"]:
        print("Already patched (movz w0,#0 ; ret). Nothing to do.")
        return
    if err == "MISMATCH":
        print("Prologue does not match the expected adrp/add. This SPL may be a "
              "different UMS9620 build; re-derive the dispatcher offset before "
              "patching.", file=sys.stderr)
        sys.exit(1)
    if args.dry_run:
        print("Dry run: dispatcher matches, would patch to 52800000 d65f03c0.")
        return
    if not args.output:
        print("Error: output path required (unless --dry-run)", file=sys.stderr)
        sys.exit(2)
    open(args.output, "wb").write(data)
    rh = info.get("rehash", {})
    print(f"Patched -> {args.output}")
    print(f"New DHTB hash: {rh.get('new_hash','?')}")


if __name__ == "__main__":
    main()
