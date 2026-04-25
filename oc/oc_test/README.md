# Overclock / undervolt experiments

Directory layout for OC/UV experiments on the RG Vita (UMS512 / T618).

## Structure

```
oc_test/
├── README.md                this file
├── CHANGELOG.md             chronological log of experiments and outcomes
├── gpu_stress.c             GLES 3.1 fragment-shader stressor source
├── gpu_stress               compiled ARM64 binary (pushed to device)
├── torture_test.sh          on-device test harness (CPU+GPU full load)
├── gpu_only_test.sh         on-device test harness (GPU load, CPUs low)
├── tools/
│   └── modify_dtb.py        generic DTB modifier helpers
└── experiments/
    ├── 000-stock-baseline/  reference data at stock OPPs
    ├── 001-*/               each experiment self-contained
    └── 002-*/
```

Each experiment directory contains:

- `README.md` - hypothesis, target, DTB modifications, flash method, notes
- `modify.py` - the DTB modification script (reproducible)
- `raw/` - test telemetry, GPU stress log, iteration counts
- `REPORT.md` - summary of results with peak temps, throttling stats, FPS
- `vendor_boot.img.signed.sha256` - hash of the image that was flashed (for provenance)

## Running a new experiment

1. Copy a prior experiment directory as a template:
   ```
   cp -r experiments/000-stock-baseline experiments/00N-short-name
   ```
2. Edit `modify.py` to describe the DTB changes.
3. Run `modify.py` to produce `/tmp/editor_modified.dts`, compile back to DTB,
   wrap in multi-DTB, place in `android_boot_image_editor/build/unzip_boot/dtb`,
   run `./gradlew pack`, record the `vendor_boot.img.signed` sha256.
4. Flash, reboot, verify with `adb shell getprop sys.boot_completed`.
5. Run the torture test or gpu-only test on device.
6. Pull results into `raw/`.
7. Generate `REPORT.md`.
8. Update the top-level `CHANGELOG.md`.
9. Commit the experiment directory.

## Test harnesses

- `torture_test.sh 180 <log_dir>` - locks CPU clusters to 2002 MHz via
  `scaling_fix_freq` and GPU to 850 MHz `performance` governor. Spawns 8
  pinned sha256sum loops and the GLES stressor. Samples all thermal zones +
  current frequencies every 1 s.
- `gpu_only_test.sh 180 <log_dir>` - pins CPU policy0 to 614.4 MHz and
  policy6 to 1228.8 MHz, GPU to 850 MHz. GPU-only workload. Useful for
  isolating GPU thermal contribution when the chassis is not saturated by
  CPU power draw.

## Known constraints

1. GPU OPPs are used by the hardware DVFS via BOTH `operating-points` AND
   `sprd,dvfs-lists`. Modifying one without the other leaves the hardware
   table inconsistent. Always update both.
2. CPU OPPs have a parallel per-cluster mapping table
   (`lit_core_cluster_tbl_T618_tt`, `big_core_cluster_tbl_T618_tt`,
   `scu_cluster_tbl_T618_tt`, etc.) that maps OPP index to voltage / SCU /
   periph / GIC indices. Adding CPU OPPs requires extending these tables too.
3. Device bricks on bad DTB are recoverable via the CVE-2022-38694 unsigned
   FDL flow (see repo-level `fdl/README.md`).
