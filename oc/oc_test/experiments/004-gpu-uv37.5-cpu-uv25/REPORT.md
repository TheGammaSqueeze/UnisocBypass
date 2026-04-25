# 004 - GPU UV -37.5 mV + CPU UV -25 mV report

Test harness: `torture_test.sh` (8 pinned sha256sum CPU loops + GLES stressor), 180 s.

## Frequencies

| axis | target | observed min | observed avg | observed max | throttled % |
|------|--------|-------------:|-------------:|-------------:|------------:|
| CPU LITTLE | 2002 MHz | 2002 | 2002 | 2002 | 0% |
| CPU BIG | 2002 MHz | 2002 | 2002 | 2002 | 0% |
| GPU | 850 MHz | 384 | 518 | 850 | 72% |

## Thermal peaks

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 65.7 |
| `thermal_zone10_ank4-thmzone` | 93.8 |
| `thermal_zone11_ank5-thmzone` | 92.0 |
| `thermal_zone12_cputop-thmzone` | 96.1 |
| `thermal_zone13_gpuank2-thmzone` | 93.5 |
| `thermal_zone1_soc-thmzone` | 101.6 |
| `thermal_zone2_prometheus6-tzone0` | 90.0 |
| `thermal_zone3_prometheus6-tzone1` | 97.0 |
| `thermal_zone4_prometheus7-thmzone` | 101.4 |
| `thermal_zone5_ank0-thmzone` | 101.1 |
| `thermal_zone6_ank1-thmzone` | 101.9 |
| `thermal_zone7_gpu-thmzone` | 95.3 |
| `thermal_zone8_ank2-thmzone` | 94.8 |
| `thermal_zone9_ank3-thmzone` | 94.8 |

## Runtime rail voltages (measured post-test)

| rail | voltage | vs stock | notes |
|------|---------|---------|-------|
| vddcpu (at 2002 MHz) | 1025 mV | **-25 mV (applied)** | UV working |
| vddgpu (any freq) | 700 mV | 0 vs 700 mV idle / UNCHANGED at peak | UV NOT applied via sysfs; HW DVFS path bypasses Linux regulator framework |
| vddcore | 900 mV | unchanged | not modified |

## GPU FPS

| window | FPS |
|--------|----:|
| first 10 s | 16.25 |
| last 10 s | 7.51 |
| average | 9.39 |

## CPU throughput (iterations per core)

| core | cluster | KiB hashed |
|------|---------|-----------:|
| cpu0 | LITTLE (A55) | 8,974,336 |
| cpu1 | LITTLE (A55) | 7,360,512 |
| cpu2 | LITTLE (A55) | 7,409,664 |
| cpu3 | LITTLE (A55) | 12,480,512 |
| cpu4 | LITTLE (A55) | 6,496,256 |
| cpu5 | LITTLE (A55) | 6,909,952 |
| cpu6 | BIG (A75) | 17,297,408 |
| cpu7 | BIG (A75) | 12,132,352 |
| total | | **79,060,992** |

## Comparison vs baseline (exp 000)

| metric | 000 stock | 004 UV CPU+GPU | delta |
|--------|----------:|--------------:|------:|
| GPU avg MHz | 517 | 518 | +1.1 |
| SoC peak C | 102.1 | 101.6 | -0.5 |
| BIG peak C | 100.6 | 101.4 | +0.8 |
| FPS last 10 s | 7.56 | 7.51 | -0.05 |

## Interpretation

- **CPU UV confirmed working** at the regulator level: vddcpu runs 1025 mV at 2002 MHz, exactly the UV'd value.
- **GPU UV did NOT apply at runtime.** The vddgpu regulator stays at 700 mV regardless of GPU frequency or DT OPP values. The Unisoc hardware DVFS path for the GPU programs voltage via a dedicated register sequence (driven by `sprd,dvfs-lists` hw_index slots) rather than through the Linux regulator framework, so modifying voltages in the DT has no observable effect.
- Thermal outcome essentially unchanged from stock: GPU still throttles from 850 MHz within 30 s. CPU power drop from UV -25 mV is ~5%, not enough to meaningfully shift the thermal envelope when 8 A55/A75 cores are at 2 GHz.
- Next experiment should target either deeper CPU UV (to verify linear scaling with voltage squared) or investigate the hardware DVFS voltage register path for GPU.
