# RG Vita (UMS512 / T618) overclock & undervolt research

This is a separate workstream from the firmware-signing-bypass research in
the parent repo. It explores how far the CPU and GPU can be pushed via
DTB modifications and kernel patches, and tries to characterise the real
performance gain.

**Bottom line: the achievable performance gain is small** (about
**+1.5 %** real GPU throughput from the 850 -> 900 MHz OC, validated
under a 600-second torture run). Earlier reports of `+17 %` were
artefacts of short benches with cold-start variability, and have been
retracted.

The research is left here as a record so the next person doesn't repeat
the dead ends.

## Layout

| Path | What's in it |
|------|--------------|
| [`oc_test/`](oc_test/) | All 25+ DTB experiments (`experiments/NNN-*/`), with three-mode bench output, `modify.py`, `modified.dts` and `vendor_boot.img.signed.sha256`. Top-level `CHANGELOG.md` and `COMPARISON.md` summarise. |
| [`torture_2026-04-25/`](torture_2026-04-25/) | 600-second, single-pin torture comparing exp 025 (900 MHz) vs stock (850 MHz). The CSVs underpin the +1.5 % number above. |
| [`voltage-ceiling-hunt/`](voltage-ceiling-hunt/) | The full chain of analysis - SPL/uboot scans, ftrace + kprobe of the regulator path, decoded GPU voltage-grade table at top DVFS controller offsets `0xe4`/`0xe8`, and the kernel-module-loading attempt that made it past sig_enforce but couldn't break Mali's clock-on rewrite. |
| [`kernel_rev/`](kernel_rev/) | Vendor kernel modules pulled from `/vendor_dlkm` for offline RE. |
| [`OC_FEASIBILITY.md`](OC_FEASIBILITY.md) | First-pass survey of where DVFS lives in the boot chain. |

## Headline numbers (corrected)

All numbers are from 600-second torture runs, identical methodology,
30-second cool-down before each run.

### GPU (gpu_stress headless GLES 3.1 fragment shader, 1280x720, CPU at min)

| Config | Mean FPS | Median | Stddev | p1 | p99 | GPU MHz | SoC peak |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stock 850 MHz | 16.247 | 16.40 | 0.497 | 14.10 | 16.60 | 850 (100 %) | 62.8 C |
| exp 025 900 MHz | 16.502 | 16.50 | 0.071 | 16.40 | 16.70 | 900 (100 %) | 61.3 C |

- Pure freq scaling would predict +5.88 %.
- Observed: **+1.57 %**.
- Stock has 11.6 % of frames below 16 FPS (down to 13.8) due to
  system-side jitter (kworker, allocations) - not thermal throttling.
  exp 025 has 0 % such dips. So the OC's real value is **stability**,
  not raw throughput.

### CPU (8 sha256sum workers via taskset, GPU at min)

| Config | Throughput | Total work / 598s | LITTLE 1820 MHz residency | BIG 1228 MHz residency | Board peak |
|---|---:|---:|---:|---:|---:|
| Stock 2002 MHz pinned | 158.3 MiB/s | 92.42 GiB | 69.6 % | 83.2 % | 91.5 C |
| OC 2100 MHz pinned (run 1) | 150.8 MiB/s | 88.06 GiB | 48.1 % | 85.2 % | **95.2 C** |
| OC 2100 MHz pinned (run 2) | 158.8 MiB/s | 92.76 GiB | 70.2 % | 79.8 % | 91.5 C |

- Pure freq scaling 2002 -> 2100 would predict +4.90 %.
- Observed (run 1): -4.74 %.
- Observed (run 2, same config): **+0.32 %** vs stock. Within noise.
- Run 1 was run back-to-back after the stock test with insufficient
  cool-down. The chip started already warm, hit the throttle threshold
  earlier, and spent more time at lower frequencies (LITTLE 48 % at 1820
  vs stock 70 %; 10 % at 1228 vs stock 0.2 %). With a longer cool-down,
  run 2 reproduces stock residency (LITTLE 70 % at 1820, BIG 80 % at
  1228) and converges to identical sustained throughput. The "-4.72 %"
  from run 1 was a thermal-state artefact, not a property of the OC.
- **Honest conclusion: under sustained all-core load, the CPU OC delivers
  zero additional throughput.** Both stock and OC saturate the same
  thermal budget and end up dispatched to the same effective frequencies.
  The 2100 MHz top OPP is reached in <0.5 % of samples either way.
- The OC is not a *regression* either, just a no-op at sustained load.
  It may still help short bursty workloads that finish before the chip
  saturates (sub-30s tasks). For sustained 8-core work, headroom in the
  OPP table doesn't translate to real throughput on this thermal package.

### Combined picture

- The CPU OC component of exp 025 is a **wash** under sustained 8-core
  load - same throughput as stock, same thermal envelope.
- The GPU OC component delivers a marginal +1.57 % with better stability
  but no real-world throughput gain.
