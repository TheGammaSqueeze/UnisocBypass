# 006-stock-gpu-only

**Status:** completed 2026-04-24
**Mode:** `gpu` (bench_test.sh)
**Config:** stock (no DTB modifications)

## Purpose

Stock baseline: GPU at 850 MHz performance governor, CPU policies pinned to min. Captures pure GPU thermal + FPS behavior.

## Result summary

| metric | value |
|--------|------:|
| samples | 39 |
| CPU LITTLE avg MHz | 614 |
| CPU BIG avg MHz | 1228 |
| GPU avg MHz | 850 |
| SoC peak C | 68.5 |
| GPU TZ peak C | 67.8 |
| BIG TZ peak C | 67.9 |
| vddcpu stress range | 762.5 - 762.5 mV |
| vddgpu stress range | 800.0 - 800.0 mV |
| GPU FPS avg | 13.86 |
| GPU FPS first 10 s | 10.81 |
| GPU FPS last 10 s | 16.23 |
