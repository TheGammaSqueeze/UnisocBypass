#!/usr/bin/env python3
"""Experiment 001: -12.5 mV UV on top GPU OPP only.

Reads the stock DTS at /tmp/editor.dts (produced by dtc from the stock
vendor_boot's embedded multi-DTB) and writes the modified DTS next to this
file so the change is reproducible.
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC_DTS = Path('/tmp/editor.dts')      # decompiled from stock editor dtb
OUT_DTS = HERE / 'modified.dts'

assert SRC_DTS.exists(), f"missing {SRC_DTS}; run: dtc -I dtb -O dts -o /tmp/editor.dts <editor>/build/unzip_boot/dtb (extract inner DTB first)"

dts = SRC_DTS.read_text()

# In the gpu@60000000 node: only the top voltage (0xc3500 = 800 mV) on the
# 850 MHz OPP changes. Anchor on surrounding tokens for uniqueness.
ops_old = '0xbb800 0xc3500 0xcf850 0xc3500>'
ops_new = '0xbb800 0xc3500 0xcf850 0xc042c>'
assert dts.count(ops_old) == 1, 'ops pattern not unique'

lst_old = '0xbb800 0xc3500 0x07 0x01 0xcf850 0xc3500 0x08 0x01'
lst_new = '0xbb800 0xc3500 0x07 0x01 0xcf850 0xc042c 0x08 0x01'
assert dts.count(lst_old) == 1

dts = dts.replace(ops_old, ops_new)
dts = dts.replace(lst_old, lst_new)

OUT_DTS.write_text(dts)
print(f'wrote {OUT_DTS}')
print('Next: tools/flash_dts.sh ' + str(OUT_DTS) + ' ' + str(HERE))
