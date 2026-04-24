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

**Current baseline: exp 025** (CPU UV -37.5 mV + CPU OC 2100 MHz + GPU OC 900 MHz, stock voltage targets, stock thermal trips). See `experiments/025-cpu2100-uv37.5-gpu900/`.

| # | date | dtb config | mode | samples | CPU avg MHz | GPU avg MHz | SoC peak C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | notes |
|---|------|-----------|------|-------:|------------:|------------:|-----------:|----------:|----------:|--------:|--------:|-------|
| **025-cpu** | 2026-04-24 | CPU UV -37.5 + CPU OC 2100 + GPU OC 900 | cpu | 109 | 2100 | 384 | 102.1 | 1050 | 700 | 78.9 | 0.00 | **BASELINE** +18.6% CPU |
| **025-gpu** | 2026-04-24 | CPU UV -37.5 + CPU OC 2100 + GPU OC 900 | gpu | 129 | 1228 | 900 | 63.1 | 719 | 799 | 0.0 | 16.26 | **BASELINE** +17% FPS vs stock 850 MHz |
| **025-both** | 2026-04-24 | CPU UV -37.5 + CPU OC 2100 + GPU OC 900 | both | 70 | 2100 | 472 | 105.0 | 1050 | 717 | 57.7 | 8.21 | **BASELINE** -0.8 C vs stock |
| 024-gpu | 2026-04-24 | GPU 900 MHz + mali-supply only (no shadercores) | gpu | 130 | 1228 | 900 | 64.4 | 756 | 800 | 0.0 | 16.25 | cap still 800 mV, mali-supply alone didn't help |
| 023-gpu | 2026-04-24 | GPU 900 MHz + mali-supply + shadercores-supply | gpu | 128 | 1228 | 900 | 64.4 | 756 | 800 | 0.0 | 16.26 | cap still 800 mV |
| 022 (partial) | 2026-04-24 | GPU 900 MHz + operating-points volt 1000 mV | ad-hoc | - | - | 900 | - | - | 800 | - | - | definitive: even 1000 mV DT request, rail stuck at 800 mV |
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

## Key findings (updated 2026-04-24 post exp 025)

1. **CPU UV via DT DOES apply.** UV in `operating-points-T618-tt` reaches DCDC_CPU via the regulator framework. -37.5 mV verified stable in exp 008/014 (3x reproducibility). -25, -50, -62.5, -75, -87.5, -100 mV all tested; -37.5 is the sweet spot for thermal gain without instability.
2. **CPU OVERVOLT above ~1050 mV does NOT apply.** Exp 019 asked for 1075 mV at 2100 MHz; rail still reads 1009-1050 mV. The ceiling is the stock top voltage for this chip bin.
3. **CPU OC to 2100 MHz is stable at stock voltage.** Exp 019 and exp 025 ran it stably in all 3 modes. No overvolt needed because none applies anyway.
4. **GPU voltage changes via DT do NOT apply.** Rail hard-capped at 800 mV regardless of DT request. Verified with 850 mV (exp 021), 1000 mV (exp 022), and with / without mali-supply/shadercores-supply DT injection (exp 023, 024).
5. **Mali driver DOES read DT voltage** (`dmesg` shows `volt=850000` in the transition log) but the rail stays at 800 mV. Between `dev_pm_opp_get_voltage()` and the SC2730 vsel register, something discards the change. The exact mechanism is unidentified; likely boot-time PMIC programming in SPL or ATF.
6. **GPU voltage bypass exists**: writing to `/sys/kernel/debug/DCDC_GPU/voltage` calls `set_voltage_sel_regmap` directly and succeeds. Rail holds at 850 mV across Mali OPP transitions. Would require a userspace daemon to ship.
7. **GPU freq via DT DOES apply.** 900 MHz confirmed under load in exp 020 and exp 025, +17% FPS vs stock 850 MHz.
8. **Thermal trip DT changes crash the thermal framework.** Exp 015 (115 C trip) and exp 017 (109 C trip) both crashed even at stock frequencies. Keep trips stock.
9. **Adding extra CPU OPPs bricks boot.** Safer to REPLACE the top OPP freq in place (e.g., 2002 -> 2100) than to add a new row.

## Planned next

- **Push CPU higher** (2150, 2200 MHz) without overvolt (it doesn't apply anyway) to find the stability ceiling at stock 1050 mV.
- **Push GPU higher** via DT freq increase + userspace voltage override (write to `/sys/kernel/debug/DCDC_GPU/voltage`) as part of the OS init. Test 950, 1000 MHz with 850 mV forced.
- **SPL / ATF RE pass** to locate where PMIC voltage grade values are programmed at boot (only remaining candidate for a proper kernel-side voltage ceiling fix).
