#!/usr/bin/env python3
"""
Modify strings inside a Unisoc uboot image and re-hash automatically.

This is a convenience wrapper around rehash.py that does byte-for-byte string
replacement inside the uboot code payload. Replacements must preserve length
(the bytes around them are instructions and must not shift).

Usage:
    python3 modify_uboot.py uboot.img -o uboot_modified.img \
        --replace "OLD STRING=NEW STRING" \
        --replace "Another old=Another new"

Each --replace argument is a pair separated by '='. Both sides must be exactly
the same byte length. Use --replace-file for more complex changes.

You can also mask a string with a fixed character (common for unlock-flag text):
    python3 modify_uboot.py uboot.img -o uboot_modified.img \
        --mask "LOCK FLAG IS : UNLOCK" --mask-char "1"
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rehash import rehash


def apply_replace(data: bytearray, old: bytes, new: bytes) -> int:
    if len(old) != len(new):
        raise ValueError(
            f"replacement length mismatch: old={len(old)} new={len(new)}"
        )
    count = 0
    start = 0
    while True:
        idx = data.find(old, start)
        if idx < 0:
            break
        data[idx:idx+len(old)] = new
        count += 1
        start = idx + len(new)
    return count


def apply_mask(data: bytearray, target: bytes, mask_char: bytes) -> int:
    if len(mask_char) != 1:
        raise ValueError("mask-char must be a single byte")
    replacement = mask_char * len(target)
    return apply_replace(data, target, replacement)


def main():
    ap = argparse.ArgumentParser(description="Modify strings in uboot and re-hash")
    ap.add_argument("input", help="Stock uboot image (DHTB-signed)")
    ap.add_argument("-o", "--output", required=True, help="Output path for modified image")
    ap.add_argument(
        "--replace", action="append", default=[],
        help='String replacement "OLD=NEW" (lengths must match); repeatable',
    )
    ap.add_argument(
        "--mask", action="append", default=[],
        help="Mask a string with a fixed character (use with --mask-char); repeatable",
    )
    ap.add_argument(
        "--mask-char", default="1",
        help="Single character to use for masking (default: '1')",
    )
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.replace and not args.mask:
        print("Error: specify at least one --replace or --mask", file=sys.stderr)
        sys.exit(2)

    with open(args.input, "rb") as f:
        data = bytearray(f.read())

    if data[0:4] != b"DHTB":
        print("Error: input is not a DHTB image", file=sys.stderr)
        sys.exit(1)

    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    code_start, code_end = 0x200, 0x200 + data_size

    total = 0
    mask_char = args.mask_char.encode()

    # Operate ONLY on the code section (not the SIMGHDR) to avoid shifting
    # any signature/metadata fields accidentally
    code_slice = bytearray(data[code_start:code_end])

    for spec in args.replace:
        if "=" not in spec:
            print(f"Error: --replace must be OLD=NEW, got {spec!r}", file=sys.stderr)
            sys.exit(2)
        old_s, new_s = spec.split("=", 1)
        old_b, new_b = old_s.encode(), new_s.encode()
        try:
            n = apply_replace(code_slice, old_b, new_b)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if args.verbose or n:
            print(f"replace {old_s!r} -> {new_s!r}: {n} match(es)")
        total += n

    for target in args.mask:
        target_b = target.encode()
        try:
            n = apply_mask(code_slice, target_b, mask_char)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if args.verbose or n:
            masked_preview = (mask_char * min(20, len(target_b))).decode() + (
                "..." if len(target_b) > 20 else ""
            )
            print(f"mask {target!r} -> {masked_preview!r}: {n} match(es)")
        total += n

    data[code_start:code_end] = code_slice

    if total == 0:
        print("Warning: no replacements matched anything", file=sys.stderr)

    rh = rehash(data)
    with open(args.output, "wb") as f:
        f.write(data)

    print(f"\nTotal replacements: {total}")
    print(f"New DHTB hash:      {rh['new_hash']}")
    print(f"Output:             {args.output}")


if __name__ == "__main__":
    main()
