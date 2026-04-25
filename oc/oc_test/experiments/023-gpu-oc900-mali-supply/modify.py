#!/usr/bin/env python3
"""Exp 023: add `mali-supply = <0x0a>` to GPU DT so Mali acquires DCDC_GPU.

Root cause identified in exp 022: Mali's power_control_init calls
regulator_get_optional(dev, "mali") and ..."shadercores"). Neither has a
corresponding *-supply in the GPU DT node (only gpu-supply). Mali ends up
with num_regulators=0, so its regulator_set_voltage calls are no-ops and
vddgpu stays at whatever SPL/uboot programmed (800 mV by default).

Exp 023 adds `mali-supply = <0x0a>` (same phandle as gpu-supply = DCDC_GPU).
Keeps operating-points top OPP at 850 mV. Expected: Mali acquires DCDC_GPU
as "mali" regulator, regulator_set_voltage(850000) writes to SC2730
DCDC_GPU via SPI, rail shows 850 mV under stress.
"""
import subprocess, pathlib, re
here = pathlib.Path(__file__).parent
# Start from exp 021 dts which already has 900 MHz @ 850 mV
base = pathlib.Path('/tmp/editor.dts').read_text()

# First apply 900 MHz @ 850 mV to match exp 021
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
gpu_ops_new = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xdbba0 0xcf850>'
assert base.count(gpu_ops_old) == 1
base = base.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xdbba0 0xcf850 0x8 0x01>'
assert base.count(gpu_lst_old) == 1
base = base.replace(gpu_lst_old, gpu_lst_new)

# Inject mali-supply and shadercores-supply right after gpu-supply (both point to DCDC_GPU = phandle 0x0a)
needle = 'gpu-supply = <0x0a>;'
assert base.count(needle) == 1
injected = ('gpu-supply = <0x0a>;\n\t\t\t\t'
            'mali-supply = <0x0a>;\n\t\t\t\t'
            'shadercores-supply = <0x0a>;')
base = base.replace(needle, injected)

out = here / 'modified.dts'
out.write_text(base)
print(f'wrote {out}')
print('  GPU top OPP: 900 MHz @ 850 mV (via operating-points)')
print('  Added mali-supply + shadercores-supply = phandle 0x0a (DCDC_GPU)')
