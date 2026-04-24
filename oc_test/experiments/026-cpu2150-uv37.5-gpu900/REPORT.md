# 026-cpu2150-uv37.5-gpu900 REPORT

## Summary across modes

| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |
|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|
| cpu | 110 | 2150 | 384 | 100.9 | 1050.0 | 700.0 | 78.73 | 0.00 | CPU perf +18.3%, SoC pk -4.1C |
| gpu | 129 | 1228 | 900 | 62.3 | 718.8 | 800.0 | 0.00 | 16.25 | GPU perf -0.2%, SoC pk -3.6C |
| both | 75 | 2150 | 467 | 105.3 | 1050.0 | 715.3 | 59.34 | 8.23 | CPU -1.7%, FPS +1.3%, SoC pk -0.5C |

## Voltage evidence

### mode=cpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 700.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 768 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 2150 | 1820 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 953.1 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 953.1 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 953.1 | 700.0 |
| cpu_policy6_sweep | 2150 | 2150 | 1050.0 | 700.0 |

### mode=gpu: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 1050.0 | 700.0 |
| gpu_sweep | 512 | 512 | 1050.0 | 750.0 |
| gpu_sweep | 614 | 614 | 1050.0 | 700.0 |
| gpu_sweep | 768 | 768 | 1050.0 | 700.0 |
| gpu_sweep | 900 | 900 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 614 | 614 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 768 | 768 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 962 | 962 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 1050.0 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 1050.0 | 800.0 |
| cpu_policy0_sweep | 2150 | 2150 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 2150 | 2150 | 1050.0 | 700.0 |

### mode=both: pre-test OPP voltage sweep

| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |
|-------|-----------:|-----------:|----------:|----------:|
| gpu_sweep | 384 | 384 | 718.8 | 700.0 |
| gpu_sweep | 512 | 512 | 718.8 | 700.0 |
| gpu_sweep | 614 | 614 | 718.8 | 700.0 |
| gpu_sweep | 768 | 768 | 718.8 | 800.0 |
| gpu_sweep | 900 | 900 | 718.8 | 800.0 |
| cpu_policy0_sweep | 614 | 614 | 718.8 | 800.0 |
| cpu_policy0_sweep | 768 | 768 | 718.8 | 700.0 |
| cpu_policy0_sweep | 962 | 962 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1144 | 1144 | 718.8 | 700.0 |
| cpu_policy0_sweep | 1228 | 1229 | 750.0 | 700.0 |
| cpu_policy0_sweep | 1482 | 1482 | 837.5 | 700.0 |
| cpu_policy0_sweep | 1536 | 1536 | 853.1 | 700.0 |
| cpu_policy0_sweep | 1716 | 1716 | 915.6 | 700.0 |
| cpu_policy0_sweep | 1820 | 1820 | 953.1 | 700.0 |
| cpu_policy0_sweep | 2150 | 2150 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1228 | 1229 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1482 | 1482 | 1050.0 | 800.0 |
| cpu_policy6_sweep | 1536 | 1536 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1742 | 1742 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 1872 | 1872 | 1050.0 | 700.0 |
| cpu_policy6_sweep | 2150 | 2150 | 1050.0 | 800.0 |

## Thermal peaks (both mode)

| sensor | peak C |
|--------|-------:|
| `thermal_zone0_board-thmzone` | 69.2 |
| `thermal_zone10_ank4-thmzone` | 96.4 |
| `thermal_zone11_ank5-thmzone` | 94.6 |
| `thermal_zone12_cputop-thmzone` | 99.5 |
| `thermal_zone13_gpuank2-thmzone` | 95.6 |
| `thermal_zone1_soc-thmzone` | 105.3 |
| `thermal_zone2_prometheus6-tzone0` | 93.4 |
| `thermal_zone3_prometheus6-tzone1` | 100.9 |
| `thermal_zone4_prometheus7-thmzone` | 104.5 |
| `thermal_zone5_ank0-thmzone` | 105.3 |
| `thermal_zone6_ank1-thmzone` | 105.8 |
| `thermal_zone7_gpu-thmzone` | 99.0 |
| `thermal_zone8_ank2-thmzone` | 97.7 |
| `thermal_zone9_ank3-thmzone` | 97.7 |
