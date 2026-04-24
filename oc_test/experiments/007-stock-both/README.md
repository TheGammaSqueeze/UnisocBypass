# 007-stock-both

**Status:** completed 2026-04-24 (v2, clean state)
**Mode:** `both` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline both: CPU + GPU under concurrent stress.

NOTE: This is the v2 baseline. The original first-run baseline was compromised (likely due to leftover background processes), showing CPU throughput ~3-4x lower than the true rate. This v2 baseline was captured after a clean boot on unmodified stock DTB.

## Result summary

| metric | value |
|--------|------:|
| samples | 75 |
| CPU LITTLE avg MHz | 2002 |
| CPU BIG avg MHz | 2002 |
| GPU avg MHz | 446 |
| GPU throttled samples | 65/75 (86%) |
| SoC peak C | 105.8 |
| vddcpu range mV | 1050.0 - 1050.0 |
| vddgpu range mV | 700.0 - 800.0 |
| CPU throughput | 63,328,256 KiB (60.39 GiB) |
| GPU FPS avg | 8.12 |
| GPU FPS first 10s | 16.01 |
| GPU FPS last 10s | 7.48 |
