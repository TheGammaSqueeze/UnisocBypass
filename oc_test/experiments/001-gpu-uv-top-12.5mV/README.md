# 001 - GPU UV top OPP only, -12.5 mV

**Status:** completed 2026-04-24
**Device:** RG Vita (UMS512 / T618)
**Config:** top GPU OPP voltage reduced by 12.5 mV (one SC2730 DCDC step)

## Hypothesis

Dropping VDDGPU at the 850 MHz OPP from 800 mV to 787.5 mV will reduce GPU power at peak freq, delaying thermal-induced throttling under torture load.

## DTB changes

In the `gpu@60000000` node, the top OPP voltage only:

| field | old | new |
|-------|-----|-----|
| `operating-points` trailing pair | `0xcf850 0xc3500` | `0xcf850 0xc042c` |
| `sprd,dvfs-lists` trailing quad | `0xcf850 0xc3500 0x08 0x01` | `0xcf850 0xc042c 0x08 0x01` |

Only the 850 MHz / 800 mV pair was touched; 768 MHz and below are unchanged.

## Result summary (vs baseline 000)

| metric | 000 stock | 001 UV top |
|--------|----------:|-----------:|
| GPU avg MHz | 517 | 499 |
| GPU throttled samples | 71% | 75% |
| SoC peak C | 102.1 | 101.9 |
| BIG peak C | 100.6 | 101.1 |
| GPU TZ peak C | 94.3 | 95.1 |
| FPS last 10 s | 7.56 | 7.52 |

Essentially no difference; -12.5 mV on a single OPP at 850 MHz is < 2 % power reduction on the GPU rail, which is dwarfed by CPU-driven heat (CPU is the dominant thermal contributor in this test).

## Conclusion

Minimum safe UV step is tolerated but too small to change the overall picture. Next step: try -25 mV across all OPPs.
