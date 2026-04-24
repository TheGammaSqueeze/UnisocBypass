#!/usr/bin/env python3
"""Generate a modified.dts applying uniform -uv_cpu_mV / -uv_gpu_mV offsets.

Usage:
    gen_uv_dts.py <cpu_uv_mV> <gpu_uv_mV> <output.dts>

Rules:
- CPU voltages (LITTLE + BIG T618-tt tables + the generic operating-points
  that mirrors T618-tt) all reduced by cpu_uv_mV. Frequencies untouched.
- GPU voltages (operating-points and sprd,dvfs-lists, 5 OPPs) reduced by
  gpu_uv_mV. hw_index / flag / freqs untouched.
- The -tt-65 high-temp variants are not touched (they have different voltage
  values that we leave alone; the active path on this device is -tt).

Asserts on pattern uniqueness so any upstream DTS change breaks loudly.
"""
import sys
from pathlib import Path

def mv2hex(mv):
    uv = int(round(mv * 1000))
    return f'0x{uv:x}'

if len(sys.argv) != 4:
    print("usage: gen_uv_dts.py <cpu_uv_mV> <gpu_uv_mV> <out.dts>", file=sys.stderr)
    sys.exit(2)

cpu_uv = float(sys.argv[1])
gpu_uv = float(sys.argv[2])
out = Path(sys.argv[3])

src = Path('/tmp/editor.dts')
dts = src.read_text()

# --- GPU ---
gpu_stock_mv = {700: ['0xaae60','0x5dc00'], 750: ['0xb71b0','0x7d000'], 800: ['0xc3500','0xcf850']}
# freq , volt pairs in operating-points
# operating-points = <0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
gpu_ops_new = f'<0x5dc00 {mv2hex(700-gpu_uv)} 0x7d000 {mv2hex(750-gpu_uv)} 0x96000 {mv2hex(750-gpu_uv)} 0xbb800 {mv2hex(800-gpu_uv)} 0xcf850 {mv2hex(800-gpu_uv)}>'
assert dts.count(gpu_ops_old) == 1, f'GPU ops found {dts.count(gpu_ops_old)} times'
dts = dts.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = (f'<0x5dc00 {mv2hex(700-gpu_uv)} 0x04 0x01 0x7d000 {mv2hex(750-gpu_uv)} 0x05 0x01 '
               f'0x96000 {mv2hex(750-gpu_uv)} 0x06 0x01 0xbb800 {mv2hex(800-gpu_uv)} 0x07 0x01 '
               f'0xcf850 {mv2hex(800-gpu_uv)} 0x08 0x01>')
assert dts.count(gpu_lst_old) == 1
dts = dts.replace(gpu_lst_old, gpu_lst_new)

# --- CPU LITTLE (T618-tt) ---
lit_stock = [
    (0x96000, 756.25), (0xbb800, 756.25), (0xeadd0, 756.25), (0x1174c0, 756.25),
    (0x12c000, 787.5), (0x169d10, 875.0), (0x177000, 890.625),
    (0x1a2f20, 953.125), (0x1bc560, 990.625), (0x1e8c50, 1050.0),
]
def pairs_to_dt(pairs, uv):
    parts = []
    for f, v in pairs:
        parts.append(f'0x{f:x}')
        parts.append(mv2hex(v - uv))
    return '<' + ' '.join(parts) + '>'

lit_old = pairs_to_dt(lit_stock, 0)
lit_new = pairs_to_dt(lit_stock, cpu_uv)
n = dts.count(lit_old)
assert n > 0, f'LITTLE pattern not found (0 occurrences)'
dts = dts.replace(lit_old, lit_new)

# --- CPU BIG (T618-tt) ---
big_stock = [
    (0x12c000, 750.0), (0x169d10, 850.0), (0x177000, 870.0),
    (0x1a94b0, 950.0), (0x1c9080, 1000.0), (0x1e8c50, 1050.0),
]
big_old = pairs_to_dt(big_stock, 0)
big_new = pairs_to_dt(big_stock, cpu_uv)
n = dts.count(big_old)
assert n > 0, f'BIG pattern not found'
dts = dts.replace(big_old, big_new)

out.write_text(dts)
print(f'wrote {out}: CPU UV -{cpu_uv} mV, GPU UV -{gpu_uv} mV')
print(f'  LITTLE replacements: {n}, BIG replacements: {n}')
