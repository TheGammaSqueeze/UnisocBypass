#!/usr/bin/env python3
"""Exp 024: try mali-supply only (no shadercores-supply).

Exp 023 used both mali-supply and shadercores-supply both pointing to DCDC_GPU.
Both mode showed rail stuck at 700 mV, worse than 800 mV baseline. Hypothesis:
two consumer regulators on the same physical rail interfere.

Exp 024 keeps only mali-supply. num_regulators becomes 1. Mali will make ONE
regulator_set_voltage call per OPP transition.
"""
import subprocess, pathlib
here = pathlib.Path(__file__).parent
base = pathlib.Path('/tmp/editor.dts').read_text()

# Apply 900 MHz @ 850 mV OC
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
gpu_ops_new = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xdbba0 0xcf850>'
assert base.count(gpu_ops_old) == 1
base = base.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xdbba0 0xcf850 0x8 0x01>'
assert base.count(gpu_lst_old) == 1
base = base.replace(gpu_lst_old, gpu_lst_new)

# Inject only mali-supply
needle = 'gpu-supply = <0x0a>;'
assert base.count(needle) == 1
base = base.replace(needle, 'gpu-supply = <0x0a>;\n\t\t\t\tmali-supply = <0x0a>;')

out = here / 'modified.dts'
out.write_text(base)
print(f'wrote {out}')
print('  GPU top OPP: 900 MHz @ 850 mV')
print('  Added mali-supply = phandle 0x0a (no shadercores-supply)')
