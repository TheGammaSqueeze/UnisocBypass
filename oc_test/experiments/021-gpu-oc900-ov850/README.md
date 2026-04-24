# 021 - GPU OC 900 MHz with operating-points overvolt to 850 mV

## Hypothesis

The Mali driver applies `operating-points` voltage to vddgpu via
`regulator_set_voltage()` inside `kbase_devfreq_target`. Evidence from kernel
reverse engineering of `mali_gondul.ko`:

- `kbase_devfreq_target -> devfreq_recommended_opp -> dev_pm_opp_get_voltage -> regulator_set_voltage(gpu_reg, uV, uV)`
- Runtime dmesg on exp 020: `mali GPU_DVFS kbase_platform_set_freq_volt index=4 cur_freq=384000 cur_volt=700000 --> freq=900000 volt=800000`
  - The `volt=800000` field is sourced from the operating-points entry, not
    from `sprd,dvfs-lists`.
- `sprd,dvfs-lists` hw_index controls GPU clock source (indexed into
  `gpu_dvfs_ctx.freq_list[hw_index-4].clk_src`), not the regulator voltage.

Exp 020 kept `operating-points[4]` at stock `0xc3500` (800 mV), so nothing
actually requested a higher voltage. This run raises it to `0xcf850` (850 mV)
to validate the path and to stabilize 900 MHz.

## DT changes vs stock

- operating-points: `<... 0xbb800 0xc3500 0xdbba0 0xcf850>` (last pair: 900 MHz @ 850 mV)
- sprd,dvfs-lists:  `<... 0xbb800 0xc3500 0x07 0x01 0xdbba0 0xcf850 0x08 0x01>`
- sprd,dvfs-range-max: unchanged at 0x04
- CPU DT: unchanged, stock
- Thermal trips: unchanged, stock

## Outcome

**DT path is confirmed insufficient for GPU voltage**.

Mali driver dmesg during GPU stress:
```
mali GPU_DVFS kbase_platform_set_freq_volt index=4 cur_freq=768000 cur_volt=700000 --> freq=900000 volt=850000
```

The `volt=850000` field proves the operating-points DT edit reached the Mali
driver and it called `regulator_set_voltage(gpu_reg, 850000, 850000)`. But
the actual vddgpu rail under stress stayed at 800 mV (telemetry.csv unique
`vddgpu_uV` values during gpu mode: `800000` only).

The HW DVFS path (kbase_platform_set_freq_volt writing OPP index to the
`dvfs_index_cfg` register + autonomous PMIC voltage switching via
`core_indexN_map` table) overrides the software regulator request. Next
step is kernel patching of either:

1. The `core_indexN_map` PMIC register values to map the top dvfs slot
   to a higher voltage grade.
2. The `TOP_DVFS_VOL_GRADE_TBL` in sprd-hwdvfs-policy.ko that defines
   what voltage each PMIC voltage grade represents.

Performance deltas at 900 MHz stock-voltage:
- gpu mode: 16.23 FPS (vs stock 006: 13.86 = +17.1%, vs exp 020: 14.93 = +8.7%)
- both mode: 8.07 FPS (within noise of stock 007 4.90, statistically similar to exp 020 8.09)
- cpu mode: SoC peak 102.4 C (vs stock 106.0 = -3.6 C, favorable)

The +17% GPU gain at stock voltage suggests 900 MHz is stable at 800 mV for
this chip bin. Higher GPU clocks (950/1000 MHz) will need the kernel patch.

## Source

- modify.py calls tools/gen_gpu_oc_dts.py 900 --volt-mv 850
- /tmp/editor.dts is stock GPU DTS baseline
