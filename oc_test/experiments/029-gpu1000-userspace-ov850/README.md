# 029 - GPU OC 1000 MHz with userspace voltage override (850 mV)

## Purpose

If exp 028 (950 MHz @ 850 mV) is stable, push to 1000 MHz at the same
rail voltage. Same userspace override via
`tools/run_iteration_gpu_ov.sh GPU_OV_MV=850`.

If 1000 MHz is unstable at 850 mV, we have found the upper GPU ceiling
reachable via userspace bypass. Next steps (if attempted) would be:
- push to 875 mV (next 3.125 mV step would be 853-ish, next 25 mV step 875)
- or accept the 950 MHz ceiling and iterate CPU instead

## DT change from baseline

- CPU: inherits exp 025 (UV -37.5 + OC 2100)
- GPU top OPP: 850 -> 1000 MHz (0xcf850 -> 0xf4240 kHz)

## Runtime
Same voltage-override wrapper as exp 028.
