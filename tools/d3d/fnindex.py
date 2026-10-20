#!/usr/bin/env python3
"""Index of the generated code for the Direct3D census: each function's PPC listing (from the generator's comments),
its direct callees, its callers and the imports it calls. Written to out/fnindex.json, then queried:

    tools/d3d/fnindex.py build
    tools/d3d/fnindex.py show sub_82664278 [--lines 80]     listing, callees, callers
    tools/d3d/fnindex.py callers sub_82664278
    tools/d3d/fnindex.py grep 'lis r11,-16384'               functions whose listing has a match (regex)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, 'app', 'generated', 'default')
OUT = os.path.join(ROOT, 'out', 'fnindex.json')


def build():
    funcs = {}
    for path in sorted(glob.glob(os.path.join(GEN, 'mhnwis_recomp.*.cpp'))):
        cur = None
        for line in open(path, errors='replace'):
            m = re.match(r'DEFINE_REX_FUNC\((sub_[0-9A-F]+)\)', line)
            if m:
                cur = m.group(1)
                funcs[cur] = {'listing': [], 'callees': [], 'imports': []}
                continue
            if cur is None:
                continue
            f = funcs[cur]
            s = line.strip()
            if s.startswith('// ') and not s.startswith('// ERROR'):
                f['listing'].append(s[3:])
            elif s.startswith('loc_') and s.endswith(':'):
                f['listing'].append(s)
            for callee in re.findall(r'\b(sub_[0-9A-F]{8})\(ctx', line):
                if callee not in f['callees']:
                    f['callees'].append(callee)
            for imp in re.findall(r'__imp__([A-Za-z_][A-Za-z0-9_]*)\(ctx', line):
                if imp not in f['imports']:
                    f['imports'].append(imp)
    callers = {}
    for name, f in funcs.items():
        for c in f['callees']:
            callers.setdefault(c, []).append(name)
    for name, f in funcs.items():
        f['callers'] = sorted(callers.get(name, []))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(funcs, open(OUT, 'w'))
    print(f'{len(funcs)} functions indexed to {OUT}')


def load():
    return json.load(open(OUT))


def main():
    cmd = sys.argv[1]
    if cmd == 'build':
        return build()
    funcs = load()
    if cmd == 'show':
        name = sys.argv[2]
        limit = int(sys.argv[sys.argv.index('--lines') + 1]) if '--lines' in sys.argv else 10**9
        f = funcs[name]
        print(f'{name}: {len(f["listing"])} lines; callers {f["callers"]}')
        print(f'  callees {f["callees"]}\n  imports {f["imports"]}')
        for line in f['listing'][:limit]:
            print('   ', line)
    elif cmd == 'callers':
        print(' '.join(funcs[sys.argv[2]]['callers']))
    elif cmd == 'grep':
        rx = re.compile(sys.argv[2])
        for name in sorted(funcs):
            hits = [l for l in funcs[name]['listing'] if rx.search(l)]
            if hits:
                print(f'{name} ({len(funcs[name]["listing"])} lines): {hits[0]}' + (f' (+{len(hits) - 1})' if len(hits) > 1 else ''))


if __name__ == '__main__':
    main()
