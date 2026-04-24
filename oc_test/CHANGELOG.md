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
2. **GPU voltage does NOT respond to DTB changes.** The Mali-G52 driver uses Unisoc's hardware DVFS register path driven by `sprd,dvfs-lists` hw_index slots, not the Linux regulator framework. Modifying `operating-points` and `sprd,dvfs-lists` voltages in the DT has no observable effect at the regulator level.
3. **Stock vddcpu runtime < stock DT voltage** in some cases (observed 1009 mV at 2002 MHz during exp 007, vs DT 1050 mV). Suggests adaptive voltage scaling (AVS) in the HW DVFS path actively trims CPU voltage below the DT ceiling.
4. **Safe UV range**: CPU UV -25 mV verified stable. GPU UV in DT does not apply at all so there is no "safe" range yet; that requires modifying the HW DVFS path (not the DT).
5. **Thermal envelope during `both` torture is dominated by CPU power.** GPU-only tests stay under 70 C. CPU-only tests hit 106 C. Combined tests still hit 106 C with heavy GPU throttling.

## Planned next

- Re-run CPU UV (-25 and -37.5 mV) using bench_test.sh in all three modes, to quantify how much CPU UV actually helps CPU-only and both-mode thermals.
- Investigate GPU voltage table: find the actual node in DT (or in a kernel driver) that controls the HW DVFS voltage indices. Candidates: `mpll-prometheus`, `mpll-ananke`, or a separate voltage-grade mapping. Without touching this path, GPU UV via DTB is a no-op.
- Once CPU UV value space is mapped out, attempt CPU OC again with proper cluster table extension.
