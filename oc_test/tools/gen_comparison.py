#!/usr/bin/env python3
"""Regenerate COMPARISON.md comparing every experiment's 3 modes vs stock baselines."""
import csv, statistics, sys
from pathlib import Path

EXP_DIR = Path('/work/vita/signing/oc_test/experiments')
BASELINES = {'cpu': '005-stock-cpu-only', 'gpu': '006-stock-gpu-only', 'both': '007-stock-both'}

LEGACY_SINGLE_MODE = {
    '000-stock-baseline': 'both',
    '001-gpu-uv-top-12.5mV': 'both',
    '002-gpu-uv-all-25mV': 'both',
    '003-gpu-uv-all-25mV-gpu-only-load': 'gpu',
    '004-gpu-uv37.5-cpu-uv25': 'both',
}

def load_mode(d, mode):
    """Load a specific mode for an experiment. Legacy dirs (000-004) have raw/ only
    and apply to one specific mode. New dirs have cpu/, gpu/, both/ subdirs."""
    if d.name in BASELINES.values():
        cands = [d/'raw']
    elif d.name in LEGACY_SINGLE_MODE:
        if LEGACY_SINGLE_MODE[d.name] != mode:
            return None
        cands = [d/'raw']
    else:
        cands = [d/mode]
    for c in cands:
        if (c/'telemetry.csv').exists():
            rows = list(csv.DictReader((c/'telemetry.csv').open()))
            if not rows: continue
            cpu_work = 0
            if (c/'cpu_counts.txt').exists():
                for line in (c/'cpu_counts.txt').read_text().splitlines():
                    if '=' in line: cpu_work += int(line.split('=')[1])
            fps = []
            if (c/'gpu_stress.log').exists():
                for l in (c/'gpu_stress.log').read_text().splitlines():
                    if 'fps=' in l: fps.append(float(l.split('fps=')[1].split()[0]))
            gpu = [int(r['gpu_mhz']) for r in rows]
            soc = max(int(r['thermal_zone1_soc-thmzone'])/1000 for r in rows)
            vcpu = [int(r['vddcpu_uV']) for r in rows if int(r['vddcpu_uV'])>0] if 'vddcpu_uV' in rows[0] else []
            vgpu = [int(r['vddgpu_uV']) for r in rows if int(r['vddgpu_uV'])>0] if 'vddgpu_uV' in rows[0] else []
            return {
                'path': c,
                'samples': len(rows),
                'gpu_avg': statistics.mean(gpu),
                'gpu_throttled_pct': sum(1 for v in gpu if v < 850) * 100 // len(rows),
                'soc_pk': soc,
                'vcpu_avg': statistics.mean(vcpu)/1000 if vcpu else 0,
                'vgpu_avg': statistics.mean(vgpu)/1000 if vgpu else 0,
                'cpu_gib': cpu_work/1024/1024 if cpu_work else 0,
                'fps_avg': statistics.mean(fps) if fps else 0,
                'fps_last': statistics.mean(fps[-10:]) if len(fps)>=10 else 0,
            }
    return None

# Load stock baselines
stock = {}
for mode, slug in BASELINES.items():
    stock[mode] = load_mode(EXP_DIR/slug, mode)

def delta_str(new, old, unit=''):
    if old is None or old == 0: return 'n/a'
    d = (new - old) / old * 100
    return f'{d:+.1f}%' if abs(d) >= 0.1 else '~0%'

