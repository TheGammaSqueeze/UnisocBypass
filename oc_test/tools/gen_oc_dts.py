#!/usr/bin/env python3
"""Generate DTS with CPU UV on lower OPPs + OC (freq + voltage override) on top OPP.

Usage:
    gen_oc_dts.py <cpu_uv_mV> <top_mhz> <top_mv> <out.dts>

Example: gen_oc_dts.py 37.5 2100 1075 modified.dts
    - Applies -37.5 mV UV to OPPs 1..N-1
    - Replaces top OPP (was 2002 MHz @ 1050 mV) with 2100 MHz @ 1075 mV

No trip point changes. Use gen_uv_trip_dts.py if you want those.
"""
import sys
from pathlib import Path

def mv2hex(mv): return f'0x{int(round(mv*1000)):x}'

if len(sys.argv) != 5:
    print("usage: gen_oc_dts.py <cpu_uv_mV> <top_mhz> <top_mv> <out.dts>", file=sys.stderr)
    sys.exit(2)
cpu_uv = float(sys.argv[1])
top_mhz = int(sys.argv[2])
top_mv = float(sys.argv[3])
out = Path(sys.argv[4])

src = Path('/tmp/editor.dts')
dts = src.read_text()

lit_stock = [(0x96000, 756.25), (0xbb800, 756.25), (0xeadd0, 756.25), (0x1174c0, 756.25),
             (0x12c000, 787.5), (0x169d10, 875.0), (0x177000, 890.625),
             (0x1a2f20, 953.125), (0x1bc560, 990.625), (0x1e8c50, 1050.0)]
big_stock = [(0x12c000, 750.0), (0x169d10, 850.0), (0x177000, 870.0),
             (0x1a94b0, 950.0), (0x1c9080, 1000.0), (0x1e8c50, 1050.0)]

def to_dt(pairs, uv, top_mhz_override, top_mv_override):
    parts = []
    for i, (f, v) in enumerate(pairs):
        is_last = (i == len(pairs) - 1)
        fout = top_mhz_override * 1000 if is_last else f
        vout = top_mv_override if is_last else (v - uv)
        parts.append(f'0x{fout:x}')
        parts.append(mv2hex(vout))
    return '<' + ' '.join(parts) + '>'

lit_old = to_dt(lit_stock, 0, 2002, 1050.0)
lit_new = to_dt(lit_stock, cpu_uv, top_mhz, top_mv)
n = dts.count(lit_old)
assert n > 0, 'LITTLE OPP pattern not found'
dts = dts.replace(lit_old, lit_new)

big_old = to_dt(big_stock, 0, 2002, 1050.0)
big_new = to_dt(big_stock, cpu_uv, top_mhz, top_mv)
n = dts.count(big_old)
assert n > 0, 'BIG OPP pattern not found'
dts = dts.replace(big_old, big_new)

out.write_text(dts)
print(f'wrote {out}')
print(f'  Lower OPPs: UV -{cpu_uv} mV')
print(f'  Top OPP: {top_mhz} MHz @ {top_mv} mV (was 2002 @ 1050)')
