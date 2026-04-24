# 000 - stock baseline

**Status:** completed 2026-04-23
**Device:** RG Vita (UMS512 / T618)
**Config:** stock, no DTB modifications

## Purpose

Reference thermal and throttling baseline for the CPU+GPU torture test at stock max OPPs. All subsequent OC/UV experiments are compared against this.

## Setup

- CPU LITTLE: `scaling_fix_freq=2002000`, userspace governor (cores 0-5)
- CPU BIG: `scaling_fix_freq=2002000`, userspace governor (cores 6-7)
- GPU: performance governor, min=max=850 MHz
- DDR: scene-frequency userspace 1866 MHz
- Load: 8 pinned sha256sum loops + GLES 3.1 fragment-shader stressor at 1280x720

## DTB modifications

None.

## Result summary

- CPU held 2002 MHz both clusters, no throttling
- GPU throttled from 850 MHz -> 384 MHz at t=34 s, stayed at 384 MHz for ~71% of the test
- SoC peak 102.1 C, BIG cluster peak 100.6 C
- GPU FPS fell from 16.7 to 7.5 (matching freq ratio 384/850)

See `REPORT.md` for full stats, `raw/` for telemetry CSV and iteration counts.
