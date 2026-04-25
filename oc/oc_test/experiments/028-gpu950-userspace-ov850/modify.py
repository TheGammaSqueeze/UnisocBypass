#!/usr/bin/env python3
"""Exp 028: push GPU to 950 MHz with userspace voltage override to 850 mV.

DT hits the 800 mV voltage ceiling (exp 021-024 proved this). We instead
use the known-working bypass: write 850 mV to
`/sys/kernel/debug/DCDC_GPU/voltage` after each boot. The debugfs write
calls `set_voltage_sel_regmap` directly and survives Mali OPP transitions
(verified manually in exp 022-024).

This modify.py only edits the DTS. The bench_test.sh hook that forces
850 mV during the gpu mode stress is planted separately via the
oc_test/tools/force_gpu_850.sh helper (pushed to /data/local/tmp by the
iteration script).

DT changes:
- CPU UV -37.5 + OC 2100 (same as exp 025 baseline, not touched)
- GPU top OPP: 850 -> 950 MHz (0xcf850 -> 0xe7ef0 kHz)
"""
import pathlib
here = pathlib.Path(__file__).parent
src = pathlib.Path('/tmp/editor.dts').read_text()

def mv2hex(mv):
    return f'0x{int(round(mv*1000)):x}'

# CPU: UV -37.5 + OC 2100 (matches exp 025)
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
lit_new = to_dt(lit_stock, 37.5, 2100, 1050.0)
assert src.count(lit_old) > 0
src = src.replace(lit_old, lit_new)

big_old = to_dt(big_stock, 0, 2002, 1050.0)
big_new = to_dt(big_stock, 37.5, 2100, 1050.0)
assert src.count(big_old) > 0
src = src.replace(big_old, big_new)

# GPU: 950 MHz top OPP. DT voltage stays at 800 mV target (irrelevant, clamped);
# actual rail will be forced to 850 mV via debugfs at bench time.
# 950 MHz kHz = 0xE7EF0
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
gpu_ops_new = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xe7ef0 0xc3500>'
assert src.count(gpu_ops_old) == 1
src = src.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xe7ef0 0xc3500 0x08 0x01>'
assert src.count(gpu_lst_old) == 1
src = src.replace(gpu_lst_old, gpu_lst_new)

(here / 'modified.dts').write_text(src)
print(f'wrote {here / "modified.dts"}')
print('  CPU: UV -37.5 + OC 2100 (baseline exp 025)')
print('  GPU: top OPP 950 MHz. Userspace voltage override to 850 mV via debugfs.')
