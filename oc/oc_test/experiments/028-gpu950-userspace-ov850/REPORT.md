# 028-gpu950-userspace-ov850 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 76 | 2100 | 384 | 105.8 | 1050.0 | 844.1 | 60.11 | 0.00 | CPU perf -9.7%, SoC pk +0.8C |
| gpu | 127 | 1228 | 950 | 75.0 | 761.5 | 854.3 | 0.00 | 16.22 | GPU perf -0.3%, SoC pk +9.1C |
| both | 61 | 2100 | 458 | 109.9 | 1050.0 | 833.6 | 54.17 | 7.96 | CPU -10.3%, FPS -2.0%, SoC pk +4.1C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 950 | 768 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 2100 | 2100 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 2100 | 2100 | 1050.0 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 850.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 750.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 950 | 950 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2100 | 1820 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 953.1 | 800.0 |
| cpu_policy6_sweep | 2100 | 2100 | 1050.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 718.8 | 700.0 |
| gpu_sweep | 512 | 512 | 718.8 | 700.0 |
| gpu_sweep | 614 | 614 | 718.8 | 700.0 |
| gpu_sweep | 768 | 768 | 718.8 | 700.0 |
| gpu_sweep | 950 | 950 | 718.8 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 718.8 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 718.8 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 750.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 837.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 853.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 915.6 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 953.1 | 800.0 |
| cpu_policy0_sweep | 2100 | 1820 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 953.1 | 800.0 |
| cpu_policy6_sweep | 2100 | 1872 | 953.1 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 75.1 |
| `thermal_zone10_ank4-thmzone` | 99.8 |
| `thermal_zone11_ank5-thmzone` | 98.0 |
| `thermal_zone12_cputop-thmzone` | 103.1 |
| `thermal_zone13_gpuank2-thmzone` | 97.9 |
| `thermal_zone1_soc-thmzone` | 109.9 |
| `thermal_zone2_prometheus6-tzone0` | 98.5 |
| `thermal_zone3_prometheus6-tzone1` | 105.3 |
| `thermal_zone4_prometheus7-thmzone` | 107.1 |
| `thermal_zone5_ank0-thmzone` | 107.3 |
| `thermal_zone6_ank1-thmzone` | 107.8 |
| `thermal_zone7_gpu-thmzone` | 101.8 |
| `thermal_zone8_ank2-thmzone` | 100.5 |
| `thermal_zone9_ank3-thmzone` | 100.8 |
