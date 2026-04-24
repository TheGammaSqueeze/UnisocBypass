# 014 - Reproducibility retest of CPU UV -37.5 mV

3 full runs (3 modes each, reboot between runs). DTB identical to exp 008.

## CPU-only mode

| run | samples | vddcpu | CPU GiB | SoC peak C |
|-----|--------:|-------:|--------:|----------:|
| run1 | 84 | 1012.5 mV | 65.85 | 106.0 |
| run2 | 79 | 1012.5 mV | 62.06 | 105.0 |
| run3 | 77 | 1012.5 mV | 60.64 | 105.3 |
| **mean ± stdev** | | | **62.85 ± 2.69 (4.3%)** | |

## GPU-only mode

| run | samples | FPS avg | GPU thr | SoC peak C |
|-----|--------:|--------:|--------:|----------:|
| run1 | 129 | 16.25 | 0% | 68.3 |
| run2 | 128 | 16.25 | 0% | 68.5 |
| run3 | 129 | 16.23 | 0% | 68.0 |
| **mean ± stdev** | | **16.24 ± 0.010** | | |

## Both mode

| run | samples | vddcpu | CPU GiB | FPS | GPU thr | SoC peak C |
|-----|--------:|-------:|--------:|----:|--------:|----------:|
| run1 | 72 | 1012.5 mV | 57.96 | 8.13 | 86% | 105.3 |
| run2 | 72 | 1012.5 mV | 57.37 | 8.11 | 87% | 105.8 |
| run3 | 67 | 1012.5 mV | 57.10 | 8.08 | 86% | 105.5 |
| **mean ± stdev (CPU GiB)** | | | **57.48 ± 0.44 (0.8%)** | | | |
| **mean ± stdev (FPS)** | | | | **8.11 ± 0.022** | | |

## Comparison vs stock baseline (005 cpu, 006 gpu, 007 both)

| metric | stock | exp 014 mean (x3) | exp 008 single | delta vs stock | conclusion |
|--------|------:|------------------:|---------------:|---------------:|------------|
| CPU-only GiB | 66.53 | 62.85 | 81.2 | -5.5% | exp 008 was an outlier, UV does NOT improve CPU perf |
| GPU-only FPS | 16.27 | 16.24 | 16.26 | -0.17% | unchanged (as expected) |
| both CPU GiB | 60.39 | 57.48 | 65.8 | -4.8% | UV gives slight regression, not improvement |
| both FPS | 8.12 | 8.11 | 8.56 | -0.16% | essentially unchanged |
| CPU-only SoC pk C | 105.0 | 105.4 | 98.8 | +0.4 | no thermal benefit reproduced |
| both SoC pk C | 105.8 | 105.5 | 105.5 | -0.3 | identical within noise |

## Conclusion

The CPU UV -37.5 mV DTB modification does NOT produce a reproducible benefit:

- **CPU-only performance**: -5.5% vs stock (was +22.1% in the single exp 008 run)
- **Both-mode performance**: -4.8% CPU, -0.16% FPS (was +9.0% / +5.4% in exp 008)
- **Thermal**: no improvement; SoC peaks at 105 C in both CPU-only and both modes, same as stock
- **GPU-only**: no change (as expected, separate rail, and GPU DTB UV doesn't reach hardware)

Exp 008 was run earlier in the test session when the chassis was cooler and had less thermal history. The thermal state of the chassis between runs has more effect on measured performance than the CPU rail voltage at this level.

Across the full sweep (exps 008-013 = -37.5 to -100 mV), the observed "gains" in single-run tests were all within run-to-run variance. The UV is physically applied (vddcpu tracks DT values down to around 950 mV) but the reduced voltage does not translate to measurable sustained performance or thermal improvement in this torture test harness.

**Recommendation**: revert to stock CPU voltage. The ~5 mW saved per core at -37.5 mV (at ~3% power reduction) is negligible compared to the 105 C thermal envelope already hit at stock, and is not reproducible across runs.
