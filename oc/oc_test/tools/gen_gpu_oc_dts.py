#!/usr/bin/env python3
"""Generate DTS with GPU top OPP frequency overclocked.

Usage:
    gen_gpu_oc_dts.py <top_gpu_mhz> [--hw-index N] [--volt-mv V] [--cpu-uv-mv X] <out.dts>

Default: keeps stock 800 mV and hw_index 8 for the top OPP, just raises freq.
Optional:
    --hw-index   force a specific hw_index for the top OPP (try 9 for next voltage slot)
    --volt-mv    force a specific voltage for the top OPP (may or may not apply to hardware)
    --cpu-uv-mv  keep CPU UV (default 0, no CPU changes)

Only the top GPU OPP is changed. operating-points and sprd,dvfs-lists get a
new freq and optionally new volt/hw_index for the 5th entry. sprd,dvfs-range-max
stays at 0x04.
"""
import argparse
from pathlib import Path

def mv2hex(mv): return f'0x{int(round(mv*1000)):x}'

ap = argparse.ArgumentParser()
ap.add_argument('top_gpu_mhz', type=int)
ap.add_argument('--hw-index', type=int, default=8)
ap.add_argument('--volt-mv', type=float, default=800.0)
ap.add_argument('--cpu-uv-mv', type=float, default=0.0)
ap.add_argument('out')
args = ap.parse_args()

src = Path('/tmp/editor.dts')
dts = src.read_text()

# Build new top-OPP hex values
top_freq_hex = f'0x{args.top_gpu_mhz * 1000:x}'
top_volt_hex = mv2hex(args.volt_mv)
hw_hex = f'0x{args.hw_index:x}'

# Stock GPU operating-points:
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
# Keep OPPs 0..3 identical, change OPP 4 (last) freq and voltage
gpu_ops_new = f'<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 {top_freq_hex} {top_volt_hex}>'
assert dts.count(gpu_ops_old) == 1, 'GPU ops not found'
dts = dts.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = (f'<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 '
               f'0xbb800 0xc3500 0x07 0x01 {top_freq_hex} {top_volt_hex} {hw_hex} 0x01>')
assert dts.count(gpu_lst_old) == 1
dts = dts.replace(gpu_lst_old, gpu_lst_new)

# Optional CPU UV
if args.cpu_uv_mv > 0:
    lit_stock = [(0x96000, 756.25), (0xbb800, 756.25), (0xeadd0, 756.25), (0x1174c0, 756.25),
                 (0x12c000, 787.5), (0x169d10, 875.0), (0x177000, 890.625),
                 (0x1a2f20, 953.125), (0x1bc560, 990.625), (0x1e8c50, 1050.0)]
    big_stock = [(0x12c000, 750.0), (0x169d10, 850.0), (0x177000, 870.0),
                 (0x1a94b0, 950.0), (0x1c9080, 1000.0), (0x1e8c50, 1050.0)]
    def to_dt(pairs, uv):
        parts = []
        for f, v in pairs:
            parts.append(f'0x{f:x}')
            parts.append(mv2hex(v - uv))
        return '<' + ' '.join(parts) + '>'
    lit_old = to_dt(lit_stock, 0); lit_new = to_dt(lit_stock, args.cpu_uv_mv)
    big_old = to_dt(big_stock, 0); big_new = to_dt(big_stock, args.cpu_uv_mv)
    assert dts.count(lit_old) > 0; dts = dts.replace(lit_old, lit_new)
    assert dts.count(big_old) > 0; dts = dts.replace(big_old, big_new)

Path(args.out).write_text(dts)
print(f'wrote {args.out}')
print(f'  GPU top OPP: {args.top_gpu_mhz} MHz, volt {args.volt_mv} mV, hw_index {args.hw_index}')
if args.cpu_uv_mv > 0:
    print(f'  CPU UV: -{args.cpu_uv_mv} mV')
