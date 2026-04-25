# 006-stock-gpu-only report

180 s torture in mode `gpu` on stock DTB. Pre-test OPP voltage sweep captured.

## Pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV | vddcore mV |
|-------|-----------:|-----------:|----------:|----------:|-----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 | 900.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 750.0 | 900.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 750.0 | 900.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 800.0 | 900.0 |
| gpu_sweep | 850 | 850 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 800.0 | 900.0 |
| cpu_policy0_sweep | 2002 | 1820 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 800.0 | 900.0 |
| cpu_policy6_sweep | 2002 | 1872 | 1050.0 | 800.0 | 900.0 |

## Stress-phase telemetry

| metric | min | avg | max |
|--------|----:|----:|----:|
| CPU0 MHz | 614 | 614 | 614 |
| CPU6 MHz | 1228 | 1228 | 1228 |
| GPU MHz | 850 | 850 | 850 |
| vddcpu uV | 762500 | 762500 | 762500 |
| vddgpu uV | 800000 | 800000 | 800000 |

## Thermal peaks

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 56.7 |
| `thermal_zone10_ank4-thmzone` | 67.5 |
| `thermal_zone11_ank5-thmzone` | 68.0 |
| `thermal_zone12_cputop-thmzone` | 68.3 |
| `thermal_zone13_gpuank2-thmzone` | 69.9 |
| `thermal_zone1_soc-thmzone` | 68.5 |
| `thermal_zone2_prometheus6-tzone0` | 65.1 |
| `thermal_zone3_prometheus6-tzone1` | 66.7 |
| `thermal_zone4_prometheus7-thmzone` | 67.9 |
| `thermal_zone5_ank0-thmzone` | 67.4 |
| `thermal_zone6_ank1-thmzone` | 67.4 |
| `thermal_zone7_gpu-thmzone` | 67.8 |
| `thermal_zone8_ank2-thmzone` | 69.3 |
| `thermal_zone9_ank3-thmzone` | 68.6 |

## GPU FPS (GLES 3.1 heavy fragment shader at 1280x720)

| window | FPS |
|--------|----:|
| first 10 s | 10.81 |
| last 10 s | 16.23 |
| average | 13.86 |
| peak | 16.30 |
| valley | 8.40 |
