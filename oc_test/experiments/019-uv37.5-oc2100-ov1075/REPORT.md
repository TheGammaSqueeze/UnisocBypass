# 019-uv37.5-oc2100-ov1075 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 80 | 2100 | 384 | 106.0 | 1009.4 | 700.0 | 62.14 | 0.00 | CPU perf -6.6%, SoC pk +1.0C |
| gpu | 128 | 1228 | 850 | 68.5 | 761.1 | 800.0 | 0.00 | 16.23 | GPU perf -0.3%, SoC pk +2.6C |
| both | 76 | 2100 | 458 | 105.0 | 1009.4 | 714.5 | 60.45 | 8.23 | CPU +0.1%, FPS +1.4%, SoC pk -0.8C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 850 | 850 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 2100 | 2100 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 2100 | 2100 | 1009.4 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1075.0 | 800.0 |
| gpu_sweep | 850 | 850 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1075.0 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1075.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1075.0 | 700.0 |
| cpu_policy0_sweep | 2100 | 2100 | 1075.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1075.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1075.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1075.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1075.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1075.0 | 800.0 |
| cpu_policy6_sweep | 2100 | 2100 | 1075.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 750.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 750.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 850 | 850 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 2100 | 2100 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 2100 | 2100 | 1009.4 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 70.9 |
| `thermal_zone10_ank4-thmzone` | 96.1 |
| `thermal_zone11_ank5-thmzone` | 94.6 |
| `thermal_zone12_cputop-thmzone` | 98.7 |
| `thermal_zone13_gpuank2-thmzone` | 94.5 |
| `thermal_zone1_soc-thmzone` | 105.0 |
| `thermal_zone2_prometheus6-tzone0` | 93.1 |
| `thermal_zone3_prometheus6-tzone1` | 100.3 |
| `thermal_zone4_prometheus7-thmzone` | 104.5 |
| `thermal_zone5_ank0-thmzone` | 104.2 |
| `thermal_zone6_ank1-thmzone` | 105.0 |
| `thermal_zone7_gpu-thmzone` | 97.7 |
| `thermal_zone8_ank2-thmzone` | 96.6 |
| `thermal_zone9_ank3-thmzone` | 96.7 |
