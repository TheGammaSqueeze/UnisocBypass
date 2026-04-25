# 020 - GPU OC 900 MHz (smallest bump, stock voltage/hw_index)

First GPU OC attempt. Replaces stock top OPP 850 MHz with 900 MHz, keeping
- hw_index 8 (stock top OPP hardware slot)
- voltage 800 mV DT value (GPU DT voltage is known not to actually change vddgpu)

Goal: determine whether GPU freq is a DT-driven clock setting or whether it
is hardware-locked at each hw_index.

DT changes:
- operating-points: last OPP 0xcf850 -> 0xdbba0 (850 -> 900 MHz)
- sprd,dvfs-lists: corresponding quad updated
- No trip, no CPU change.
