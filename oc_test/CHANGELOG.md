# OC/UV experiment changelog

Chronological log of bench/torture tests on the RG Vita (UMS512 / T618). Most recent first.

Each experiment lives in `experiments/NNN-short-name/` with `README.md`, `modify.py`, `modified.dts`, `raw/`, `REPORT.md`, and `vendor_boot.img.signed.sha256`.

## Test modes

Starting with experiment 005, all tests run via `bench_test.sh <mode>`:

- `cpu` - 8 cores at 2002 MHz stress, GPU pinned at 384 MHz idle
- `gpu` - GPU at 850 MHz stress, CPU policies pinned to min (LITTLE 614.4 / BIG 1228.8)
- `both` - concurrent CPU + GPU stress, equivalent to the legacy torture test

Every run includes a pre-test OPP voltage sweep recorded to `opp_voltage_sweep.csv`, so the actual regulator voltage at each OPP is evidence that DTB changes reached the hardware.

## Comparison table

| # | date | dtb config | mode | samples | CPU avg MHz | GPU avg MHz | SoC peak C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | notes |
|---|------|-----------|------|-------:|------------:|------------:|-----------:|----------:|----------:|--------:|--------:|-------|
| 021-cpu | 2026-04-24 | GPU OC 900 MHz + operating-points volt 850 mV | cpu | 98 | 2002 | 384 | 102.4 | 1050 | 700 | 73.2 | 0.00 | iteration step (CPU unchanged) |
| 021-gpu | 2026-04-24 | GPU OC 900 MHz + operating-points volt 850 mV | gpu | 129 | 1228 | 900 | 64.7 | 756 | 800 | 0.0 | 16.23 | Mali logs volt=850000, rail clamped at 800 mV |
| 021-both | 2026-04-24 | GPU OC 900 MHz + operating-points volt 850 mV | both | 66 | 2002 | 452 | 105.5 | 1050 | 712 | 56.1 | 8.07 | DT OV rejected at HW DVFS layer |
| 020-cpu | 2026-04-24 | GPU OC 900 MHz stock volt | cpu | 71 | 2002 | 384 | 106.3 | 1050 | 700 | 57.2 | 0.00 | iteration step |
| 020-gpu | 2026-04-24 | GPU OC 900 MHz stock volt | gpu | 101 | 1228 | 900 | 63.6 | 756 | 800 | 0.0 | 14.93 | 900 MHz freq applies from DT |
| 020-both | 2026-04-24 | GPU OC 900 MHz stock volt | both | 68 | 2002 | 458 | 105.5 | 1050 | 712 | 56.7 | 8.09 | iteration step |
| 008-cpu | 2026-04-24 | CPU -37.5 mV + GPU -25 mV | cpu | 114 | 2002 | 384 | 98.8 | 1012 | 700 | 81.2 | 0.00 | iteration step |
| 008-gpu | 2026-04-24 | CPU -37.5 mV + GPU -25 mV | gpu | 129 | 1228 | 850 | 61.0 | 719 | 799 | 0.0 | 16.26 | iteration step |
| 008-both | 2026-04-24 | CPU -37.5 mV + GPU -25 mV | both | 86 | 2002 | 482 | 105.5 | 1012 | 720 | 65.8 | 8.56 | iteration step |
| 007 | 2026-04-24 | stock | both | 76 | 2002 | 588 | 106.8 | 1009 | 700-800 | 12.9 | 4.90 | stock baseline, both stress |
| 006 | 2026-04-24 | stock | gpu | 39 | 1228 | 850 | 68.5 | 762 | 800 | n/a | 13.86 | stock baseline, GPU-only |
| 005 | 2026-04-24 | stock | cpu | 135 | 2002 | 384 | 106.0 | 1050 | 700 | 20.0 | n/a | stock baseline, CPU-only |
| 004 | 2026-04-24 | GPU UV -37.5 + CPU UV -25 | both | 96 | 2002 | 525 | 102.9 | 1025 | 700-800 | - | 9.4 | CPU UV landed (1025 mV), GPU UV did NOT land (vddgpu unchanged) |
| 003 | 2026-04-24 | GPU UV -25 | gpu | 149 | 1228 | 850 | 66.1 | - | - | n/a | 16.41 | UV booted but vddgpu hardware unaffected |
| 002 | 2026-04-24 | GPU UV -25 | both (legacy) | 95 | 2002 | 506 | 106.3 | - | - | - | 8.86 | legacy torture, pre-voltage-sampling harness |
| 001 | 2026-04-24 | GPU UV top -12.5 | both (legacy) | 112 | 2002 | 499 | 101.9 | - | - | - | 9.22 | legacy torture |
| 000 | 2026-04-23 | stock | both (legacy) | 109 | 2002 | 517 | 102.1 | - | - | - | 9.56 | legacy torture baseline (supplanted by 007) |

