#!/usr/bin/env python3
"""Experiment 004: GPU UV -37.5 mV + CPU UV -25 mV (LITTLE and BIG).

Goal: reduce BOTH rails' power so the CPU no longer saturates the thermal
envelope during torture tests. GPU -37.5 is halfway between known-safe -25
(exp 002) and known-brick -50 (recovered). CPU -25 matches the validated
GPU safe margin.

DTB edits are voltage-only; all frequencies and all cluster mapping
tables remain untouched, so OPP indexing is unchanged.
"""
from pathlib import Path

HERE = Path(__file__).parent
SRC_DTS = Path('/tmp/editor.dts')
OUT_DTS = HERE / 'modified.dts'
assert SRC_DTS.exists(), f"missing {SRC_DTS}"
dts = SRC_DTS.read_text()

# ---- GPU UV -37.5 mV (5 OPPs) ----
gpu_ops_old = '<0x5dc00 0xaae60 0x7d000 0xb71b0 0x96000 0xb71b0 0xbb800 0xc3500 0xcf850 0xc3500>'
gpu_ops_new = '<0x5dc00 0xa1be4 0x7d000 0xadf34 0x96000 0xadf34 0xbb800 0xba284 0xcf850 0xba284>'
assert dts.count(gpu_ops_old) == 1
dts = dts.replace(gpu_ops_old, gpu_ops_new)

gpu_lst_old = '<0x5dc00 0xaae60 0x04 0x01 0x7d000 0xb71b0 0x05 0x01 0x96000 0xb71b0 0x06 0x01 0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01>'
gpu_lst_new = '<0x5dc00 0xa1be4 0x04 0x01 0x7d000 0xadf34 0x05 0x01 0x96000 0xadf34 0x06 0x01 0xbb800 0xba284 0x07 0x01 0xcf850 0xba284 0x08 0x01>'
assert dts.count(gpu_lst_old) == 1
dts = dts.replace(gpu_lst_old, gpu_lst_new)

# ---- CPU UV -25 mV ----
# LITTLE T618-tt, 10 OPPs. Voltage pairs only, frequencies untouched.
lit_old = '<0x96000 0xb8a1a 0xbb800 0xb8a1a 0xeadd0 0xb8a1a 0x1174c0 0xb8a1a 0x12c000 0xc042c 0x169d10 0xd59f8 0x177000 0xd9701 0x1a2f20 0xe8b25 0x1bc560 0xf1da1 0x1e8c50 0x100590>'
# Map each voltage -25 mV:
#   0xb8a1a (756250) -> 0xb2872 (731250)
#   0xc042c (787500) -> 0xba284 (762500)
#   0xd59f8 (875000) -> 0xcf850 (850000)
#   0xd9701 (890625) -> 0xd3559 (865625)
#   0xe8b25 (953125) -> 0xe297d (928125)
#   0xf1da1 (990625) -> 0xebbf9 (965625)
#   0x100590 (1050000) -> 0xfa3e8 (1025000)
lit_new = '<0x96000 0xb2872 0xbb800 0xb2872 0xeadd0 0xb2872 0x1174c0 0xb2872 0x12c000 0xba284 0x169d10 0xcf850 0x177000 0xd3559 0x1a2f20 0xe297d 0x1bc560 0xebbf9 0x1e8c50 0xfa3e8>'
# operating-points-T618-tt in LITTLE appears twice (once as `operating-points-T618`, once as `-tt`)
# Actually stock DTS has it in multiple places. Count both.
n = dts.count(lit_old)
print(f"LITTLE old pattern count: {n}")
assert n > 0, "LITTLE pattern not found"
dts = dts.replace(lit_old, lit_new)

# BIG T618-tt, 6 OPPs. Same UV -25 mV.
big_old = '<0x12c000 0xb71b0 0x169d10 0xcf850 0x177000 0xd4670 0x1a94b0 0xe7ef0 0x1c9080 0xf4240 0x1e8c50 0x100590>'
#   0xb71b0 (750000) -> 0xb1008 (725000)
#   0xcf850 (850000) -> 0xc96a8 (825000)
#   0xd4670 (870000) -> 0xce4c8 (845000)
#   0xe7ef0 (950000) -> 0xe1d48 (925000)
#   0xf4240 (1000000) -> 0xee098 (975000)
#   0x100590 (1050000) -> 0xfa3e8 (1025000)
big_new = '<0x12c000 0xb1008 0x169d10 0xc96a8 0x177000 0xce4c8 0x1a94b0 0xe1d48 0x1c9080 0xee098 0x1e8c50 0xfa3e8>'
n = dts.count(big_old)
print(f"BIG old pattern count: {n}")
assert n > 0, "BIG pattern not found"
dts = dts.replace(big_old, big_new)

OUT_DTS.write_text(dts)
print(f'wrote {OUT_DTS}')
print('Next: /work/vita/signing/oc_test/tools/flash_dts.sh', OUT_DTS, HERE)