out = Path('/work/vita/signing/oc_test/COMPARISON.md')
with out.open('w') as f:
    f.write('# Experiment comparison vs stock baselines\n\n')
    f.write('Auto-generated from `oc_test/experiments/*/{cpu,gpu,both}/telemetry.csv` and friends. ')
    f.write('Stock baselines: 005 (cpu-only), 006 (gpu-only), 007 (both).\n\n')
    
    f.write('## Stock baseline reference\n\n')
    f.write('| mode | samples | GPU avg MHz | GPU throttled % | SoC peak C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | FPS last 10s |\n')
    f.write('|------|--------:|------------:|----------------:|-----------:|----------:|----------:|--------:|--------:|-------------:|\n')
    for mode in ['cpu','gpu','both']:
        s = stock.get(mode)
        if s:
            f.write(f'| {mode} | {s["samples"]} | {s["gpu_avg"]:.0f} | {s["gpu_throttled_pct"]}% | {s["soc_pk"]:.1f} | {s["vcpu_avg"]:.0f} | {s["vgpu_avg"]:.0f} | {s["cpu_gib"]:.2f} | {s["fps_avg"]:.2f} | {s["fps_last"]:.2f} |\n')
    
    # Find all experiments (excluding stock baselines)
    exps = sorted([d for d in EXP_DIR.iterdir() if d.is_dir() and d.name not in BASELINES.values()])
    
    for exp in exps:
        # Parse name for description
        name = exp.name
        f.write(f'\n## {name}\n\n')
        
        # Try to extract config from README.md
        readme = exp/'README.md'
        if readme.exists():
            lines = readme.read_text().splitlines()
            for l in lines[:10]:
                if '**Config:**' in l or 'Config:' in l:
                    f.write(l.replace('**Config:**', 'Config:') + '\n\n')
                    break
        
        f.write('| mode | samples | GPU avg | GPU thr. % | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs stock |\n')
        f.write('|------|--------:|--------:|-----------:|---------:|----------:|----------:|--------:|--------:|----------|\n')
        
        has_any = False
        for mode in ['cpu','gpu','both']:
            r = load_mode(exp, mode)
            if not r: continue
            has_any = True
            s = stock.get(mode)
            cmps = []
            if s:
                if mode == 'cpu':
                    cmps.append(f'CPU perf {delta_str(r["cpu_gib"], s["cpu_gib"])}')
                    cmps.append(f'SoC {r["soc_pk"] - s["soc_pk"]:+.1f}C')
                    cmps.append(f'vddcpu {r["vcpu_avg"] - s["vcpu_avg"]:+.0f}mV')
                elif mode == 'gpu':
                    cmps.append(f'GPU perf {delta_str(r["fps_avg"], s["fps_avg"])}')
                    cmps.append(f'SoC {r["soc_pk"] - s["soc_pk"]:+.1f}C')
                    cmps.append(f'vddgpu {r["vgpu_avg"] - s["vgpu_avg"]:+.0f}mV')
                elif mode == 'both':
                    cmps.append(f'CPU {delta_str(r["cpu_gib"], s["cpu_gib"])}')
                    cmps.append(f'FPS {delta_str(r["fps_avg"], s["fps_avg"])}')
                    cmps.append(f'SoC {r["soc_pk"] - s["soc_pk"]:+.1f}C')
            f.write(f'| {mode} | {r["samples"]} | {r["gpu_avg"]:.0f} | {r["gpu_throttled_pct"]}% | {r["soc_pk"]:.1f} | {r["vcpu_avg"]:.0f} | {r["vgpu_avg"]:.0f} | {r["cpu_gib"]:.2f} | {r["fps_avg"]:.2f} | {", ".join(cmps)} |\n')
        
        if not has_any:
            f.write('| (no results yet) |\n')
    
    f.write('\n## Conclusions (running)\n\n')
    f.write('- **CPU UV lands on hardware.** vddcpu tracks the DT voltage reduction (minus AVS adjustment).\n')
    f.write('- **GPU UV via DTB does NOT land.** vddgpu stays at stock 700/800 mV regardless of DT voltage changes. Requires a different attack path (kernel module patch or as-yet-unidentified DT property).\n')
    f.write('- **Torture mode is CPU-thermal-dominated.** CPU-only hits 106 C just as fast as both-mode. GPU-only stays below 70 C. UV impact on both-mode thermals is modest (~1-2 C) unless the UV is deep enough to noticeably cut CPU power.\n')
    f.write('- **UV performance cliff**: TBD. Iterating down in 12.5 mV steps until either perf drops >10% or boot fails.\n')
print(f'wrote {out}')
