# 008 - CPU UV -37.5 mV + GPU UV -25 mV (all three modes)

**Status:** running 2026-04-24
**Config:** CPU LITTLE/BIG UV -37.5 mV across all OPPs, GPU UV -25 mV across all OPPs

## Hypothesis

Combining modest CPU + GPU UV should reduce SoC power with no performance loss. Target voltages:

- CPU LITTLE 2002 MHz: 1050 mV -> 1012.5 mV
- CPU BIG 2002 MHz: 1050 mV -> 1012.5 mV
- GPU 850 MHz: 800 mV -> 775 mV (DT change; may not reach hardware)

Performance metrics to watch:
- CPU throughput (KiB/s hashed, from sha256sum loops)
- GPU FPS (shader stressor)
- Stability: boot + survive 180 s stress without crash

Threshold for STOP: >10% drop in CPU GiB or GPU FPS versus stock baseline, or boot failure.
