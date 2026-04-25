# 024-gpu-oc900-mali-only REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 93 | 2002 | 384 | 106.0 | 1009.4 | 700.0 | 72.77 | 0.00 | CPU perf +9.4%, SoC pk +1.0C |
| gpu | 129 | 1228 | 900 | 69.0 | 762.3 | 799.2 | 0.00 | 16.25 | GPU perf -0.1%, SoC pk +3.0C |
| both | 62 | 2002 | 434 | 108.1 | 1050.0 | 787.9 | 56.52 | 8.45 | CPU -6.4%, FPS +4.0%, SoC pk +2.3C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 768 | 1009.4 | 800.0 |
| gpu_sweep | 614 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1009.4 | 700.0 |
| gpu_sweep | 900 | 900 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 614 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 768 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 962 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1144 | 2002 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 1228 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1482 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1536 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1716 | 2002 | 1009.4 | 700.0 |
| cpu_policy0_sweep | 1820 | 2002 | 1009.4 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1228 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1482 | 2002 | 1009.4 | 800.0 |
| cpu_policy6_sweep | 1536 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1742 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 1872 | 2002 | 1009.4 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1009.4 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 700.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 756.2 | 700.0 |
| gpu_sweep | 512 | 512 | 756.2 | 700.0 |
| gpu_sweep | 614 | 614 | 756.2 | 700.0 |
| gpu_sweep | 768 | 768 | 756.2 | 700.0 |
| gpu_sweep | 900 | 900 | 756.2 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 756.2 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 756.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 756.2 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 756.2 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 787.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 875.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 890.6 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 953.1 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 990.6 | 700.0 |
| cpu_policy0_sweep | 2002 | 1820 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 990.6 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 990.6 | 700.0 |
| cpu_policy6_sweep | 2002 | 1872 | 990.6 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 69.6 |
| `thermal_zone10_ank4-thmzone` | 98.2 |
| `thermal_zone11_ank5-thmzone` | 96.1 |
| `thermal_zone12_cputop-thmzone` | 101.3 |
| `thermal_zone13_gpuank2-thmzone` | 96.3 |
| `thermal_zone1_soc-thmzone` | 108.1 |
| `thermal_zone2_prometheus6-tzone0` | 94.7 |
| `thermal_zone3_prometheus6-tzone1` | 102.4 |
| `thermal_zone4_prometheus7-thmzone` | 106.3 |
| `thermal_zone5_ank0-thmzone` | 108.1 |
| `thermal_zone6_ank1-thmzone` | 108.9 |
| `thermal_zone7_gpu-thmzone` | 100.0 |
| `thermal_zone8_ank2-thmzone` | 98.5 |
| `thermal_zone9_ank3-thmzone` | 98.7 |
