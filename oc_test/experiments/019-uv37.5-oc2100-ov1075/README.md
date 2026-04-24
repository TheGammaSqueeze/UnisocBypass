# 019 - UV -37.5 mV lower OPPs + OC 2100 MHz @ 1075 mV (overvolt)

Second OC attempt. Exp 016 (2100 @ 1012.5 mV) crashed both-mode twice.
Silicon likely needed more voltage at 2100 than stock 2002 needs at 1050.
Giving top OPP stock+25 mV = 1075 mV to provide stability margin.

DT changes:
- CPU LITTLE/BIG lower OPPs (OPPs 0..N-2) UV'd -37.5 mV
- CPU LITTLE/BIG top OPP: 2002 MHz @ 1050 mV -> 2100 MHz @ 1075 mV
- Stock thermal trips (85 C passive, 110 C crit) - exp 017 showed DT trip
  changes destabilise thermal framework, so we leave stock.

Expected: 2100 MHz stable in all 3 modes including both. If yes, iterate to
2150 / 2200 with further voltage bumps.
