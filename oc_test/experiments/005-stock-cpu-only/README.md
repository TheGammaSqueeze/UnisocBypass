# 005-stock-cpu-only

**Status:** completed 2026-04-24
**Mode:** `cpu` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline: 8 CPU cores at 2002 MHz, GPU pinned at 384 MHz idle. Captures pure CPU thermal + throughput behavior.

## Result summary

| metric | value |
|--------|------:|
| samples | 135 |
| CPU LITTLE avg MHz | 2002 |
| CPU BIG avg MHz | 2002 |
| GPU avg MHz | 384 |
| SoC peak C | 106.0 |
| GPU TZ peak C | 97.7 |
| BIG TZ peak C | 104.0 |
| vddcpu stress range | 1050.0 - 1050.0 mV |
| vddgpu stress range | 700.0 - 700.0 mV |
| CPU throughput | 20,992,000 KiB (20.0 GiB) |
