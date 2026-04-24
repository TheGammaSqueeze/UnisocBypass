# 007-stock-both

**Status:** completed 2026-04-24
**Mode:** `both` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline: CPU 2002 + GPU 850 MHz under concurrent stress. New-harness equivalent of 000-stock-baseline.

## Result summary

| metric | value |
|--------|------:|
| samples | 76 |
| CPU LITTLE avg MHz | 2002 |
| CPU BIG avg MHz | 2002 |
| GPU avg MHz | 588 |
| SoC peak C | 106.8 |
| GPU TZ peak C | 100.3 |
| BIG TZ peak C | 104.5 |
| vddcpu stress range | 1009.4 - 1009.4 mV |
| vddgpu stress range | 700.0 - 800.0 mV |
| CPU throughput | 13,524,992 KiB (12.9 GiB) |
| GPU FPS avg | 4.90 |
| GPU FPS first 10 s | 4.21 |
| GPU FPS last 10 s | 8.16 |
