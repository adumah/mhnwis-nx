#!/usr/bin/env python3
"""Finds functions in an address range whose listing uses every one of a set of displacements (e.g. 48 and 52, the
device's ring pointer and limit), and shows each with its size, callers and census rate (out/census/census_run1.csv).

    tools/d3d/fingerprint.py 48 52 [--lo 0x8264E000] [--hi 0x82698000] [--max-insns 400] [--regex REGEX ...]
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap = argparse.ArgumentParser()
ap.add_argument('offsets', nargs='*', type=int)
ap.add_argument('--lo', type=lambda s: int(s, 16), default=0x8264E000)
ap.add_argument('--hi', type=lambda s: int(s, 16), default=0x82698000)
ap.add_argument('--max-insns', type=int, default=400)
ap.add_argument('--regex', action='append', default=[])
ap.add_argument('--census', default=os.path.join(ROOT, 'out', 'census', 'census_run1.csv'))
a = ap.parse_args()

F = json.load(open(os.path.join(ROOT, 'out', 'fnindex.json')))
rate = {}
if os.path.exists(a.census):
    rows = [l.strip().split(',') for l in open(a.census)]
    last = {p.split(':')[0]: int(p.split(':')[1]) for p in rows[-1][1:]}
    swaps = last.get('82664278', 1) or 1
    rate = {k: v / swaps for k, v in last.items()}
for name in sorted(F):
    addr = int(name[4:], 16)
    if not a.lo <= addr < a.hi:
        continue
    L = F[name]['listing']
    if len(L) > a.max_insns:
        continue
    disps = {int(m.group(1)) for l in L for m in [re.search(r',(-?\d+)\(r\d+\)$', l)] if m}
    if not set(a.offsets) <= disps:
        continue
    if not all(any(re.search(rx, l) for l in L) for rx in a.regex):
        continue
    r = rate.get(name[4:], 0)
    print(f'{name}  {len(L):4d} insns  {len(F[name]["callers"]):3d} callers  {r:10.2f}/frame (run total)')
