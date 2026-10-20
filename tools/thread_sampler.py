#!/usr/bin/env python3
"""Samples per-thread CPU use of a running process from /proc every second, for finding which thread limits the
frame rate (the game's own threads or the emulated GPU's). Needs no profiler or root.

    tools/thread_sampler.py <pid> <out.csv>

Writes one row per second and thread: seconds since start, thread id, thread name, CPU % of one core in that second.
Also one row named "host GPU busy": the host GPU's load in that second (amdgpu's gpu_busy_percent, read 10 times and
averaged; absent on other drivers). Stops when the process exits.
"""
import glob
import os
import sys
import time

pid, out_path = int(sys.argv[1]), sys.argv[2]
tick = os.sysconf('SC_CLK_TCK')
gpu_busy = sorted(glob.glob('/sys/class/drm/card*/device/gpu_busy_percent'))


def read_gpu_busy():
    try:
        with open(gpu_busy[0]) as f:
            return int(f.read())
    except (IndexError, OSError, ValueError):
        return None


def sample():
    threads = {}
    try:
        tids = os.listdir(f'/proc/{pid}/task')
    except FileNotFoundError:
        return None
    for tid in tids:
        try:
            with open(f'/proc/{pid}/task/{tid}/stat') as f:
                stat = f.read()
            with open(f'/proc/{pid}/task/{tid}/comm') as f:
                name = f.read().strip()
        except (FileNotFoundError, ProcessLookupError):
            continue
        fields = stat[stat.rindex(')') + 2:].split()  # after "pid (comm) "
        threads[tid] = (name, int(fields[11]) + int(fields[12]))  # utime + stime, in clock ticks
    return threads


start = time.monotonic()
previous = sample()
with open(out_path, 'w') as out:
    out.write('seconds,tid,name,cpu_percent\n')
    while previous is not None:
        readings = []
        for _ in range(10):
            time.sleep(0.1)
            busy = read_gpu_busy()
            if busy is not None:
                readings.append(busy)
        current = sample()
        if current is None:
            break
        now = time.monotonic() - start
        for tid, (name, ticks) in current.items():
            before = previous.get(tid, (name, ticks))[1]
            out.write(f'{now:.1f},{tid},{name},{100.0 * (ticks - before) / tick:.0f}\n')
        if readings:
            out.write(f'{now:.1f},0,host GPU busy,{sum(readings) / len(readings):.0f}\n')
        out.flush()
        previous = current
