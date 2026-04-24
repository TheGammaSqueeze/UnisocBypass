# 005-stock-cpu-only report

180 s torture in mode `cpu` on stock DTB. Pre-test OPP voltage sweep captured.

## Pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV | vddcore mV |
|-------|-----------:|-----------:|----------:|----------:|-----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 700.0 | 900.0 |
| cpu_policy0_sweep | 2002 | 1820 | 1009.4 | 700.0 | 900.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 700.0 | 900.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 700.0 | 900.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 700.0 | 900.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 | 900.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 | 900.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 700.0 | 900.0 |

## Stress-phase telemetry

| metric | min | avg | max |
|--------|----:|----:|----:|
| CPU0 MHz | 2002 | 2002 | 2002 |
| CPU6 MHz | 2002 | 2002 | 2002 |
| GPU MHz | 384 | 384 | 384 |
| vddcpu uV | 1050000 | 1050000 | 1050000 |
| vddgpu uV | 700000 | 700000 | 700000 |

## Thermal peaks

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 68.1 |
| `thermal_zone10_ank4-thmzone` | 95.6 |
| `thermal_zone11_ank5-thmzone` | 93.5 |
| `thermal_zone12_cputop-thmzone` | 99.5 |
| `thermal_zone13_gpuank2-thmzone` | 94.0 |
| `thermal_zone1_soc-thmzone` | 106.0 |
| `thermal_zone2_prometheus6-tzone0` | 93.9 |
| `thermal_zone3_prometheus6-tzone1` | 101.1 |
| `thermal_zone4_prometheus7-thmzone` | 104.0 |
| `thermal_zone5_ank0-thmzone` | 105.3 |
| `thermal_zone6_ank1-thmzone` | 106.0 |
| `thermal_zone7_gpu-thmzone` | 97.7 |
| `thermal_zone8_ank2-thmzone` | 95.8 |
| `thermal_zone9_ank3-thmzone` | 95.9 |

## CPU throughput

| core | cluster | KiB hashed |
|------|---------|-----------:|
| cpu0 | LITTLE (A55) | 2,265,088 |
| cpu1 | LITTLE (A55) | 1,974,272 |
| cpu2 | LITTLE (A55) | 2,064,384 |
| cpu3 | LITTLE (A55) | 3,444,736 |
| cpu4 | LITTLE (A55) | 1,736,704 |
| cpu5 | LITTLE (A55) | 1,867,776 |
| cpu6 | BIG (A75) | 4,222,976 |
| cpu7 | BIG (A75) | 3,416,064 |
| **total** | | **20,992,000** |
