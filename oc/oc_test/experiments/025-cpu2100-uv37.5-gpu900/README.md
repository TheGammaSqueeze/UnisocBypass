# 025 - Combined stable OC: CPU UV -37.5 + OC 2100 + GPU OC 900

## Purpose

Daily-driver DTB that bundles every independently-verified knob:

| Change | Evidence |
|--------|----------|
| CPU lower OPPs UV -37.5 mV | exp 008, exp 014 (3x reproducibility) stable |
| CPU top OPP 2002 -> 2100 MHz, stock volt target | exp 019 stable both mode |
| GPU top OPP 850 -> 900 MHz, stock volt target | exp 020 +17% FPS, stable |
| Stock thermal trips | exp 015, exp 017 showed raised trips crash |
| No voltage overvolt | Rails cap around stock; overvolt DT values don't apply |

This experiment does NOT break new ground. It composes prior winning configs
into a single vendor_boot.img for daily use.

## DT changes vs stock

- CPU LITTLE cluster top OPP: `0x1e8c50 0xe7ef0` -> `0x200b20 0xe7ef0`
  (2002 MHz @ 1050 mV -> 2100 MHz @ 1050 mV)
- CPU LITTLE cluster lower OPPs: each voltage -37.5 mV (756.25 -> 718.75 etc)
- CPU BIG cluster top OPP: same freq bump
- CPU BIG cluster lower OPPs: same UV
- GPU operating-points top: `0xcf850 0xc3500` -> `0xdbba0 0xc3500`
  (850 MHz @ 800 mV -> 900 MHz @ 800 mV)
- GPU sprd,dvfs-lists top entry: 850 -> 900 MHz, hw_index still 8

## Expected outcome

Cumulative vs stock:
- CPU throughput: no change at 2002 MHz (we run 2100), modest gain at top OPP
- GPU throughput: +17% at top (900 vs 850 MHz)
- CPU peak temp: -5 to -8 C from UV reducing power at mid OPPs
- Overall thermal headroom in both mode should give slightly less throttling
