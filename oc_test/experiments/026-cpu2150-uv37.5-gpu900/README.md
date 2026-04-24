# 026 - CPU 2150 MHz (step up from baseline exp 025)

## Purpose

Exp 025 (CPU 2100 MHz) ran stable in all 3 modes at stock 1050 mV voltage.
CPU overvolt above 1050 mV is known not to apply (exp 019 with 1075 mV
request landed at 1009 mV). So extra MHz has to come from frequency scaling
alone at the ceiling voltage.

Step +50 MHz from baseline: 2100 -> 2150 MHz.

## DT changes vs baseline exp 025

Only the CPU top OPP freq is changed. UV and GPU OC unchanged:
- CPU LITTLE top OPP: 2100 MHz -> 2150 MHz
- CPU BIG top OPP: 2100 MHz -> 2150 MHz

## Expected

If 2150 MHz is stable in cpu and both modes, exp 027 pushes to 2200. If
it crashes or throttles heavily, we've found the per-chip freq ceiling at
stock 1050 mV. User has authorised aggressive pushes.
