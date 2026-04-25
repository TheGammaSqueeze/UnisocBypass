# 005-stock-cpu-only

**Status:** completed 2026-04-24 (v2, clean state)
**Mode:** `cpu` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline CPU-only: 8 cores at 2002 MHz, GPU pinned at 384 MHz idle.

NOTE: This is the v2 baseline. The original first-run baseline was compromised (likely due to leftover background processes), showing CPU throughput ~3-4x lower than the true rate. This v2 baseline was captured after a clean boot on unmodified stock DTB.

## Result summary

| metric | value |
|--------|------:|
| samples | 85 |
| CPU LITTLE avg MHz | 2002 |
| CPU BIG avg MHz | 2002 |
| GPU avg MHz | 384 |
| GPU throttled samples | 85/85 (100%) |
| SoC peak C | 105.0 |
| vddcpu range mV | 1050.0 - 1050.0 |
| vddgpu range mV | 700.0 - 700.0 |
| CPU throughput | 69,763,072 KiB (66.53 GiB) |
