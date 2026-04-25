# 028 - GPU OC 950 MHz with userspace voltage override (850 mV)

## Purpose

Break the 800 mV GPU rail ceiling by writing 850 mV to
`/sys/kernel/debug/DCDC_GPU/voltage` (calls `set_voltage_sel_regmap`
directly, verified in exp 022-024 to succeed and hold across Mali OPP
transitions).

If 950 MHz runs stably at 850 mV, we can push to 1000 MHz next (exp 029).

## Components

- CPU UV -37.5 + CPU OC 2100 (inherited from baseline exp 025)
- GPU top OPP: 850 -> 950 MHz at stock 800 mV DT target
  (the DT voltage is ignored; override happens via debugfs)
- Runtime: `tools/run_iteration_gpu_ov.sh` with `GPU_OV_MV=850`. Writes
  850 mV via debugfs once at boot, again before each bench mode, and
  re-primes every 15 s during stress (defensive in case Mali resets).

## Expected

- gpu mode: 950 MHz @ 850 mV rail, >17% FPS vs stock (950/850 > 900/800 energy ratio)
- cpu mode: unchanged vs exp 025
- both mode: slightly higher GPU throttle floor

If the rail drops back to 800 mV despite the override, the 15 s re-prime
should catch it and the sample csv will still show the transition. Any
hang / crash indicates 950 MHz at 850 mV is unstable on this chip.