- Earlier 180-second `bench_test.sh` runs that suggested +17 % GPU and
  +18.6 % CPU are short-bench artefacts. Once thermal saturation kicks
  in (~30-60 s after a cool-down), all of the gain disappears.

For practical use the recommended config is **stock everywhere, or stock
CPU + GPU OC 900 MHz** if you specifically want the GPU stability win.
The CPU UV (-37.5 mV) at the lower OPPs is still uncontroversial (lower
voltage at the same frequency is a free win), but its claimed
contribution to all-core sustained throughput was over-estimated.

## What "exp 025" was

A bundled DTB containing every individually-verified-stable knob:

- CPU LITTLE/BIG lower OPPs: UV -37.5 mV
- CPU top OPP: 2002 -> 2100 MHz at stock 1050 mV target
- GPU top OPP: 850 -> 900 MHz at stock 800 mV target
- Thermal trips: stock (raising them crashes the thermal framework)
- No voltage overvolt (DT requests above stock are silently ignored
  by the hardware DVFS path - see voltage-ceiling-hunt/)

This config was the "daily driver" recommendation. With +1.57 % real
GPU gain and 0 % real CPU gain under sustained load, **rolling back to
stock everywhere is a defensible choice**. The CPU UV (-37.5 mV) is the
only uncontroversial individual win (lower voltage at unchanged
frequency); the CPU OC and GPU OC are both debatable.

## Voltage ceiling

The GPU rail caps at 800 mV regardless of DT request. We chased this in
detail (see `voltage-ceiling-hunt/`):

1. Decoded the GPU voltage-grade table at top DVFS controller registers
   `0xe4` / `0xe8` - confirmed grade 0/1/2 = 700/750/800 mV and grade 3
   = 850 mV (pre-programmed but unused by stock OPPs).
2. Patched the kernel to disable `CONFIG_MODULE_SIG_FORCE` at runtime
   by flipping a single byte in the kernel image (file offset
   `0x22e8350` of the boot.img kernel) - lets us load arbitrary OOT
   modules.
3. Built a kernel module that ioremap's the GPU syscon and changes
   `core_index4_map` (slot 4's grade index) from 2 to 3 - the
   `regmap_update_bits` succeeds and the read-back confirms.
4. **The patch doesn't hold.** Mali's `mali_clock_on` path actively
   rewrites the `core_indexN_map` registers on every GPU power cycle,
   restoring slot 4 to grade 2 before the rail can use the new mapping.
   To make the patch persistent we'd need to binary-patch
   `mali_gondul.ko`'s `mali_clock_on` (or kprobe-hook every write).

Given the actual gain is +1.57 %, neither route was worth pursuing.

## Method gotchas (so the next pass doesn't repeat them)

- 180-second benches are too short. Stock 850 has periodic dips that
  drag the average down; only a longer (>=10 minute) run with consistent
  cool-down before each run gives a stable comparison.
- Cold-start frames matter. Stock's first 30 seconds and exp 025's first
  30 seconds are systematically different.
- Reading `/sys/kernel/debug/regmap/dummy-syscon@60110000/registers`
  from userspace can raise an asynchronous SError if the GPU subsystem
  is power-gated when the read happens. The deferred error arrives later
  on an unrelated CPU and panics the kernel. Do reads only while GPU
  power is held, or use targeted single-register reads via a kernel
  module.
- `regmap_update_bits_base` on the GPU syscon while the GPU is at the
  affected slot can also raise SError. Park GPU at min OPP first.
- BootROM does NOT touch PMIC voltage-rail registers (see
  `analysis/bootrom/DISASSEMBLY.md` in the parent repo). The grade
  table at top DVFS CTRL `0xe4`/`0xe8` is programmed by uboot or
  somewhere later - we did not find the exact write site.

## Earlier (now-retracted) numbers

The pre-torture experiment write-ups quote a `+17 %` GPU FPS gain from
the 900 MHz OC (eg. exp 020/025 README). That number came from the
180-second `bench_test.sh` runs and is wrong. The first long-form
torture (this directory, 2026-04-25) is the corrected figure. Specific
docs that contain the bad number have been left in place as a historical
record but should not be cited.

## Files of interest

- `oc_test/experiments/025-cpu2100-uv37.5-gpu900/modified.dts` - the
  exp 025 DTB
- `oc_test/CHANGELOG.md` - chronological log of every experiment
- `torture_2026-04-25/exp025_900MHz/telemetry.csv` - 552 per-second
  rows of the OC config under stress
- `torture_2026-04-25/stock_850MHz/telemetry.csv` - the matched stock
  baseline
- `voltage-ceiling-hunt/FOUND_IT.md` + `MODULE_LOADING_PATH.md` - the
  voltage-ceiling investigation that proved the +17 % was unreachable
  via DT alone, then chased it down to Mali's clock-on rewrite
