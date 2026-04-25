# 014 - Reproducibility: CPU UV -37.5 mV x 3 runs

Re-run the winning config (exp 008: CPU UV -37.5 mV, GPU UV -25 mV) three
times with a full reboot between runs, to validate that the +22% cpu-only
and +9% both-mode perf deltas are reproducible and not run-to-run noise.

Each run executes all 3 bench modes (cpu, gpu, both) for 180 s, with a
reboot between runs (not between modes within a run).

Structure:
- run1/{cpu,gpu,both}/raw
- run2/{cpu,gpu,both}/raw
- run3/{cpu,gpu,both}/raw
