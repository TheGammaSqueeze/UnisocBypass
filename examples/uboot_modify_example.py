#!/usr/bin/env python3
"""
Example: modify a stock uboot by masking the unlock-status strings with "1"
characters, then re-hash. This reproduces exactly the modification that was
validated booting on a Vita Pro.

Usage:
    python3 uboot_modify_example.py <stock_uboot.img> <output.img>

After producing the modified image, flash it:
    ./scripts/flash_uboot.sh <output.img>
    adb reboot
"""

import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from rehash import rehash  # noqa: E402


STRINGS_TO_MASK = [
    b"WARNNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!!!",
    b"INFO: LOCK FLAG IS : UNLOCK!!!",
]


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <stock_uboot.img> <output.img>")
        sys.exit(2)

    in_path, out_path = sys.argv[1], sys.argv[2]
    with open(in_path, "rb") as f:
        data = bytearray(f.read())

    if data[0:4] != b"DHTB":
        print("Error: input is not a DHTB image", file=sys.stderr)
        sys.exit(1)

    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    code_start, code_end = 0x200, 0x200 + data_size

    total = 0
    for target in STRINGS_TO_MASK:
        replacement = b"1" * len(target)
        start = code_start
        while True:
            idx = data.find(target, start, code_end)
            if idx < 0:
                break
            data[idx:idx + len(target)] = replacement
            total += 1
            start = idx + len(replacement)
            print(f"  replaced {target!r} at 0x{idx:x}")

    if total == 0:
        print("Warning: no strings matched")

    result = rehash(data)

    with open(out_path, "wb") as f:
        f.write(data)

    print(f"\nReplaced {total} string(s)")
    print(f"New DHTB hash: {result['new_hash']}")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
