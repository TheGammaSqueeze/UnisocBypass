#!/usr/bin/env python3
"""Generate DTS with CPU UV + raised thermal trip points + optional CPU OC.

Usage:
    gen_uv_trip_dts.py <cpu_uv_mV> <trip_C> <cpu_max_mhz> <out.dts>

cpu_uv_mV      - CPU under-volt, e.g. 37.5
trip_C         - effective thermal trip in C (raises soc passive trip, cluster max-temp, and soc_crit = trip_C + 10)
cpu_max_mhz    - max CPU freq in MHz; e.g. 2002 keeps stock, 2100 bumps both clusters' top OPP
                 (only replaces EXISTING 2002 MHz OPP; does not add new OPPs)
"""
import sys
from pathlib import Path

def mv2hex(mv): return f'0x{int(round(mv*1000)):x}'
def mhz2hex(mhz): return f'0x{int(round(mhz*1000)):x}'
def c2hex(c): return f'0x{int(round(c*1000)):x}'

if len(sys.argv) != 5:
    print("usage: gen_uv_trip_dts.py <cpu_uv_mV> <trip_C> <cpu_max_mhz> <out.dts>", file=sys.stderr)
    sys.exit(2)
cpu_uv = float(sys.argv[1])
trip_c = float(sys.argv[2])
max_mhz = int(sys.argv[3])
out = Path(sys.argv[4])

src = Path('/tmp/editor.dts')
dts = src.read_text()

# ---- CPU UV ----
lit_stock = [(0x96000, 756.25), (0xbb800, 756.25), (0xeadd0, 756.25), (0x1174c0, 756.25),
             (0x12c000, 787.5), (0x169d10, 875.0), (0x177000, 890.625),
             (0x1a2f20, 953.125), (0x1bc560, 990.625), (0x1e8c50, 1050.0)]
big_stock = [(0x12c000, 750.0), (0x169d10, 850.0), (0x177000, 870.0),
             (0x1a94b0, 950.0), (0x1c9080, 1000.0), (0x1e8c50, 1050.0)]

def pairs_to_dt(pairs, uv, freq_override_last=None):
    parts = []
    for i, (f, v) in enumerate(pairs):
        is_last = (i == len(pairs) - 1)
        fout = freq_override_last if (is_last and freq_override_last is not None) else f
        parts.append(f'0x{fout:x}')
        parts.append(mv2hex(v - uv))
    return '<' + ' '.join(parts) + '>'

# For OC: override the last freq (2002 -> max_mhz)
freq_override = max_mhz * 1000 if max_mhz != 2002 else None  # override only if non-stock

lit_old = pairs_to_dt(lit_stock, 0)
lit_new = pairs_to_dt(lit_stock, cpu_uv, freq_override)
n = dts.count(lit_old)
assert n > 0, 'LITTLE OPP pattern not found in DTS'
dts = dts.replace(lit_old, lit_new)

big_old = pairs_to_dt(big_stock, 0)
big_new = pairs_to_dt(big_stock, cpu_uv, freq_override)
n = dts.count(big_old)
assert n > 0, 'BIG OPP pattern not found in DTS'
dts = dts.replace(big_old, big_new)

# ---- Raise thermal trip points ----
soc_crit_c = trip_c + 10

# stock: soc passive trip@1 = 85 C (0x14c08), soc_crit = 110 C (0x1adb0)
# stock: cluster0 max-temp = 90 C (0x15f90), cluster1 max-temp = 85 C (0x14c08)
# Target: soc passive trip@1 = trip_c, cluster0/1 max-temp = trip_c, soc_crit = trip_c + 10

# soc passive trip@1 uniqueness: `temperature = <0x14c08>` appears in multiple places.
# Anchor it with hysteresis + type
soc_trip1_old = '''trip-point@1 {
					temperature = <0x14c08>;
					hysteresis = <0x3e8>;
					type = "passive";'''
soc_trip1_new = soc_trip1_old.replace('<0x14c08>', f'<{c2hex(trip_c)}>')
assert dts.count(soc_trip1_old) == 1
dts = dts.replace(soc_trip1_old, soc_trip1_new)

# soc_crit
soc_crit_old = '''soc_crit {
					temperature = <0x1adb0>;'''
soc_crit_new = soc_crit_old.replace('<0x1adb0>', f'<{c2hex(soc_crit_c)}>')
assert dts.count(soc_crit_old) == 1
dts = dts.replace(soc_crit_old, soc_crit_new)

# cluster0 max-temp (90 C)
# The pattern "sprd,max-temp = <0x15f90>" is unique to cluster0-cooling
cl0_old = 'sprd,max-temp = <0x15f90>'
cl0_new = f'sprd,max-temp = <{c2hex(trip_c)}>'
assert dts.count(cl0_old) == 1
dts = dts.replace(cl0_old, cl0_new)

# cluster1 max-temp (85 C) - same hex as soc_trip1 but different node context
# Pattern: "sprd,max-temp = <0x14c08>" is unique to cluster1-cooling
cl1_old = 'sprd,max-temp = <0x14c08>'
cl1_new = f'sprd,max-temp = <{c2hex(trip_c)}>'
assert dts.count(cl1_old) == 1
dts = dts.replace(cl1_old, cl1_new)

out.write_text(dts)
print(f'wrote {out}')
print(f'  CPU UV: -{cpu_uv} mV')
print(f'  CPU max: {max_mhz} MHz (was 2002)')
print(f'  Trip: {trip_c} C (was 85)')
print(f'  soc_crit: {soc_crit_c} C (was 110)')
print(f'  cluster0/1 max-temp: {trip_c} C (was 90/85)')
