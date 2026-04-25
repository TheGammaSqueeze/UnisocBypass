# 012-cpu-uv87.5 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 89 | 2002 | 384 | 105.8 | 1009.4 | 700.0 | 68.97 | 0.00 | CPU perf +3.7%, SoC pk +0.8C |
| gpu | 129 | 1228 | 850 | 67.2 | 756.7 | 799.2 | 0.00 | 16.26 | GPU perf -0.0%, SoC pk +1.3C |
| both | 76 | 2002 | 482 | 105.0 | 962.5 | 721.1 | 61.87 | 8.37 | CPU +2.4%, FPS +3.1%, SoC pk -0.8C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

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
| cpu_policy0_sweep | 1228 | 1229 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 700.0 |
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
| cpu_policy0_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1009.4 | 800.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 668.8 | 700.0 |
| gpu_sweep | 512 | 512 | 668.8 | 700.0 |
| gpu_sweep | 614 | 614 | 668.8 | 750.0 |
| gpu_sweep | 768 | 768 | 668.8 | 800.0 |
| gpu_sweep | 850 | 850 | 668.8 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 668.8 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 668.8 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 668.8 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 668.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 700.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 787.5 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 803.1 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 865.6 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 903.1 | 700.0 |
| cpu_policy0_sweep | 2002 | 1820 | 903.1 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 903.1 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 903.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 903.1 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 903.1 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 903.1 | 700.0 |
| cpu_policy6_sweep | 2002 | 1872 | 903.1 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 71.9 |
| `thermal_zone10_ank4-thmzone` | 97.7 |
| `thermal_zone11_ank5-thmzone` | 96.1 |
| `thermal_zone12_cputop-thmzone` | 99.8 |
| `thermal_zone13_gpuank2-thmzone` | 97.1 |
| `thermal_zone1_soc-thmzone` | 105.0 |
| `thermal_zone2_prometheus6-tzone0` | 94.9 |
| `thermal_zone3_prometheus6-tzone1` | 101.4 |
| `thermal_zone4_prometheus7-thmzone` | 104.5 |
| `thermal_zone5_ank0-thmzone` | 104.5 |
| `thermal_zone6_ank1-thmzone` | 104.7 |
| `thermal_zone7_gpu-thmzone` | 99.0 |
| `thermal_zone8_ank2-thmzone` | 98.2 |
| `thermal_zone9_ank3-thmzone` | 98.2 |
