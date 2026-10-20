#!/usr/bin/env python3
"""Finds the slow spots of a tools/play.sh recording and what limited them.

    tools/perf_report.py out/pc/play [--budget-ms 16.7]

A slow spot is a second whose frames average over the budget, or that holds a hitch (a single frame over 50 ms). For
each: the frame times, the busiest threads, and the screenshot nearest to it. The SDK's draw-call and pipeline-miss
counters are shown only when the recording has any (the emulated GPU's Vulkan path leaves them at 0).

CPU % is time on a core, not work: a thread that waits by spinning shows 100 % while idle in effect.
"""
import argparse
import csv
import os
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument('folder')
ap.add_argument('--budget-ms', type=float, default=17.5,
                help='frame budget; 60 fps is 16.7 ms, so a little over it counts as on time (default 17.5)')
a = ap.parse_args()

# Frames, placed in time by adding up their frame times.
seconds = defaultdict(list)
misses = defaultdict(int)
draws = defaultdict(list)
t = 0.0
with open(os.path.join(a.folder, 'frames.csv')) as f:
    for row in csv.DictReader(f):
        ms = int(row['frame_time_us']) / 1000
        t += ms / 1000
        s = int(t)
        seconds[s].append(ms)
        misses[s] += int(row.get('pipeline_cache_misses') or 0)
        draws[s].append(int(row.get('draw_calls') or 0))

threads = defaultdict(list)  # second -> [(cpu %, name)]
with open(os.path.join(a.folder, 'threads.csv')) as f:
    for row in csv.DictReader(f):
        threads[int(float(row['seconds']))].append((int(row['cpu_percent']), row['name']))

total = sum(len(v) for v in seconds.values())
slow_total = sum(1 for v in seconds.values() for ms in v if ms > a.budget_ms)
print(f'{total} frames over {len(seconds)} s; {slow_total} frames ({100 * slow_total / max(total, 1):.1f} %) over '
      f'{a.budget_ms:.1f} ms')

# Whole-run thread totals: which threads use the most CPU overall.
busy = defaultdict(list)
for rows in threads.values():
    for cpu, name in rows:
        busy[name].append(cpu)
print('\nbusiest threads over the run (mean / max % of one core):')
for name, values in sorted(busy.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:8]:
    print(f'  {name:20} {sum(values) / len(values):5.0f} / {max(values):4d}')

shots = sorted(int(n[5:-5]) for n in os.listdir(os.path.join(a.folder, 'shots'))
               if n.startswith('shot_') and n.endswith('s.ppm')) if os.path.isdir(os.path.join(a.folder, 'shots')) else []

print('\nslow spots:')
for s in sorted(seconds):
    frames = seconds[s]
    mean = sum(frames) / len(frames)
    worst = max(frames)
    if mean <= a.budget_ms and worst <= 50:
        continue
    extra = ''
    if any(misses.values()):
        extra += f', new shaders {misses[s]:3d}'
    if any(sum(v) for v in draws.values()):
        extra += f', draws/frame {sum(draws[s]) // len(draws[s]):5d}'
    top = ', '.join(f'{n} {c}%' for c, n in sorted(threads.get(s, []), reverse=True)[:3])
    shot = min(shots, key=lambda x: abs(x - s)) if shots else None
    print(f'  {s:5d} s: {len(frames):3d} fps, mean {mean:5.1f} ms, worst {worst:6.1f} ms, '
          f'{extra[2:] + " | " if extra else ""}{top}'
          + (f' | shot_{shot}s' if shot is not None else ''))
