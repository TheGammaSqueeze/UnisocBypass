# 016 - UV -37.5 mV + trip 115 C + CPU OC 2100 MHz (+5%)

First OC attempt on top of -37.5 mV UV + raised thermal trips.

DT changes:
- CPU LITTLE/BIG top OPP freq: 2002 -> 2100 MHz (2100000 kHz)
- CPU LITTLE/BIG top OPP voltage: 1050 -> 1012.5 mV (keep UV)
- Mid-tier OPPs also UV'd -37.5 mV
- Thermal trip 115 C + soc_crit 125 C + cluster max-temp 115 C

Implementation: REPLACES existing top OPP freq only; does NOT add new OPPs.
This avoids touching the cluster mapping tables which bricked us in prior attempts.

Hypothesis: +5% CPU frequency yields measurable CPU-only throughput gain.
