# 022 - GPU OC 900 MHz with aggressive operating-points overvolt to 1000 mV

## Purpose

Exp 021 raised operating-points to 850 mV but rail stayed at 800 mV. Exp 022
pushes to 1000 mV to definitively prove that DT operating-points voltage
changes are IGNORED by whatever actually programs vddgpu.

## DT changes vs stock

- operating-points top OPP: 850 MHz @ 800 mV -> 900 MHz @ 1000 mV (0xdbba0 0xf4240)
- sprd,dvfs-lists top entry: 900 MHz @ 1000 mV

## Outcome

**DT path definitively insufficient for GPU voltage.**

Device booted fine. Manual test under gpu_stress at forced 900 MHz:
- Mali dmesg: `mali GPU_DVFS kbase_platform_set_freq_volt index=4 cur_freq=768000 cur_volt=700000 --> freq=900000 volt=1000000`
- Actual vddgpu rail: 800 mV
- DCDC_GPU debugfs read: 800 mV

So even requesting 1000 mV via DT, the rail is hard-capped at 800 mV.

## Breakthrough test

With GPU stressed and rail stuck at 800 mV, writing directly to
`/sys/kernel/debug/DCDC_GPU/voltage` = 850 mV DID succeed:
- rail immediately went to 850 mV
- held at 850 mV through Mali OPP transitions (900 -> 768 -> 900 MHz)

This proved:
1. The SC2730 PMIC CAN deliver 850 mV on DCDC_GPU
2. The regulator framework writes DO reach hardware when called via
   `set_voltage_sel_regmap` (what debugfs uses)
3. Something in the Mali path between `dev_pm_opp_get_voltage()` and the
   actual SC2730 vsel register write is either failing silently or being
   overridden

## Note

This experiment did not produce telemetry CSVs for the 3 bench modes; the
run script was accidentally piped through `| head -5` which severed the
pipe and killed the iteration after pack but before the bench modes.
DTB flash still succeeded (verified via /proc/device-tree read). The
manual test captured the key finding above.
