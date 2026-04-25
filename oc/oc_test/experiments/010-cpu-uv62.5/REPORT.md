# 010-cpu-uv62.5 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 97 | 2002 | 384 | 101.9 | 987.5 | 700.0 | 73.00 | 0.00 | CPU perf +9.7%, SoC pk -3.1C |
| gpu | 129 | 1228 | 850 | 64.4 | 693.8 | 799.2 | 0.00 | 16.25 | GPU perf -0.1%, SoC pk -1.6C |
| both | 78 | 2002 | 479 | 104.5 | 987.5 | 718.6 | 61.28 | 8.44 | CPU +1.5%, FPS +4.0%, SoC pk -1.3C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 987.5 | 700.0 |
| gpu_sweep | 512 | 512 | 987.5 | 700.0 |
| gpu_sweep | 614 | 614 | 987.5 | 700.0 |
| gpu_sweep | 768 | 768 | 987.5 | 800.0 |
| gpu_sweep | 850 | 850 | 987.5 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 987.5 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 987.5 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 987.5 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 987.5 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 987.5 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 987.5 | 700.0 |
| gpu_sweep | 512 | 512 | 987.5 | 700.0 |
| gpu_sweep | 614 | 614 | 987.5 | 700.0 |
| gpu_sweep | 768 | 768 | 987.5 | 700.0 |
| gpu_sweep | 850 | 850 | 987.5 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 987.5 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 987.5 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 987.5 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 987.5 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 987.5 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 987.5 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 987.5 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 693.8 | 700.0 |
| gpu_sweep | 512 | 512 | 693.8 | 750.0 |
| gpu_sweep | 614 | 614 | 693.8 | 700.0 |
| gpu_sweep | 768 | 768 | 693.8 | 700.0 |
| gpu_sweep | 850 | 850 | 693.8 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 693.8 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 693.8 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 693.8 | 800.0 |
| cpu_policy0_sweep | 1144 | 1144 | 693.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 725.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 812.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 828.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 890.6 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 928.1 | 800.0 |
| cpu_policy0_sweep | 2002 | 2002 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 987.5 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 987.5 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 987.5 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 987.5 | 800.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 70.1 |
| `thermal_zone10_ank4-thmzone` | 97.4 |
| `thermal_zone11_ank5-thmzone` | 95.9 |
| `thermal_zone12_cputop-thmzone` | 99.2 |
| `thermal_zone13_gpuank2-thmzone` | 96.1 |
| `thermal_zone1_soc-thmzone` | 104.5 |
| `thermal_zone2_prometheus6-tzone0` | 93.4 |
| `thermal_zone3_prometheus6-tzone1` | 100.1 |
| `thermal_zone4_prometheus7-thmzone` | 104.0 |
| `thermal_zone5_ank0-thmzone` | 103.7 |
| `thermal_zone6_ank1-thmzone` | 104.5 |
| `thermal_zone7_gpu-thmzone` | 98.5 |
| `thermal_zone8_ank2-thmzone` | 97.7 |
| `thermal_zone9_ank3-thmzone` | 98.0 |
