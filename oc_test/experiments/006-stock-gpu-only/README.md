# 006-stock-gpu-only

**Status:** completed 2026-04-24 (v2, clean state)
**Mode:** `gpu` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline GPU-only: GPU at 850 MHz, CPUs pinned to min.

NOTE: This is the v2 baseline. The original first-run baseline was compromised (likely due to leftover background processes), showing CPU throughput ~3-4x lower than the true rate. This v2 baseline was captured after a clean boot on unmodified stock DTB.

## Result summary

| metric | value |
|--------|------:|
| samples | 129 |
| CPU LITTLE avg MHz | 614 |
| CPU BIG avg MHz | 1228 |
| GPU avg MHz | 850 |
| GPU throttled samples | 0/129 (0%) |
| SoC peak C | 66.0 |
| vddcpu range mV | 756.2 - 762.5 |
| vddgpu range mV | 700.0 - 800.0 |
| GPU FPS avg | 16.27 |
| GPU FPS first 10s | 16.30 |
| GPU FPS last 10s | 16.23 |
