# OC/UV experiment changelog

Chronological log of DTB experiments on the RG Vita (UMS512 / T618). One row per test, most recent first.

| # | Date | Config | Test | GPU avg MHz | GPU throttled % | SoC peak | FPS last 10 s | Outcome |
|---|------|--------|------|------------:|----------------:|---------:|--------------:|---------|
| 003 | 2026-04-24 | GPU UV -25 mV all | GPU-only, CPUs low | **850** | 0 % | 66 C | 16.45 | stable at 850 MHz for 180 s |
| 002 | 2026-04-24 | GPU UV -25 mV all | CPU+GPU torture | 506 | 75 % | 106 C | 7.52 | no benefit (CPU-dominated thermals) |
| 001 | 2026-04-24 | GPU UV top -12.5 mV | CPU+GPU torture | 499 | 75 % | 102 C | 7.52 | no measurable benefit |
| 000 | 2026-04-23 | stock | CPU+GPU torture | 517 | 71 % | 102 C | 7.56 | baseline |

## Bricked attempts (recovery needed)

| attempt | config | failure mode |
|---------|--------|--------------|
| brick-01 | CPU OC 2002->2100 MHz + 1050->1075 mV on T618 variants + GPU UV -50 mV | no boot - cluster mapping tables not extended |
| brick-02 | GPU UV -50 mV all OPPs (650/700/750 mV) | no boot - voltage too aggressive or UV regions mismatched with cluster tables |
| brick-03 | in-place DTB replace (no editor repack) at various voltages | no boot - in-place replace missed an AVB / size field somewhere |

## Lessons learned

1. **Always round-trip through `android_boot_image_editor`**, not in-place DTB replace. The editor handles AVB + header padding correctly.
2. **GPU DTB has paired tables**: `operating-points` and `sprd,dvfs-lists`. Both must be updated consistently.
3. **Torture test with all 8 cores at max is NOT sensitive to GPU UV.** The CPU-driven heat dominates the thermal picture. Use `gpu_only_test.sh` to isolate GPU thermal behavior when evaluating UV.
4. **CPU OC requires extending per-cluster mapping tables** (`lit_core_cluster_tbl_T618_tt`, `big_core_cluster_tbl_T618_tt`, `scu_cluster_tbl_T618_tt`, etc.). Just adding a row to `operating-points-T618-tt` is not sufficient.
5. **Safe UV range** so far: -25 mV across all GPU OPPs verified stable. -50 mV bricks. Cliff is somewhere between.

## Planned next

- Experiment 004: GPU UV -37.5 mV all OPPs (midpoint between known-safe -25 and known-cliff -50).
- Experiment 005+: CPU OC via full cluster-table extension, once hwdvfs table layout is fully reverse-engineered.
