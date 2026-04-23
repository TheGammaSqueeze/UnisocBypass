#!/usr/bin/env python3
"""
Verify the integrity of a Unisoc DHTB image.

Checks:
- DHTB magic is present
- DHTB SHA256 hash matches the data payload
- SIMGHDR data hash matches DHTB hash (if SIMGHDR is present)

Exit codes:
    0 - image is valid (hashes match)
    1 - image is invalid (hash mismatch, missing magic, truncated, etc.)

Usage:
    python3 verify_image.py <image.img>
"""

import argparse
import hashlib
import struct
import sys


def verify(path: str) -> bool:
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 0x200:
        print(f"FAIL: {path}: file too small ({len(data)} bytes)")
        return False

    if data[0:4] != b"DHTB":
        print(f"FAIL: {path}: missing DHTB magic (got {data[0:4]})")
        return False

    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    if 0x200 + data_size > len(data):
        print(f"FAIL: {path}: truncated (data_size=0x{data_size:x}, file=0x{len(data):x})")
        return False

    stored = data[8:0x28]
    computed = hashlib.sha256(data[0x200:0x200 + data_size]).digest()
    if stored != computed:
        print(f"FAIL: {path}: DHTB hash mismatch")
        print(f"  stored:   {stored.hex()}")
        print(f"  computed: {computed.hex()}")
        return False

    simghdr_off = 0x200 + data_size
    if simghdr_off + 1172 <= len(data) and data[simghdr_off:simghdr_off+8] == b"SIMGHDR\x00":
        simghdr_hash = data[simghdr_off + 0x16C: simghdr_off + 0x18C]
        if simghdr_hash != stored:
            print(f"WARN: {path}: SIMGHDR data hash does not match DHTB hash")
            print(f"  DHTB:    {stored.hex()}")
            print(f"  SIMGHDR: {simghdr_hash.hex()}")
            # Still consider image valid (BootROM only checks DHTB)

    print(f"OK:   {path}: DHTB hash valid ({stored.hex()[:16]}...)")
    return True


def main():
    ap = argparse.ArgumentParser(description="Verify Unisoc DHTB image integrity")
    ap.add_argument("images", nargs="+", help="DHTB image files to verify")
    args = ap.parse_args()

    any_fail = False
    for img in args.images:
        try:
            ok = verify(img)
        except FileNotFoundError:
            print(f"FAIL: {img}: file not found")
            ok = False
        if not ok:
            any_fail = True

    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
