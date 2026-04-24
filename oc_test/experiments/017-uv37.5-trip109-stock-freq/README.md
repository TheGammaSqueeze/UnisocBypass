# 017 - UV -37.5 mV + trip 109 C (safe revert after 2100 MHz crash)

Exp 016 (CPU OC 2100 MHz) crashed device twice in both-mode stress.
Per user direction: revert CPU to stock 2002 MHz, keep UV -37.5 mV, and
lower thermal trips from 115 C to 109 C for a safer operating envelope.

DT changes:
- CPU UV -37.5 mV (operating-points and T618-tt/etc)
- Freq stock 2002 MHz
- soc passive trip: 85 C -> 109 C
- soc_crit: 110 C -> 119 C
- cluster0/1 max-temp: 90/85 C -> 109 C

Expected: all 3 modes complete stably. Lower trip + no OC = same conditions
as exp 014 repro minus the 109 C safety envelope.
