# 007-stock-both report

180 s torture in mode `both` on stock DTB. Pre-test OPP voltage sweep captured.

## Pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV | vddcore mV |
|-------|-----------:|-----------:|----------:|----------:|-----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 | 900.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 750.0 | 900.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 750.0 | 900.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 800.0 | 900.0 |
| gpu_sweep | 850 | 850 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 800.0 | 900.0 |
| cpu_policy0_sweep | 2002 | 1820 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 800.0 | 900.0 |
| cpu_policy6_sweep | 2002 | 1872 | 1009.4 | 800.0 | 900.0 |

## Stress-phase telemetry

| metric | min | avg | max |
|--------|----:|----:|----:|
| CPU0 MHz | 2002 | 2002 | 2002 |
| CPU6 MHz | 2002 | 2002 | 2002 |
| GPU MHz | 384 | 588 | 850 |
| vddcpu uV | 1009375 | 1009375 | 1009375 |
| vddgpu uV | 700000 | 744737 | 800000 |

## Thermal peaks

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 69.2 |
| `thermal_zone10_ank4-thmzone` | 98.0 |
| `thermal_zone11_ank5-thmzone` | 95.9 |
| `thermal_zone12_cputop-thmzone` | 101.6 |
| `thermal_zone13_gpuank2-thmzone` | 97.4 |
| `thermal_zone1_soc-thmzone` | 106.8 |
| `thermal_zone2_prometheus6-tzone0` | 94.9 |
| `thermal_zone3_prometheus6-tzone1` | 102.4 |
| `thermal_zone4_prometheus7-thmzone` | 104.5 |
| `thermal_zone5_ank0-thmzone` | 107.1 |
| `thermal_zone6_ank1-thmzone` | 107.1 |
| `thermal_zone7_gpu-thmzone` | 100.3 |
| `thermal_zone8_ank2-thmzone` | 99.0 |
| `thermal_zone9_ank3-thmzone` | 99.2 |

## CPU throughput

| core | cluster | KiB hashed |
|------|---------|-----------:|
| cpu0 | LITTLE (A55) | 1,490,944 |
| cpu1 | LITTLE (A55) | 1,257,472 |
| cpu2 | LITTLE (A55) | 1,277,952 |
| cpu3 | LITTLE (A55) | 2,334,720 |
| cpu4 | LITTLE (A55) | 1,073,152 |
| cpu5 | LITTLE (A55) | 1,159,168 |
| cpu6 | BIG (A75) | 2,658,304 |
| cpu7 | BIG (A75) | 2,273,280 |
| **total** | | **13,524,992** |

## GPU FPS (GLES 3.1 heavy fragment shader at 1280x720)

| window | FPS |
|--------|----:|
| first 10 s | 4.21 |
| last 10 s | 8.16 |
| average | 4.90 |
| peak | 8.40 |
| valley | 2.10 |
