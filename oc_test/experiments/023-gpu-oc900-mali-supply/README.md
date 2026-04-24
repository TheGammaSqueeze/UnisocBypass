# 023 - GPU OC 900 MHz, fix Mali regulator binding

## Root cause (identified in exp 022)

Mali driver's `power_control_init` calls `regulator_get_optional(dev, "mali")`
and `regulator_get_optional(dev, "shadercores")`. The GPU DT node only has
`gpu-supply = <0x0a>`, not `mali-supply` or `shadercores-supply`. So Mali
gets no regulator handle, `num_regulators = 0` is stored at `kbdev+0xd0`,
and `kbase_devfreq_target`'s per-regulator voltage loop never executes.
`regulator_set_voltage()` is never called for DCDC_GPU.

The Mali dmesg `volt=850000` print comes from `kbase_platform_set_freq_volt`
which just reads `dev_pm_opp_get_voltage()` from the DT and prints it,
regardless of whether the regulator call happened.

The 800 mV rail value is whatever SPL/uboot programmed at boot. HW DVFS
does not override it (verified in exp 022: writing 850 mV via
`/sys/kernel/debug/DCDC_GPU/voltage` held at 850 mV even across Mali OPP
transitions, because the debugfs write calls `set_voltage_sel_regmap`
directly, bypassing consumer constraints).

## DT changes vs stock

- operating-points top OPP: 850 MHz @ 800 mV -> 900 MHz @ 850 mV
- sprd,dvfs-lists top entry: 850 MHz -> 900 MHz (with 850 mV, hw_index 8)
- GPU node: add `mali-supply = <0x0a>;` and `shadercores-supply = <0x0a>;`
  alongside existing `gpu-supply = <0x0a>` (all three point to DCDC_GPU)

## Expected outcome

Mali driver acquires DCDC_GPU as "mali" regulator. When OPP 4 (900 MHz)
activates, `regulator_set_voltage(gpu_reg, 850000, 850000)` goes through
the regulator framework, reaches SC2730 regulator's
`regulator_set_voltage_sel_regmap`, writes vsel register. Rail reads
850 mV under stress.

If it works, we have real GPU voltage control via DT and can push
900/950/1000 MHz with matched voltage.

## Source

- modify.py edits /tmp/editor.dts (stock) to inject 900 MHz @ 850 mV plus
  mali-supply/shadercores-supply. Both supplies use the same phandle 0x0a
  (DCDC_GPU) since the GPU is a single voltage domain.
