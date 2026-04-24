# 003 - GPU UV all OPPs -25 mV, GPU-only load

**Status:** completed 2026-04-24
**Device:** RG Vita (UMS512 / T618)

## Hypothesis

The CPU-heavy torture test dominates SoC thermals and masks any GPU UV benefit. If we CAP CPUs to low frequencies (policy0=614.4 MHz, policy6=1228.8 MHz) and only stress the GPU at 850 MHz, the GPU should sustain its peak frequency indefinitely if the -25 mV UV is stable.

## DTB changes

Same as experiment 002 (-25 mV across all 5 GPU OPPs).

## Test harness

`gpu_only_test.sh` rather than `torture_test.sh`. No CPU stressors, CPUs locked low.

## Result summary

| metric | value |
|--------|------:|
| Samples | 149 (180 s) |
| GPU avg MHz | **850** (zero throttling) |
| GPU throttled samples | **0/149 (0%)** |
| SoC peak C | 66.1 |
| GPU TZ peak C | 64.2 |
| cputop peak C | 64.4 |
| FPS first 10 s | 16.43 |
| FPS last 10 s | 16.45 |
| FPS avg | 16.41 |

## Conclusion

- -25 mV UV on all GPU OPPs is **thermally + electrically stable** at 850 MHz continuously.
- With CPU idle, the GPU's thermal contribution to SoC is modest (~66 C SoC peak vs 102 C under CPU+GPU torture).
- This validates the UV patch for gaming workloads where CPU rarely saturates all 8 cores.
- FPS is stable within noise (±0.1) across the entire 180 s, confirming no stability issues.
