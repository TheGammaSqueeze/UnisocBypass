# 013-cpu-uv100 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 96 | 2002 | 384 | 104.2 | 950.0 | 700.0 | 73.93 | 0.00 | CPU perf +11.1%, SoC pk -0.8C |
| gpu | 129 | 1228 | 850 | 67.2 | 756.7 | 799.2 | 0.00 | 16.26 | GPU perf -0.0%, SoC pk +1.3C |
| both | 81 | 2002 | 479 | 104.7 | 950.0 | 718.5 | 62.53 | 8.44 | CPU +3.5%, FPS +3.9%, SoC pk -1.0C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 950.0 | 700.0 |
| gpu_sweep | 850 | 850 | 950.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 950.0 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 950.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 950.0 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 950.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 950.0 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 950.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 950.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 950.0 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 950.0 | 700.0 |
| gpu_sweep | 512 | 512 | 950.0 | 700.0 |
| gpu_sweep | 614 | 614 | 950.0 | 700.0 |
| gpu_sweep | 768 | 768 | 950.0 | 700.0 |
| gpu_sweep | 850 | 850 | 950.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 950.0 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 950.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 950.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 950.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 950.0 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 950.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 950.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 950.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 950.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 656.2 | 700.0 |
| gpu_sweep | 512 | 512 | 656.2 | 700.0 |
| gpu_sweep | 614 | 614 | 656.2 | 750.0 |
| gpu_sweep | 768 | 768 | 656.2 | 800.0 |
| gpu_sweep | 850 | 850 | 656.2 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 656.2 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 656.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 656.2 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 656.2 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 687.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 775.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 790.6 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 853.1 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 890.6 | 700.0 |
| cpu_policy0_sweep | 2002 | 1820 | 890.6 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 890.6 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 890.6 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 890.6 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 890.6 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 890.6 | 700.0 |
| cpu_policy6_sweep | 2002 | 1872 | 890.6 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 71.4 |
| `thermal_zone10_ank4-thmzone` | 97.7 |
| `thermal_zone11_ank5-thmzone` | 96.1 |
| `thermal_zone12_cputop-thmzone` | 99.2 |
| `thermal_zone13_gpuank2-thmzone` | 96.3 |
| `thermal_zone1_soc-thmzone` | 104.7 |
| `thermal_zone2_prometheus6-tzone0` | 94.7 |
| `thermal_zone3_prometheus6-tzone1` | 101.1 |
| `thermal_zone4_prometheus7-thmzone` | 104.7 |
| `thermal_zone5_ank0-thmzone` | 104.2 |
| `thermal_zone6_ank1-thmzone` | 105.0 |
| `thermal_zone7_gpu-thmzone` | 99.0 |
| `thermal_zone8_ank2-thmzone` | 97.9 |
| `thermal_zone9_ank3-thmzone` | 98.2 |
