# 020-gpu-oc900 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 71 | 2002 | 384 | 106.3 | 1050.0 | 700.0 | 57.23 | 0.00 | CPU perf -14.0%, SoC pk +1.3C |
| gpu | 101 | 1228 | 900 | 63.6 | 756.2 | 800.0 | 0.00 | 14.93 | GPU perf -8.2%, SoC pk -2.3C |
| both | 68 | 2002 | 458 | 105.5 | 1050.0 | 711.8 | 56.68 | 8.09 | CPU -6.2%, FPS -0.4%, SoC pk -0.3C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 700.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 2002 | 1820 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 800.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 756.2 | 700.0 |
| gpu_sweep | 512 | 512 | 756.2 | 750.0 |
| gpu_sweep | 614 | 614 | 756.2 | 750.0 |
| gpu_sweep | 768 | 768 | 756.2 | 800.0 |
| gpu_sweep | 900 | 900 | 756.2 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 756.2 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 756.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 756.2 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 756.2 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 787.5 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 875.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 890.6 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 953.1 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 990.6 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 800.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 756.2 | 700.0 |
| gpu_sweep | 512 | 512 | 756.2 | 750.0 |
| gpu_sweep | 614 | 614 | 756.2 | 750.0 |
| gpu_sweep | 768 | 768 | 756.2 | 800.0 |
| gpu_sweep | 900 | 900 | 756.2 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 756.2 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 756.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 756.2 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 756.2 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 787.5 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 875.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 890.6 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 953.1 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 990.6 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 71.4 |
| `thermal_zone10_ank4-thmzone` | 98.2 |
| `thermal_zone11_ank5-thmzone` | 95.6 |
| `thermal_zone12_cputop-thmzone` | 100.5 |
| `thermal_zone13_gpuank2-thmzone` | 95.8 |
| `thermal_zone1_soc-thmzone` | 105.5 |
| `thermal_zone2_prometheus6-tzone0` | 93.6 |
| `thermal_zone3_prometheus6-tzone1` | 101.4 |
| `thermal_zone4_prometheus7-thmzone` | 103.7 |
| `thermal_zone5_ank0-thmzone` | 104.5 |
| `thermal_zone6_ank1-thmzone` | 105.5 |
| `thermal_zone7_gpu-thmzone` | 99.2 |
| `thermal_zone8_ank2-thmzone` | 97.4 |
| `thermal_zone9_ank3-thmzone` | 98.0 |
