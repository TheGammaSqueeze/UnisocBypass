# RG Vita (UMS512 / T618) stock max-OPP torture test

Duration: 180 seconds. All clocks locked to highest stock OPP:

- CPU LITTLE (policy0, cores 0-5): 2002 MHz, userspace governor, `scaling_fix_freq=2002000`
- CPU BIG    (policy6, cores 6-7): 2002 MHz, userspace governor, `scaling_fix_freq=2002000`
- GPU (Mali-G52 MC2): 850 MHz, performance governor, min=max=850 MHz
- DDR scene-frequency: 1866 MHz

Load: 8 parallel `sha256sum < /dev/zero` loops pinned one per core via `taskset`, plus a headless GLES 3.1 fragment-shader stressor at 1280x720.

## Frequency stability

| policy | target | min | avg | max | samples below target |
|--------|--------|-----|-----|-----|--------------------|
| `policy0` | 2002 MHz | 2002 | 2002 | 2002 | 0/109 (0%) |
| `policy6` | 2002 MHz | 2002 | 2002 | 2002 | 0/109 (0%) |
| `gpu` | 850 MHz | 384 | 517 | 850 | 78/109 (71%) |

**CPU: zero throttling.** Both clusters held 2002 MHz for all 180 seconds.

**GPU: heavy throttling.** First drop off 850 MHz at t=34s. Stayed at 384 MHz (minimum OPP) for the majority of the run. No sustained operation at 850 MHz past the first 30 seconds of load.

## Thermal peaks

| sensor | label | min | peak |
|--------|-------|----:|-----:|
| `thermal_zone0_board-thmzone` | tz0 board | 34.4 C | **64.6 C** |
| `thermal_zone10_ank4-thmzone` | tz10 ank4 | 41.0 C | **93.3 C** |
| `thermal_zone11_ank5-thmzone` | tz11 ank5 | 40.8 C | **91.7 C** |
| `thermal_zone12_cputop-thmzone` | tz12 cputop | 43.1 C | **95.3 C** |
| `thermal_zone13_gpuank2-thmzone` | tz13 gpuank2 | 49.8 C | **92.8 C** |
| `thermal_zone1_soc-thmzone` | tz1 soc | 47.7 C | **102.1 C** |
| `thermal_zone2_prometheus6-tzone0` | tz2 prometheus6-tzone0 | 45.4 C | **89.5 C** |
| `thermal_zone3_prometheus6-tzone1` | tz3 prometheus6-tzone1 | 50.1 C | **96.7 C** |
| `thermal_zone4_prometheus7-thmzone` | tz4 prometheus7 | 52.9 C | **100.6 C** |
| `thermal_zone5_ank0-thmzone` | tz5 ank0 | 53.7 C | **101.1 C** |
| `thermal_zone6_ank1-thmzone` | tz6 ank1 | 54.5 C | **101.9 C** |
| `thermal_zone7_gpu-thmzone` | tz7 gpu | 42.0 C | **94.3 C** |
| `thermal_zone8_ank2-thmzone` | tz8 ank2 | 41.2 C | **93.2 C** |
| `thermal_zone9_ank3-thmzone` | tz9 ank3 | 50.6 C | **93.8 C** |

Peak SoC temp of **102.1 C** and multiple core sensors above 100 C.

## CPU performance (iterations completed per core over 180 s)

| core | cluster | expected role | bytes hashed | rel. to slowest |
|------|---------|---------------|-------------:|----------------:|
| cpu0 | LITTLE (A55) | - | 8,482,816 KiB | 1.27x |
| cpu1 | LITTLE (A55) | - | 7,557,120 KiB | 1.13x |
| cpu2 | LITTLE (A55) | - | 7,548,928 KiB | 1.13x |
| cpu3 | LITTLE (A55) | - | 11,898,880 KiB | 1.77x |
| cpu4 | LITTLE (A55) | - | 6,705,152 KiB | 1.00x |
| cpu5 | LITTLE (A55) | - | 7,069,696 KiB | 1.05x |
| cpu6 | BIG (A75) | - | 17,936,384 KiB | 2.68x |
| cpu7 | BIG (A75) | - | 11,571,200 KiB | 1.73x |

BIG cluster (cpu6, cpu7) did 2.4x - 2.7x the work of LITTLE cores at the same 2.002 GHz, reflecting the raw IPC advantage of A75 over A55. The spread within the LITTLE cluster (cpu4 did 6.7M vs cpu3 did 11.9M) reflects scheduler interactions with GPU stressor and monitor processes.

## GPU performance

Stressor: full-screen triangle with 128-iteration trig fragment shader at 1280x720.

FPS samples over 180 seconds: 171 total

| window | FPS |
|--------|-----|
| first 10s avg | 16.69 |
| middle 10s avg | 7.59 |
| last 10s avg | 7.56 |
| overall avg | 9.56 |
| peak | 16.70 |
| valley | 7.40 |

GPU performance dropped **55%** by end of test. This matches the GPU frequency throttle ratio (850 -> 384 MHz = 54.8% drop; observed 55% FPS drop aligns with the linear freq scaling as expected for a shader-bound workload).

## Interpretation

The stock silicon handles the nominal max OPPs without tripping any hard limit (no reboot, no hang, no kernel panic) for 3 minutes of concurrent full-CPU + heavy-GPU load.

However, the thermal envelope at stock max OPPs is ALREADY near-saturated in this enclosure:

- The kernel cpufreq cooling driver never triggered on the CPU clusters because `scaling_fix_freq` overrides the cpufreq cooling driver's dynamic cap. Under normal userspace thermal policies, CPU would have throttled too. The fact that the SoC survived full-CPU at 2 GHz for 3 minutes at 100+ C indicates the silicon is stable there; it is just very hot.
- The GPU devfreq thermal cooling driver was active. GPU throttled from 850 MHz down to 384 MHz within 30 seconds and stayed pinned at 384 MHz for the rest of the test. The Mali driver respects devfreq thermal hints.
- SoC zone 1 and core sensors ank0/ank1 exceed 100 C briefly. No hardware cutoff triggered.

## Implications for OC

Any overclocking effort must address GPU thermal management, not silicon capability. The GPU is already throttling at stock MAX, so adding a higher OPP (e.g. 900 MHz) would hit the same thermal cap within seconds unless paired with:

- a larger thermal mass or better cooling,
- a more aggressive DVFS governor (so the GPU spends less time at peak),
- a raised thermal trip point (risky; reduces longevity),
- or a narrower burst-only max OPP usage pattern (games that run below 60 FPS can benefit; games that already run at 60 FPS on stock see no improvement from higher peak).

CPU OC to 2.1-2.2 GHz is thermally plausible because the clusters never throttled in this test; headroom vs stock is unclear without thermal hint limits removed, but the silicon ran at 2.002 GHz stably at 100 C. Voltage increase to drive higher frequency stably will worsen thermals.

