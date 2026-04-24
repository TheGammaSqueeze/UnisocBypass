# 002 - GPU UV all OPPs, -25 mV

**Status:** completed 2026-04-24
**Device:** RG Vita (UMS512 / T618)

## Hypothesis

-25 mV across ALL five GPU OPPs should reduce GPU rail power across the whole DVFS range, not just at peak. Since the GPU spends most of the torture test throttled at 384 MHz, UV'ing the low OPPs should matter more than UV'ing the high OPPs.

## DTB changes

In the `gpu@60000000` node, all 5 voltages:

| OPP | stock | new |
|-----|------:|----:|
| 384 MHz | 700 mV (`0xaae60`) | 675 mV (`0xa4cb0`) |
| 512 MHz | 750 mV (`0xb71b0`) | 725 mV (`0xb1008`) |
| 614 MHz | 750 mV (`0xb71b0`) | 725 mV (`0xb1008`) |
| 768 MHz | 800 mV (`0xc3500`) | 775 mV (`0xbd358`) |
| 850 MHz | 800 mV (`0xc3500`) | 775 mV (`0xbd358`) |

Applied identically to `operating-points` and `sprd,dvfs-lists` in the GPU node.

## Result summary (vs baseline 000)

| metric | 000 stock | 002 UV -25 mV all |
|--------|----------:|-----------------:|
| GPU avg MHz | 517 | 506 |
| GPU throttled samples | 71% | 75% |
| SoC peak C | 102.1 | **106.3** |
| BIG peak C | 100.6 | **105.2** |
| GPU TZ peak C | 94.3 | 99.2 |
| FPS last 10 s | 7.56 | 7.52 |

Slightly hotter, not cooler. Run variance suspect (different ambient / starting temps). UV alone of -25 mV across all OPPs did not provide measurable benefit under the CPU-dominated torture test.

## Conclusion

UV helps GPU rail but the GPU rail is only ~10-15% of total SoC power during the torture test. CPU at 2 GHz x 8 cores dominates. Verified stable at -25 mV (no crash), so the UV itself works; the torture test just isn't sensitive to this change. See experiment 003 for the isolated GPU-only variant which confirms -25 mV UV is stable at 850 MHz indefinitely.
