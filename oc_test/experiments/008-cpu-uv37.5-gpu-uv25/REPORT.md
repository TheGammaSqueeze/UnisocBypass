# 008-cpu-uv37.5-gpu-uv25 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 114 | 2002 | 384 | 98.8 | 1012.5 | 700.0 | 81.20 | 0.00 | CPU perf +305.6%, SoC pk -7.3C |
| gpu | 129 | 1228 | 850 | 61.0 | 718.8 | 799.2 | 0.00 | 16.26 | GPU perf +17.3%, SoC pk -7.5C |
| both | 86 | 2002 | 482 | 105.5 | 1012.5 | 719.8 | 65.83 | 8.56 | CPU +410.4%, FPS +74.7%, SoC pk -1.3C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 800.0 |
| gpu_sweep | 850 | 850 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 614 | 2002 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 768 | 2002 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 962 | 2002 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1144 | 2002 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 1228 | 2002 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 2002 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 2002 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1716 | 2002 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1820 | 2002 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1228 | 2002 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1482 | 2002 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1536 | 2002 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 1742 | 2002 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1872 | 2002 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1012.5 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1012.5 | 700.0 |
| gpu_sweep | 512 | 512 | 1012.5 | 700.0 |
| gpu_sweep | 614 | 614 | 1012.5 | 700.0 |
| gpu_sweep | 768 | 768 | 1012.5 | 700.0 |
| gpu_sweep | 850 | 850 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1012.5 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1012.5 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1012.5 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 718.8 | 700.0 |
| gpu_sweep | 512 | 512 | 718.8 | 700.0 |
| gpu_sweep | 614 | 614 | 718.8 | 700.0 |
| gpu_sweep | 768 | 768 | 718.8 | 700.0 |
| gpu_sweep | 850 | 850 | 718.8 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 718.8 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 718.8 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 750.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 837.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 853.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 915.6 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 953.1 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1012.5 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1012.5 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1012.5 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 69.7 |
| `thermal_zone10_ank4-thmzone` | 96.7 |
| `thermal_zone11_ank5-thmzone` | 94.3 |
| `thermal_zone12_cputop-thmzone` | 98.5 |
| `thermal_zone13_gpuank2-thmzone` | 95.3 |
| `thermal_zone1_soc-thmzone` | 105.5 |
| `thermal_zone2_prometheus6-tzone0` | 93.6 |
| `thermal_zone3_prometheus6-tzone1` | 100.3 |
| `thermal_zone4_prometheus7-thmzone` | 105.0 |
| `thermal_zone5_ank0-thmzone` | 105.0 |
| `thermal_zone6_ank1-thmzone` | 106.0 |
| `thermal_zone7_gpu-thmzone` | 97.4 |
| `thermal_zone8_ank2-thmzone` | 96.4 |
| `thermal_zone9_ank3-thmzone` | 96.7 |
