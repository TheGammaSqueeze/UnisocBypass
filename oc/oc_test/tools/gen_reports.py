#!/usr/bin/env python3
"""Generate README.md + REPORT.md for an experiment dir containing cpu/, gpu/, both/ subdirs."""
import csv, statistics, sys
from pathlib import Path

def load_run(d):
    if not (d/'telemetry.csv').exists():
        return None
    rows = list(csv.DictReader((d/'telemetry.csv').open()))
    if not rows:
        return None
    cpu_work = 0
    if (d/'cpu_counts.txt').exists():
        for line in (d/'cpu_counts.txt').read_text().splitlines():
            if '=' in line:
                cpu_work += int(line.split('=')[1])
    fps = []
    if (d/'gpu_stress.log').exists():
        for l in (d/'gpu_stress.log').read_text().splitlines():
            if 'fps=' in l:
                fps.append(float(l.split('fps=')[1].split()[0]))
    sweep = list(csv.DictReader((d/'opp_voltage_sweep.csv').open())) if (d/'opp_voltage_sweep.csv').exists() else []
    return {'rows': rows, 'cpu_work': cpu_work, 'fps': fps, 'sweep': sweep}

def summary(run):
    r = run['rows']
    return {
        'samples': len(r),
        'cpu0_avg': statistics.mean(int(x['cpu0_mhz']) for x in r),
        'cpu6_avg': statistics.mean(int(x['cpu6_mhz']) for x in r),
        'gpu_avg': statistics.mean(int(x['gpu_mhz']) for x in r),
        'soc_pk': max(int(x['thermal_zone1_soc-thmzone'])/1000 for x in r),
        'gpu_tz_pk': max(int(x['thermal_zone7_gpu-thmzone'])/1000 for x in r),
        'big_pk': max(int(x['thermal_zone4_prometheus7-thmzone'])/1000 for x in r),
        'vcpu_avg': statistics.mean(int(x['vddcpu_uV']) for x in r if int(x['vddcpu_uV'])>0)/1000,
        'vgpu_avg': statistics.mean(int(x['vddgpu_uV']) for x in r if int(x['vddgpu_uV'])>0)/1000,
        'cpu_work_gib': run['cpu_work']/1024/1024 if run['cpu_work'] else 0,
        'fps_avg': statistics.mean(run['fps']) if run['fps'] else 0,
        'fps_first': statistics.mean(run['fps'][:10]) if len(run['fps'])>=10 else 0,
        'fps_last': statistics.mean(run['fps'][-10:]) if len(run['fps'])>=10 else 0,
    }

