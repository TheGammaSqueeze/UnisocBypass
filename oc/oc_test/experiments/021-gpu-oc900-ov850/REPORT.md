# 021-gpu-oc900-ov850 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 98 | 2002 | 384 | 102.4 | 1050.0 | 700.0 | 73.22 | 0.00 | CPU perf +10.1%, SoC pk -2.6C |
| gpu | 129 | 1228 | 900 | 64.7 | 756.4 | 800.0 | 0.00 | 16.23 | GPU perf -0.3%, SoC pk -1.3C |
| both | 66 | 2002 | 452 | 105.5 | 1050.0 | 712.1 | 56.05 | 8.07 | CPU -7.2%, FPS -0.6%, SoC pk -0.3C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 614 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 800.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 2002 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 768 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 2002 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 2002 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 2002 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 2002 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 2002 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 700.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 750.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 800.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 1050.0 | 800.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 756.2 | 700.0 |
| gpu_sweep | 512 | 512 | 756.2 | 700.0 |
| gpu_sweep | 614 | 614 | 756.2 | 700.0 |
| gpu_sweep | 768 | 768 | 756.2 | 700.0 |
| gpu_sweep | 900 | 900 | 756.2 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 756.2 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 756.2 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 756.2 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 756.2 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 787.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 875.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 890.6 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 953.1 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 990.6 | 800.0 |
| cpu_policy0_sweep | 2002 | 1820 | 990.6 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 990.6 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 990.6 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 990.6 | 800.0 |
| cpu_policy6_sweep | 2002 | 1872 | 990.6 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 70.6 |
| `thermal_zone10_ank4-thmzone` | 98.0 |
| `thermal_zone11_ank5-thmzone` | 95.6 |
| `thermal_zone12_cputop-thmzone` | 100.5 |
| `thermal_zone13_gpuank2-thmzone` | 95.3 |
| `thermal_zone1_soc-thmzone` | 105.5 |
| `thermal_zone2_prometheus6-tzone0` | 94.1 |
| `thermal_zone3_prometheus6-tzone1` | 101.4 |
| `thermal_zone4_prometheus7-thmzone` | 104.0 |
| `thermal_zone5_ank0-thmzone` | 105.5 |
| `thermal_zone6_ank1-thmzone` | 105.5 |
| `thermal_zone7_gpu-thmzone` | 99.0 |
| `thermal_zone8_ank2-thmzone` | 97.4 |
| `thermal_zone9_ank3-thmzone` | 97.7 |
