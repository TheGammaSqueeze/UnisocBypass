# 015 - UV -37.5 mV + thermal trip 115 C (stock freq)

Base step for OC: validate that raising thermal trip + keeping CPU UV is boot-stable.
DT changes:
- CPU LITTLE/BIG UV -37.5 mV (operating-points)
- soc passive trip: 85 C -> 115 C
- soc_crit: 110 C -> 125 C
- cluster0 max-temp: 90 C -> 115 C
- cluster1 max-temp: 85 C -> 115 C
- CPU freq: stock 2002 MHz max

Hypothesis: no functional change in stress behaviour; validates mechanism before
attempting CPU OC.