def main():
    if len(sys.argv) != 2:
        print("usage: gen_reports.py <experiment_dir>", file=sys.stderr)
        sys.exit(2)
    exp = Path(sys.argv[1])
    runs = {}
    for mode in ['cpu', 'gpu', 'both']:
        r = load_run(exp/mode)
        if r:
            runs[mode] = r

    # Baselines for comparison
    baselines = {}
    for mode, slug in [('cpu','005-stock-cpu-only'), ('gpu','006-stock-gpu-only'), ('both','007-stock-both')]:
        base_dir = Path(f'/work/vita/signing/oc_test/experiments/{slug}/raw')
        r = load_run(base_dir)
        if r:
            baselines[mode] = r

    # Write REPORT.md
    rpt = exp/'REPORT.md'
    with rpt.open('w') as f:
        f.write(f'# {exp.name} REPORT\n\n')
        f.write('## Summary across modes\n\n')
        f.write('| mode | samples | CPU6 MHz | GPU MHz | SoC pk C | vddcpu mV | vddgpu mV | CPU GiB | FPS avg | vs baseline |\n')
        f.write('|------|--------:|---------:|--------:|---------:|----------:|----------:|--------:|--------:|-------------|\n')
        for mode in ['cpu','gpu','both']:
            if mode not in runs:
                continue
            s = summary(runs[mode])
            bs = summary(baselines[mode]) if mode in baselines else None
            cmp_strs = []
            if bs:
                # Performance comparison
                if mode == 'cpu' and s['cpu_work_gib'] and bs['cpu_work_gib']:
                    delta = (s['cpu_work_gib'] - bs['cpu_work_gib']) / bs['cpu_work_gib'] * 100
                    cmp_strs.append(f'CPU perf {delta:+.1f}%')
                if mode == 'gpu' and s['fps_avg'] and bs['fps_avg']:
                    delta = (s['fps_avg'] - bs['fps_avg']) / bs['fps_avg'] * 100
                    cmp_strs.append(f'GPU perf {delta:+.1f}%')
                if mode == 'both':
                    if s['cpu_work_gib'] and bs['cpu_work_gib']:
                        d1 = (s['cpu_work_gib'] - bs['cpu_work_gib']) / bs['cpu_work_gib'] * 100
                        cmp_strs.append(f'CPU {d1:+.1f}%')
                    if s['fps_avg'] and bs['fps_avg']:
                        d2 = (s['fps_avg'] - bs['fps_avg']) / bs['fps_avg'] * 100
                        cmp_strs.append(f'FPS {d2:+.1f}%')
                dt = s['soc_pk'] - bs['soc_pk']
                cmp_strs.append(f'SoC pk {dt:+.1f}C')
            f.write(f'| {mode} | {s["samples"]} | {s["cpu6_avg"]:.0f} | {s["gpu_avg"]:.0f} | {s["soc_pk"]:.1f} | {s["vcpu_avg"]:.1f} | {s["vgpu_avg"]:.1f} | {s["cpu_work_gib"]:.2f} | {s["fps_avg"]:.2f} | {", ".join(cmp_strs)} |\n')

        # Voltage evidence: compare stock DT vs observed per mode
        f.write('\n## Voltage evidence\n\n')
        for mode in ['cpu','gpu','both']:
            if mode not in runs:
                continue
            f.write(f'### mode={mode}: pre-test OPP voltage sweep\n\n')
            f.write('| stage | target MHz | actual MHz | vddcpu mV | vddgpu mV |\n')
            f.write('|-------|-----------:|-----------:|----------:|----------:|\n')
            for sr in runs[mode]['sweep']:
                actual = int(sr['actual_cur_freq_hz']) / (1_000_000 if 'gpu' in sr['stage'] else 1_000)
                f.write(f'| {sr["stage"]} | {sr["target_mhz"]} | {actual:.0f} | {int(sr["vddcpu_uV"])/1000:.1f} | {int(sr["vddgpu_uV"])/1000:.1f} |\n')
            f.write('\n')

        # Thermal detail for both mode
        if 'both' in runs:
            f.write('## Thermal peaks (both mode)\n\n')
            rows = runs['both']['rows']
            f.write('| sensor | peak C |\n|--------|-------:|\n')
            for col in sorted([k for k in rows[0].keys() if 'thermal_zone' in k]):
                peak = max(int(r[col])/1000 for r in rows)
                f.write(f'| `{col}` | {peak:.1f} |\n')

    print(f'wrote {rpt}')

    # Also produce a one-line summary row for CHANGELOG insertion
    changelog_row = None
    if 'both' in runs:
        s = summary(runs['both'])
        bs = summary(baselines['both']) if 'both' in baselines else None
        cpu_delta = 0
        fps_delta = 0
        if bs:
            if s['cpu_work_gib'] and bs['cpu_work_gib']:
                cpu_delta = (s['cpu_work_gib'] - bs['cpu_work_gib']) / bs['cpu_work_gib'] * 100
            if s['fps_avg'] and bs['fps_avg']:
                fps_delta = (s['fps_avg'] - bs['fps_avg']) / bs['fps_avg'] * 100
        print(f'CHANGELOG_ROW: samples={s["samples"]} cpu_gib={s["cpu_work_gib"]:.2f} fps={s["fps_avg"]:.2f} soc_pk={s["soc_pk"]:.1f} cpu_delta={cpu_delta:+.1f}% fps_delta={fps_delta:+.1f}%')

if __name__ == '__main__':
    main()
