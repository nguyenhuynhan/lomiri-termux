#!/usr/bin/env python3
"""Summarize Qt render-loop timings; these are not display FPS measurements."""
import csv
import json
import math
from pathlib import Path
import re
import statistics

runtime = Path(__file__).resolve().parent.parent / 'runtime/gpu-experiments'
results = []
for round_name, directory in [('round1', runtime / 'round1'), ('round2', runtime)]:
    for backend in ['software', 'virgl', 'kgsl', 'zink', 'kgsl-threaded']:
        path = directory / (backend + '-menu-timing.log')
        if not path.exists():
            continue
        # Only the three finalists are repeated in round 2.
        if round_name == 'round2' and backend in ['virgl', 'kgsl-threaded']:
            continue
        rows = [tuple(map(int, item)) for item in re.findall(
            r"Frame rendered with '[^']+' renderloop in (\d+)ms.*?render=(\d+), swap=(\d+)",
            path.read_text(errors='replace'))]
        if not rows:
            results.append({'round': round_name, 'backend': backend, 'frames': 0})
            continue
        def p95(values):
            ordered = sorted(values)
            return ordered[math.ceil(len(ordered) * .95) - 1]
        total, render, swap = list(zip(*rows))
        results.append({'round': round_name, 'backend': backend, 'frames': len(rows),
                        'median_loop_ms': statistics.median(total), 'p95_loop_ms': p95(total),
                        'median_render_ms': statistics.median(render), 'p95_render_ms': p95(render),
                        'median_swap_ms': statistics.median(swap), 'p95_swap_ms': p95(swap)})
output = {'measurement': 'Qt render-loop duration, not actual presentation FPS',
          'workload': '2 warmup and 12 menu toggles, 672x1339, per-process basic or threaded loop',
          'p95_definition': 'nearest rank', 'results': results}
(runtime / 'timing-summary.json').write_text(json.dumps(output, indent=2))
if results:
    with (runtime / 'timing-summary.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(next(item for item in results if item['frames']).keys()))
        writer.writeheader()
        writer.writerows(results)
print(json.dumps(output, indent=2))
