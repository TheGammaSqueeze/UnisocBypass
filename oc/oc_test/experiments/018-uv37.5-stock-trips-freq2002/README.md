# 018 - UV -37.5 mV + stock 2002 MHz freq + stock trips (control)

Exp 017 (UV + trips 109 C, stock freq) crashed cpu mode. Removing trip changes
to isolate whether trip modifications themselves destabilise the device.

DT changes:
- CPU UV -37.5 mV (stock operating-points modified)
- No thermal trip changes
- Freq stock 2002 MHz

This is functionally identical to exp 014 repro (which was stable). Confirming
the repro is still stable is a prerequisite for OC attempts.
