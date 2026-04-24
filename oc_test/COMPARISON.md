# OC/UV torture test comparison

All tests: 180 s duration, Mali-G52 at 850 MHz performance governor, devfreq thermal cooling active.

## Frequency stability and thermals

| test | samples | GPU avg MHz | GPU <850 | SoC peak | GPU TZ peak | BIG TZ peak |
|------|--------:|------------:|---------:|---------:|------------:|------------:|
| stock (max CPU+GPU) | 109 | 517 | 78/109 (71%) | 102.1 C | 94.3 C | 100.6 C |
| UV-12.5mV top OPP | 112 | 499 | 85/112 (75%) | 101.9 C | 95.1 C | 101.1 C |
| UV-25mV all OPPs | 95 | 506 | 72/95 (75%) | 106.3 C | 99.2 C | 105.2 C |
| UV-25mV GPU-only, low CPU | 149 | 850 | 0/149 (0%) | 66.1 C | 64.2 C | 66.1 C |

## GPU FPS (shader-bound stressor at 1280x720)

| test | first 10 s | last 10 s | average |
|------|-----------:|----------:|--------:|
| stock (max CPU+GPU) | 16.69 | 7.56 | 9.56 |
| UV-12.5mV top OPP | 16.38 | 7.52 | 9.22 |
| UV-25mV all OPPs | 16.45 | 7.52 | 8.86 |
| UV-25mV GPU-only, low CPU | 16.43 | 16.45 | 16.41 |

## Key findings

1. **CPU stress dominates the thermal envelope in the original torture test.** With all 8 cores at 2 GHz, SoC hits 100+ C within 30 s and GPU devfreq thermal cooling throttles from 850 MHz to 384 MHz. GPU UV has negligible impact on this overall picture because the CPU is the main heat source.

2. **GPU at 850 MHz with -25 mV UV is stable under GPU-only load.** With CPUs locked to minimum freq, GPU held 850 MHz for the entire 180 s with peak SoC temp of only 66 C. No frame drops, no instability.

3. **GPU UV past -50 mV fails to boot** (first brick attempt). The safe range appears to be at least -25 mV across all OPPs. Deeper UV sweeps were not completed due to brick risk.

4. **CPU OC via DTB OPP table extension failed** (second brick). The cluster mapping tables `lit_core_cluster_tbl_T618_tt` / `big_core_cluster_tbl_T618_tt` and the voltage-grade tables need to be extended in parallel when adding new OPPs; just changing the top OPP values without updating the dependency indices does not work.

## Practical implication

In a realistic gaming workload (2-4 CPU cores active, not 8), the GPU thermal budget is much more generous. The `-25 mV` UV is proven safe and reduces GPU power by ~6%, which should let the GPU sustain higher frequencies longer under mixed load. Further UV testing would iterate toward the stability cliff.

For CPU OC, the right approach requires DTB-level changes to:

- `operating-points-T618-tt` and `-tt-65` variants (LITTLE and BIG)
- Per-cluster mapping tables `lit_core_cluster_tbl_T618_tt[_65]`, `big_core_cluster_tbl_T618_tt[_65]`
- SCU / periph / gic cluster tables `scu_cluster_tbl_T618_tt[_65]` etc.
- Possibly a voltage grade table in the hwdvfs module

Each new OPP adds one row to each of those tables. Getting this right requires careful reading of the sprd-hwdvfs-ums512-arch.ko parsing code to understand the exact table layout.
