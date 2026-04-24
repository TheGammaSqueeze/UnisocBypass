# 009-cpu-uv50-gpu-uv37.5 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 106 | 2002 | 384 | 101.1 | 1009.4 | 700.0 | 77.51 | 0.00 | CPU perf +16.5%, SoC pk -3.9C |
| gpu | 129 | 1228 | 850 | 62.8 | 706.2 | 799.2 | 0.00 | 16.21 | GPU perf -0.4%, SoC pk -3.1C |
| both | 81 | 2002 | 467 | 105.3 | 1000.0 | 717.3 | 63.87 | 8.45 | CPU +5.7%, FPS +4.0%, SoC pk -0.5C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 750.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 750.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 800.0 |
| gpu_sweep | 850 | 850 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1009.4 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 800.0 |
| gpu_sweep | 850 | 850 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1009.4 | 800.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 706.2 | 700.0 |
| gpu_sweep | 512 | 512 | 706.2 | 700.0 |
| gpu_sweep | 614 | 614 | 706.2 | 700.0 |
| gpu_sweep | 768 | 768 | 706.2 | 700.0 |
| gpu_sweep | 850 | 850 | 706.2 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 706.2 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 706.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 706.2 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 706.2 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 737.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 825.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 840.6 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 903.1 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 940.6 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1000.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1000.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1000.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1000.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1000.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1000.0 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1000.0 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 69.2 |
| `thermal_zone10_ank4-thmzone` | 96.7 |
| `thermal_zone11_ank5-thmzone` | 94.8 |
| `thermal_zone12_cputop-thmzone` | 99.0 |
| `thermal_zone13_gpuank2-thmzone` | 95.3 |
| `thermal_zone1_soc-thmzone` | 105.3 |
| `thermal_zone2_prometheus6-tzone0` | 93.6 |
| `thermal_zone3_prometheus6-tzone1` | 100.6 |
| `thermal_zone4_prometheus7-thmzone` | 104.0 |
| `thermal_zone5_ank0-thmzone` | 104.2 |
| `thermal_zone6_ank1-thmzone` | 105.0 |
| `thermal_zone7_gpu-thmzone` | 98.0 |
| `thermal_zone8_ank2-thmzone` | 97.2 |
| `thermal_zone9_ank3-thmzone` | 97.2 |
