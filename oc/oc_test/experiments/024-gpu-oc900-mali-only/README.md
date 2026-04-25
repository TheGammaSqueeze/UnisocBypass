# 024 - Try mali-supply only (no shadercores-supply)

## Motivation (from exp 023 results)

Exp 023 added both `mali-supply = <0x0a>` and `shadercores-supply = <0x0a>`
pointing to DCDC_GPU. Both phandles the same. Under gpu mode stress at 900 MHz,
rail stayed at 800 mV (unchanged from exp 022). Under both mode, rail bounced
between 700 and 800 mV, avg 710 mV, worse than 800 baseline.

Hypothesis: two consumer regulator handles on the same physical rail conflict.
Mali's `kbase_devfreq_target` iterates `for i in range(num_regulators)` and
calls `regulator_set_voltage(regulators[i], new_voltage[i])`. With shadercores
pointing to the same DCDC_GPU, the second call may write a different voltage
(e.g., 700 mV for idle shadercores) that overrides the first.

Remove shadercores-supply. num_regulators becomes 1. Only one regulator_set_voltage
call per OPP transition on DCDC_GPU.

## DT changes vs stock

- operating-points top OPP: 850 MHz @ 800 mV -> 900 MHz @ 850 mV (same as 021, 023)
- sprd,dvfs-lists top entry updated accordingly
- GPU node: add `mali-supply = <0x0a>;` (not shadercores-supply)

## Expected outcome

If the conflict hypothesis is right: rail should go to 850 mV under gpu mode stress.

If still 800 mV: the problem is elsewhere (Mali driver doesn't call
regulator_set_voltage, or the call fails silently for other reasons).