## Bricked attempts

| attempt | config | failure mode |
|---------|--------|--------------|
| brick-01 | CPU OC 2002->2100 MHz + voltage 1050->1075 mV | no boot (cluster mapping tables not extended) |
| brick-02 | GPU UV -50 mV all OPPs | no boot (voltage too aggressive or tables mismatched) |
| brick-03 | in-place DTB replace (no `android_boot_image_editor` repack) | no boot (header field or AVB footer integrity) |

## Key findings so far

1. **CPU voltage responds to DTB changes.** UV applied in the `operating-points-T618-tt` table reaches the SC2730 DCDC_CPU regulator via the standard Linux regulator framework. Verified in exp 004: vddcpu @ 2002 MHz dropped from stock 1009-1050 mV to 1025 mV when DT was changed from 1050 to 1025.
2. **GPU voltage does NOT respond to DTB changes, and exp 021 pinpoints why.** The Mali driver reads `operating-points` voltage and calls `regulator_set_voltage(850000)` when the DT asks for 850 mV (confirmed via Mali dmesg: `volt=850000` in `kbase_platform_set_freq_volt`). But the HW DVFS mechanism writing to `dvfs_index_cfg` + `core_indexN_map` autonomously sets vddgpu per its own voltage grade table, overriding the software regulator request. Rail stays at 800 mV for the top OPP regardless of DT.
3. **GPU freq DOES respond to DT.** Exp 020 raised the top OPP from 850 to 900 MHz via operating-points/sprd,dvfs-lists and the GPU ran at 900 MHz under load. So freq-only OC works; voltage changes require kernel patching.
4. **Kernel patch target**: either `core_indexN_map` register values in DT (which drive PMIC writes), or the voltage grade table in `sprd-hwdvfs-policy.ko` / `sprd-hwdvfs-ums512-arch.ko` (strings: `TOP_DVFS_VOL_GRADE_TBL`, `ums512_volt_grades_tbl`, `sprd_voltage_grade_value_update`).
5. **Stock vddcpu runtime ~= stock DT voltage** - no AVS floor; rail follows DT. Earlier "1009 mV" readings were just averaging across 1009/1050 mV transitions between freq changes.
6. **Safe UV range**: CPU UV -37.5 mV verified stable in exp 008/014. GPU UV via DT is a no-op.
7. **Thermal envelope during `both` torture is dominated by CPU power.** GPU-only tests stay under 70 C. CPU-only tests hit 106 C. Combined tests still hit 106 C with heavy GPU throttling.

## Planned next

- **Patch GPU voltage path in kernel**: locate hw_index-to-voltage binding in `sprd-hwdvfs-policy.ko` (strings point to `TOP_DVFS_VOL_GRADE_TBL`, `ums512_volt_grades_tbl`, `sprd_voltage_grade_value_update`, `default_dcdc_volt_update`). Target: raise voltage grade 4 (top OPP) from 800 to 850 mV, enabling stable 950+ MHz OC.
- **Patch CPU voltage path**: the CPU uses a separate `sprd-hwdvfs-ums512-arch.ko` with cluster tables (`lit_core_cluster_tbl_T618_tt`, `big_core_cluster_tbl_T618_tt`). Adding a 2100+ MHz entry requires extending these tables, not just operating-points.
- Re-check vendor_boot/SPL for voltage grade registers programmed at boot (unlikely per earlier SPL RE, but worth confirming).
