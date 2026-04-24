# Experiment comparison vs stock baselines

Auto-generated from `oc_test/experiments/*/{cpu,gpu,both}/telemetry.csv` and friends. Stock baselines: 005 (cpu-only), 006 (gpu-only), 007 (both).

## Stock baseline reference

| mode | samples | GPU avg MHz | GPU throttled % | SoC peak C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | FPS last 10s |
|------|--------:|------------:|----------------:|-----------:|----------:|----------:|--------:|--------:|-------------:|
| cpu | 85 | 384 | 100% | 105.0 | 1050 | 700 | 66.53 | 0.00 | 0.00 |
| gpu | 129 | 850 | 0% | 66.0 | 761 | 799 | 0.00 | 16.27 | 16.23 |
| both | 75 | 446 | 86% | 105.8 | 1050 | 713 | 60.39 | 8.12 | 7.48 |

## 000-stock-baseline

Config: stock, no DTB modifications

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| both | 109 | 517 | 71% | 102.1 | 0 | 0 | 75.12 | 9.56 | CPU +24.4%, FPS +17.7%, SoC -3.6C |

## 001-gpu-uv-top-12.5mV

Config: top GPU OPP voltage reduced by 12.5 mV (one SC2730 DCDC step)

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| both | 112 | 499 | 75% | 101.9 | 0 | 0 | 76.37 | 9.22 | CPU +26.5%, FPS +13.5%, SoC -3.9C |

## 002-gpu-uv-all-25mV

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| both | 95 | 506 | 75% | 106.3 | 0 | 0 | 62.42 | 8.86 | CPU +3.4%, FPS +9.1%, SoC +0.5C |

## 003-gpu-uv-all-25mV-gpu-only-load

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| gpu | 149 | 850 | 0% | 66.1 | 0 | 0 | 0.00 | 16.41 | GPU perf +0.8%, SoC +0.2C, vddgpu -799mV |

## 004-gpu-uv37.5-cpu-uv25

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| both | 96 | 525 | 69% | 102.9 | 1025 | 728 | 72.62 | 9.16 | CPU +20.2%, FPS +12.8%, SoC -2.9C |

## 008-cpu-uv37.5-gpu-uv25

Config: CPU LITTLE/BIG UV -37.5 mV across all OPPs, GPU UV -25 mV across all OPPs

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 114 | 384 | 100% | 98.8 | 1012 | 700 | 81.20 | 0.00 | CPU perf +22.1%, SoC -6.2C, vddcpu -38mV |
| gpu | 129 | 850 | 0% | 61.0 | 719 | 799 | 0.00 | 16.26 | GPU perf ~0%, SoC -4.9C, vddgpu +0mV |
| both | 86 | 482 | 79% | 105.5 | 1012 | 720 | 65.83 | 8.56 | CPU +9.0%, FPS +5.4%, SoC -0.3C |

## 009-cpu-uv50-gpu-uv37.5

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 106 | 384 | 100% | 101.1 | 1009 | 700 | 77.51 | 0.00 | CPU perf +16.5%, SoC -3.9C, vddcpu -41mV |
| gpu | 129 | 850 | 0% | 62.8 | 706 | 799 | 0.00 | 16.21 | GPU perf -0.4%, SoC -3.1C, vddgpu +0mV |
| both | 81 | 467 | 82% | 105.3 | 1000 | 717 | 63.87 | 8.45 | CPU +5.7%, FPS +4.0%, SoC -0.5C |

## 010-cpu-uv62.5

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 97 | 384 | 100% | 101.9 | 988 | 700 | 73.00 | 0.00 | CPU perf +9.7%, SoC -3.1C, vddcpu -62mV |
| gpu | 129 | 850 | 0% | 64.4 | 694 | 799 | 0.00 | 16.25 | GPU perf -0.1%, SoC -1.6C, vddgpu +0mV |
| both | 78 | 479 | 80% | 104.5 | 988 | 719 | 61.28 | 8.44 | CPU +1.5%, FPS +4.0%, SoC -1.3C |

## 011-cpu-uv75

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 95 | 384 | 100% | 104.0 | 975 | 700 | 74.01 | 0.00 | CPU perf +11.2%, SoC -1.0C, vddcpu -75mV |
| gpu | 129 | 850 | 0% | 66.2 | 753 | 799 | 0.00 | 16.23 | GPU perf -0.3%, SoC +0.3C, vddgpu +0mV |
| both | 80 | 456 | 85% | 105.0 | 975 | 714 | 62.25 | 8.37 | CPU +3.1%, FPS +3.1%, SoC -0.8C |

## 012-cpu-uv87.5

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 89 | 384 | 100% | 105.8 | 1009 | 700 | 68.97 | 0.00 | CPU perf +3.7%, SoC +0.8C, vddcpu -41mV |
| gpu | 129 | 850 | 0% | 67.2 | 757 | 799 | 0.00 | 16.26 | GPU perf ~0%, SoC +1.3C, vddgpu +0mV |
| both | 76 | 482 | 78% | 105.0 | 962 | 721 | 61.87 | 8.37 | CPU +2.4%, FPS +3.1%, SoC -0.8C |

## 013-cpu-uv100

| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |
|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|
| cpu | 96 | 384 | 100% | 104.2 | 950 | 700 | 73.93 | 0.00 | CPU perf +11.1%, SoC -0.8C, vddcpu -100mV |
| gpu | 129 | 850 | 0% | 67.2 | 757 | 799 | 0.00 | 16.26 | GPU perf ~0%, SoC +1.3C, vddgpu +0mV |
| both | 81 | 479 | 80% | 104.7 | 950 | 719 | 62.53 | 8.44 | CPU +3.5%, FPS +3.9%, SoC -1.0C |

## Conclusions (running)

- **CPU UV lands on hardware.** vddcpu tracks the DT voltage reduction (minus AVS adjustment).
- **GPU UV via DTB does NOT land.** vddgpu stays at stock 700/800 mV regardless of DT voltage changes. Requires a different attack path (kernel module patch or as-yet-unidentified DT property).
- **Torture mode is CPU-thermal-dominated.** CPU-only hits 106 C just as fast as both-mode. GPU-only stays below 70 C. UV impact on both-mode thermals is modest (~1-2 C) unless the UV is deep enough to noticeably cut CPU power.
- **UV performance cliff**: TBD. Iterating down in 12.5 mV steps until either perf drops >10% or boot fails.
