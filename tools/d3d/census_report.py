#!/usr/bin/env python3
"""Reads out/pc/census.csv (tools/d3d/census_build.py) and prints, for a time window, each function's calls per frame
(frames = calls to the Swap function in the window), plus its total over the whole run.

    tools/d3d/census_report.py [--from 140] [--to 168] [--swap 82664278] [--top 60] [--only ADDR,...]
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap = argparse.ArgumentParser()
ap.add_argument('--csv', default=os.path.join(ROOT, 'out', 'pc', 'census.csv'))
ap.add_argument('--from', dest='lo', type=int, default=140)
ap.add_argument('--to', dest='hi', type=int, default=168)
ap.add_argument('--swap', default='82664278')
ap.add_argument('--top', type=int, default=60)
ap.add_argument('--only', default='')
a = ap.parse_args()

rows = {}
for line in open(a.csv):
    parts = line.strip().split(',')
    rows[int(parts[0])] = {p.split(':')[0]: int(p.split(':')[1]) for p in parts[1:]}
times = sorted(rows)
lo = max(t for t in times if t <= a.lo)
hi = max(t for t in times if t <= a.hi)
last = rows[times[-1]]
delta = {k: rows[hi].get(k, 0) - rows[lo].get(k, 0) for k in rows[hi]}
frames = delta.get(a.swap, 0) or 1
fn = json.load(open(os.path.join(ROOT, 'out', 'fnindex.json')))
print(f'window {lo}-{hi} s: {frames} frames (Swap calls), {frames / (hi - lo):.1f} per second')
keys = a.only.split(',') if a.only else sorted(delta, key=lambda k: -delta[k])[:a.top]
for k in keys:
    f = fn.get('sub_' + k, {'listing': [], 'callers': []})
    print(f'  {k}  {delta.get(k, 0) / frames:9.2f}/frame  total {last.get(k, 0):9d}  '
          f'{len(f["listing"]):4d} insns  {len(f["callers"]):3d} direct callers')
