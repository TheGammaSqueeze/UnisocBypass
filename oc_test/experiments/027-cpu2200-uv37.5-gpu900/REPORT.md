# 027-cpu2200-uv37.5-gpu900 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 84 | 2200 | 384 | 106.0 | 1050.0 | 700.0 | 66.20 | 0.00 | CPU perf -0.5%, SoC pk +1.0C |
| gpu | 129 | 1228 | 900 | 67.2 | 760.8 | 799.2 | 0.00 | 16.27 | GPU perf +0.0%, SoC pk +1.3C |
| both | 64 | 2200 | 457 | 107.8 | 1050.0 | 711.7 | 56.91 | 8.05 | CPU -5.8%, FPS -0.9%, SoC pk +2.1C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 750.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 750.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 900 | 768 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 1820 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 953.1 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 953.1 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 953.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 953.1 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 953.1 | 700.0 |
| cpu_policy0_sweep | 2200 | 1820 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 953.1 | 700.0 |
| cpu_policy6_sweep | 2200 | 1872 | 953.1 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 700.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 750.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2200 | 2200 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2200 | 2200 | 1050.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 718.8 | 700.0 |
| gpu_sweep | 512 | 512 | 718.8 | 700.0 |
| gpu_sweep | 614 | 614 | 718.8 | 700.0 |
| gpu_sweep | 768 | 768 | 718.8 | 700.0 |
| gpu_sweep | 900 | 900 | 718.8 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 718.8 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 718.8 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 750.0 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 837.5 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 853.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 915.6 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 953.1 | 700.0 |
| cpu_policy0_sweep | 2200 | 1820 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 953.1 | 700.0 |
| cpu_policy6_sweep | 2200 | 1872 | 953.1 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 72.7 |
| `thermal_zone10_ank4-thmzone` | 99.0 |
| `thermal_zone11_ank5-thmzone` | 97.2 |
| `thermal_zone12_cputop-thmzone` | 101.0 |
| `thermal_zone13_gpuank2-thmzone` | 98.7 |
| `thermal_zone1_soc-thmzone` | 107.8 |
| `thermal_zone2_prometheus6-tzone0` | 95.2 |
| `thermal_zone3_prometheus6-tzone1` | 102.4 |
| `thermal_zone4_prometheus7-thmzone` | 107.3 |
| `thermal_zone5_ank0-thmzone` | 107.3 |
| `thermal_zone6_ank1-thmzone` | 108.4 |
| `thermal_zone7_gpu-thmzone` | 100.8 |
| `thermal_zone8_ank2-thmzone` | 100.0 |
| `thermal_zone9_ank3-thmzone` | 100.3 |
