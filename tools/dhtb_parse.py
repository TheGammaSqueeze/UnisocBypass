#!/usr/bin/env python3
"""
Parse and display a Unisoc DHTB + SIMGHDR signed image.

Usage:
    python3 dhtb_parse.py <image.img>

Displays all header fields, hash values, key moduli, and validity checks.
"""

import argparse
import hashlib
import struct
import sys


SIMGHDR_MAGIC = b"SIMGHDR\x00"
DHTB_MAGIC = b"DHTB"


def parse_dhtb_header(data):
    """Parse a 0x200-byte DHTB header at offset 0."""
    if len(data) < 0x200:
        return None

    magic = data[0:4]
    if magic != DHTB_MAGIC:
        return None

    hdr = {
        "magic": magic,
        "version": struct.unpack("<I", data[4:8])[0],
        "data_hash": data[8:0x28],
        "marker1": data[0x28:0x2C],
        "marker2": data[0x2C:0x30],
        "data_size": struct.unpack("<Q", data[0x30:0x38])[0],
        "field_38": struct.unpack("<Q", data[0x38:0x40])[0],
        "field_40": struct.unpack("<Q", data[0x40:0x48])[0],
        "field_48": struct.unpack("<Q", data[0x48:0x50])[0],
    }
    return hdr


def parse_simghdr(data, offset):
    """Parse a 1172-byte SIMGHDR at offset. Returns None if not present."""
    if offset + 1172 > len(data):
        return None

    magic = data[offset:offset+8]
    if magic != SIMGHDR_MAGIC:
        return None

    return {
        "magic": magic,
        "data_size":       struct.unpack("<Q", data[offset+0x10:offset+0x18])[0],
        "header_size":     struct.unpack("<Q", data[offset+0x18:offset+0x20])[0],
        "sig_struct_size": struct.unpack("<Q", data[offset+0x20:offset+0x28])[0],
        "total_offset":    struct.unpack("<Q", data[offset+0x28:offset+0x30])[0],
        "flags":           data[offset+0x60:offset+0x68],
        "exponent":        struct.unpack(">I", data[offset+0x68:offset+0x6C])[0],
        "modulus":         data[offset+0x6C:offset+0x16C],
        "data_hash_copy":  data[offset+0x16C:offset+0x18C],
        "second_hash":     data[offset+0x18C:offset+0x1AC],
        "end_flags":       data[offset+0x1AC:offset+0x1B4],
        "signature":       data[offset+0x1B4:offset+0x2B4],
    }


def fmt_hex(b, max_len=32):
    h = b.hex()
    if len(h) > max_len * 2:
        return h[:max_len*2] + "..."
    return h


def dump_image(path):
    with open(path, "rb") as f:
        data = f.read()

    print(f"=== {path} ===")
    print(f"File size: {len(data)} bytes (0x{len(data):x})")
    print()

    dhtb = parse_dhtb_header(data)
    if not dhtb:
        print("Not a DHTB-signed image (magic not found).")
        return 1

    print("DHTB Header:")
    print(f"  magic:     {dhtb['magic']}")
    print(f"  version:   {dhtb['version']}")
    print(f"  data_size: 0x{dhtb['data_size']:x} ({dhtb['data_size']} bytes)")
    print(f"  data_hash: {dhtb['data_hash'].hex()}")
    print()

    # Verify DHTB hash
    data_section = data[0x200:0x200 + dhtb['data_size']]
    computed = hashlib.sha256(data_section).digest()
    match = computed == dhtb['data_hash']
    marker = "OK" if match else "MISMATCH"
    print(f"DHTB hash integrity: [{marker}]")
    if not match:
        print(f"  computed: {computed.hex()}")
    print()

    # Parse SIMGHDR
    simghdr_off = 0x200 + dhtb['data_size']
    simghdr = parse_simghdr(data, simghdr_off)
    if not simghdr:
        print(f"No SIMGHDR at 0x{simghdr_off:x} (may be truncated or unsigned).")
        return 0

    print(f"SIMGHDR (at 0x{simghdr_off:x}):")
    print(f"  magic:           {simghdr['magic']}")
    print(f"  data_size:       0x{simghdr['data_size']:x}")
    print(f"  header_size:     0x{simghdr['header_size']:x}")
    print(f"  sig_struct_size: 0x{simghdr['sig_struct_size']:x}")
    print(f"  total_offset:    0x{simghdr['total_offset']:x}")
    print(f"  flags:           {simghdr['flags'].hex()}")
    print(f"  RSA exponent:    {simghdr['exponent']} (0x{simghdr['exponent']:x})")
    print(f"  RSA modulus:     {fmt_hex(simghdr['modulus'], 16)}")
    print(f"  data_hash_copy:  {simghdr['data_hash_copy'].hex()}")
    print(f"  second_hash:     {simghdr['second_hash'].hex()}")
    print(f"  signature:       {fmt_hex(simghdr['signature'], 16)}")
    print()

    # Check SIMGHDR data hash matches DHTB
    if simghdr['data_hash_copy'] == dhtb['data_hash']:
        print("SIMGHDR data hash matches DHTB hash: [OK]")
    else:
        print("SIMGHDR data hash mismatch: [WARNING]")
        print(f"  DHTB:    {dhtb['data_hash'].hex()}")
        print(f"  SIMGHDR: {simghdr['data_hash_copy'].hex()}")
    print()

    # Check if signature is zeroed (unsigned/debug)
    if all(b == 0 for b in simghdr['signature']):
        print("RSA signature is all zeros (unsigned / debug image)")
    else:
        print("RSA signature present (image is formally signed)")
    print()

    # Identify key by modulus prefix
    mod_prefix = simghdr['modulus'][:8].hex()
    key_a_prefix = "d0a0300adc72c62f"
    key_b_prefix = "ad7e67e09f57f0a3"
    if mod_prefix.startswith(key_a_prefix[:8]):
        print("Signing key: Key A (SPL / FDL1 group)")
    elif mod_prefix.startswith(key_b_prefix[:8]):
        print("Signing key: Key B (SML / TrustOS / UBoot / FDL2 group)")
    else:
        print(f"Signing key: Unknown (modulus prefix {mod_prefix})")

    return 0


def main():
    ap = argparse.ArgumentParser(description="Parse a Unisoc DHTB + SIMGHDR image")
    ap.add_argument("image", help="Path to the DHTB image file")
    args = ap.parse_args()
    sys.exit(dump_image(args.image))


if __name__ == "__main__":
    main()
