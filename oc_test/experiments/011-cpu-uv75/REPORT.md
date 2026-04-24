# 011-cpu-uv75 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 95 | 2002 | 384 | 104.0 | 975.0 | 700.0 | 74.01 | 0.00 | CPU perf +11.2%, SoC pk -1.0C |
| gpu | 129 | 1228 | 850 | 66.2 | 753.1 | 799.2 | 0.00 | 16.23 | GPU perf -0.3%, SoC pk +0.3C |
| both | 80 | 2002 | 456 | 105.0 | 975.0 | 713.8 | 62.25 | 8.37 | CPU +3.1%, FPS +3.1%, SoC pk -0.8C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1009.4 | 700.0 |
| gpu_sweep | 512 | 512 | 1009.4 | 750.0 |
| gpu_sweep | 614 | 614 | 1009.4 | 750.0 |
| gpu_sweep | 768 | 768 | 975.0 | 700.0 |
| gpu_sweep | 850 | 850 | 975.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 975.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 975.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 975.0 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 975.0 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 975.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 975.0 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 975.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 975.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 975.0 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 975.0 | 700.0 |
| gpu_sweep | 512 | 512 | 975.0 | 700.0 |
| gpu_sweep | 614 | 614 | 975.0 | 700.0 |
| gpu_sweep | 768 | 768 | 975.0 | 700.0 |
| gpu_sweep | 850 | 850 | 975.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 975.0 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 975.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 975.0 | 800.0 |
| cpu_policy0_sweep | 1228 | 1229 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 975.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 975.0 | 800.0 |
| cpu_policy0_sweep | 1820 | 1820 | 975.0 | 700.0 |
| cpu_policy0_sweep | 2002 | 2002 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 975.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 975.0 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 975.0 | 800.0 |
| cpu_policy6_sweep | 1872 | 1872 | 975.0 | 700.0 |
| cpu_policy6_sweep | 2002 | 2002 | 975.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 681.2 | 700.0 |
| gpu_sweep | 512 | 512 | 681.2 | 700.0 |
| gpu_sweep | 614 | 614 | 681.2 | 700.0 |
| gpu_sweep | 768 | 768 | 681.2 | 700.0 |
| gpu_sweep | 850 | 850 | 681.2 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 681.2 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 681.2 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 681.2 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 681.2 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 712.5 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 800.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 815.6 | 800.0 |
| cpu_policy0_sweep | 1716 | 1716 | 878.1 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 915.6 | 700.0 |
| cpu_policy0_sweep | 2002 | 1820 | 915.6 | 700.0 |
| cpu_policy6_sweep | 1228 | 1229 | 915.6 | 700.0 |
| cpu_policy6_sweep | 1482 | 1482 | 915.6 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 915.6 | 800.0 |
| cpu_policy6_sweep | 1742 | 1742 | 915.6 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 915.6 | 700.0 |
| cpu_policy6_sweep | 2002 | 1872 | 915.6 | 700.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 70.9 |
| `thermal_zone10_ank4-thmzone` | 96.4 |
| `thermal_zone11_ank5-thmzone` | 94.8 |
| `thermal_zone12_cputop-thmzone` | 98.5 |
| `thermal_zone13_gpuank2-thmzone` | 95.8 |
| `thermal_zone1_soc-thmzone` | 105.0 |
| `thermal_zone2_prometheus6-tzone0` | 94.1 |
| `thermal_zone3_prometheus6-tzone1` | 101.4 |
| `thermal_zone4_prometheus7-thmzone` | 105.0 |
| `thermal_zone5_ank0-thmzone` | 104.7 |
| `thermal_zone6_ank1-thmzone` | 105.5 |
| `thermal_zone7_gpu-thmzone` | 97.7 |
| `thermal_zone8_ank2-thmzone` | 96.6 |
| `thermal_zone9_ank3-thmzone` | 96.9 |
