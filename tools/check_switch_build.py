#!/usr/bin/env python3
# mhnwis: a copy of sa2-nx's tools/check_switch_build.py (GPL-3.0) for this game: its own guest halts (guest_halts),
# no SA2 FMA pairings, this repository's paths, and a fix in chain_to.
"""Checks a Switch build before it is packaged (from sasrt-nx's check_switch_build.py and nfsmw-nx's lessons).

  python tools/check_switch_build.py [--elf out/nx/sa2] [--nro out/nx/sa2.nro]

Checks (exit 1 if any fails):
  - _start is at address 0 (nfsmw-nx: a section-ordering file that moved the start-up code made the NRO unbootable);
  - the build names the optimised codegen flavour (the only one delivered);
  - the NRO links the nfsmw NVK driver of the SDK (its "Mesa x.y.z" string; the generic portlibs Mesa once got in), or,
    for a build without the driver (1.0.3 on: no nvk_ symbol in the ELF), no Mesa string at all;
  - branch-to-self loops in recompiled functions are only in the functions with a known guest halt (KNOWN_HALTS; a
    polling loop GCC turned into "b ." with non-volatile memory means a missing loop barrier);
  - no vector fmla/fmls in recompiled functions: the generated code has no vector fused multiply-add (VMX multiply-adds
    are a multiply and an add), so any would be contraction that leaked past -ffp-contract=off (e.g. at an LTO link).
    Scalar fmadd/fmsub/fnmadd/fnmsub come from the guest's own std::fma and are only counted, and so are the vector
    ones checked to be two of them packed together (KNOWN_VECTOR_FMA).
"""
import argparse
import collections
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The 15 functions whose original PowerPC code has a "b ." halt (the non-LTO optimised build, 2026-10-06). Optimisation
# may duplicate a halt instruction (the LTO build has two adjacent ones in sub_828DB988 and sub_8293FA08), so the check
# is by function: a branch-to-self anywhere else is a polling loop that lost its barrier.
def guest_halts():
    """mhnwis: the functions whose original PowerPC code branches to itself, from the decrypted image the code generator
    dumps (out/default_image.bin) and the generated code's function starts: "b ." (0x48000000) and the conditional
    form, a bc with a zero displacement ("bne cr6,$": the compilers' halt on a failed check, e.g. sub_8263ABE0).
    sa2-nx lists SA2's by hand."""
    import bisect
    import glob
    import struct
    image = os.path.join(ROOT, 'out', 'default_image.bin')
    if not os.path.exists(image):
        return []
    data = open(image, 'rb').read()
    starts = sorted(int(m, 16) for path in glob.glob(os.path.join(ROOT, 'app', 'generated', '*', '*_recomp.*.cpp'))
                    for m in re.findall(r'^DEFINE_REX_FUNC\(sub_([0-9A-F]{8})\)', open(path, errors='replace').read(), re.M))
    halts = set()
    for off in range(0, len(data) - 3, 4):
        word = struct.unpack_from('>I', data, off)[0]
        if word == 0x48000000 or (word >> 26 == 16 and word & 0xFFFF == 0):  # b . / bc ...,$ (not linking, relative)
            k = bisect.bisect_right(starts, 0x82000000 + off) - 1
            if k >= 0:
                halts.add(f'sub_{starts[k]:08X}')
    return sorted(halts)


# Self-branches GCC made from paths the original code takes forever too (never taken in practice), checked one by one
# in the Switch build of 2026-10-20 (the source line of each `b .` from a -S -g1 compile of its file):
KNOWN_FAITHFUL = {
    'sub_82605ED8': "the guest's own register-only spin (cmplw cr6,r11,r9 / beq back)",
    'sub_8263ABE0': 'list walk: obj = node - 320; a null obj skips to the check without advancing node (cmplwi r28,0 / bne)',
    'sub_8263ACE8': 'the same list walk (cmplwi r29,0 / bne)',
    'sub_82B15D88': 'list search: at the end r10 = 0 and, the entry not found, it searches again from the end forever',
    'sub_82B16990': 'the same list search, inlined',
    'sub_829EA4E8': 'an unreachable block (after an unconditional branch, no branch to it)',
}
KNOWN_HALTS = guest_halts() + sorted(KNOWN_FAITHFUL)
DEVKITA64 = next((d + '/devkitA64/bin/' for d in (os.environ.get('DEVKITPRO', ''), 'C:/devkitPro', '/opt/devkitpro')
                  if d and os.path.isdir(d + '/devkitA64/bin')), 'C:/devkitPro/devkitA64/bin/')
# Vector fmla/fmls that are the guest's own fused multiply-adds, not contraction: two scalar std::fma (fmadds) of the
# generated code that GCC's SLP vectorizer packed into one 2-lane double fmla (each lane is still one fused operation,
# rounded to float afterwards as before, so the results are bit-identical). Function -> count, with the evidence.
KNOWN_VECTOR_FMA = {}  # mhnwis: SA2's pairings do not apply; a new one is checked and listed here with its evidence
EXE = '.exe' if os.name == 'nt' else ''


def generated_calls():
    """name -> the recompiled functions its generated C++ body calls directly (app/generated/*/ *_recomp.*.cpp)."""
    import glob
    out = {}
    head = re.compile(r'^DEFINE_REX_FUNC\((sub_[0-9A-F]{8})\) \{$', re.M)
    call = re.compile(r'\b(?:__imp__)?(sub_[0-9A-F]{8})\(ctx, base\)')
    for path in glob.glob(os.path.join(ROOT, 'app', 'generated', '*', '*_recomp.*.cpp')):
        text = open(path, encoding='utf-8', errors='replace').read()
        heads = list(head.finditer(text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            out[m.group(1)] = set(call.findall(text, m.end(), end))
    return out


def chain_to(calls, f, targets, depth=4, seen=()):
    """The shortest-first chain of direct calls from f to one of the targets, at most `depth` calls long, or None."""
    callees = calls.get(f, set())  # mhnwis: a set (a tuple cannot be intersected)
    hit = sorted(callees & targets)
    if hit:
        return [f, hit[0]]
    if depth > 1:
        for c in sorted(callees):
            if c not in seen:
                rest = chain_to(calls, c, targets, depth - 1, seen + (f,))
                if rest:
                    return [f] + rest
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--elf', default=os.path.join(ROOT, 'out', 'nx', 'mhnwis'))
    ap.add_argument('--nro', default=os.path.join(ROOT, 'out', 'nx', 'mhnwis.nro'))
    ap.add_argument('--halts', default=','.join(KNOWN_HALTS),
                    help='the recompiled functions with a genuine guest halt (b . in the original PowerPC code)')
    ap.add_argument('--sdk-vulkan', default='C:/devkitPro/mesa-switch-main-nfsmw-source/mesa-switch-main/'
                    'mesa-unified-install/opt/devkitpro/portlibs/switch/lib/libvulkan.a')
    a = ap.parse_args()
    failures = []

    nm = subprocess.run([DEVKITA64 + 'aarch64-none-elf-nm' + EXE, a.elf], capture_output=True, text=True).stdout
    start = next((int(l.split()[0], 16) for l in nm.splitlines() if l.endswith(' _start')), None)
    print(f'_start at {start:#x}' if start is not None else '_start not found')
    if start != 0:
        failures.append('_start is not at address 0')

    nro = open(a.nro, 'rb').read()
    # mhnwis: this port uses the generator's classic flavour (sa2-nx ships its optimised one): reported, not a failure.
    if b'optimised codegen' not in nro:
        print('flavour: classic codegen (this port does not use sa2-nx\'s optimised flavour yet)')
    else:
        print('flavour: optimised codegen')
    mesa = sorted(set(re.findall(rb'Mesa \d+\.\d+\.\d+ \(git-[0-9a-f]+\)', nro)))
    nvk = sum(1 for l in nm.splitlines() if ' nvk_' in l)
    if nvk == 0:
        # 1.0.3 on: a build without the driver (REXGLUE_SWITCH_NO_NVK, Renut on deko3d) must carry none of Mesa's
        # driver: no nvk_ symbol (above) and no Mesa version string.
        print('Vulkan driver: none linked (no nvk_ symbols); Mesa in the NRO:', [m.decode() for m in mesa])
        if mesa:
            failures.append('a build without the NVK driver carries a Mesa version string')
    else:
        sdk = sorted(set(re.findall(rb'Mesa \d+\.\d+\.\d+ \(git-[0-9a-f]+\)', open(a.sdk_vulkan, 'rb').read())))
        print('Mesa in the NRO:', [m.decode() for m in mesa], '| in the SDK:', [m.decode() for m in sdk])
        if not mesa or mesa != sdk:
            failures.append('the NRO does not carry the SDK driver\'s Mesa string')

    # One streaming pass over the disassembly: per function, b-to-self and fused multiply-adds.
    proc = subprocess.Popen([DEVKITA64 + 'aarch64-none-elf-objdump' + EXE, '-d', '--no-show-raw-insn', a.elf],
                            stdout=subprocess.PIPE, text=True, errors='replace', bufsize=1 << 20)
    func = None
    self_loops = []
    vector_fma = collections.Counter()
    scalar_fma = 0
    head = re.compile(r'^[0-9a-f]+ <([^>]+)>:$')
    ins = re.compile(r'^\s+([0-9a-f]+):\s+(\S+)\s*(.*)$')
    for line in proc.stdout:
        m = head.match(line)
        if m:
            func = m.group(1)
            continue
        m = ins.match(line)
        if not m or not func:
            continue
        addr, op, args = m.groups()
        guest = func.startswith(('sub_8', '__imp__sub_8'))
        if op == 'b' and args.split(' ')[0] == addr:
            if guest:
                self_loops.append(func)
        elif op in ('fmla', 'fmls') and guest:
            vector_fma[func] += 1
        elif op in ('fmadd', 'fmsub', 'fnmadd', 'fnmsub') and guest:
            scalar_fma += 1
    proc.wait()
    known = set(a.halts.split(','))
    functions = {f.replace('__imp__', '') for f in self_loops}
    unknown = sorted(functions - known)
    # Round 7: GCC may inline a known halt into a caller (non_volatile_as_local made the callees smaller: the halts of
    # sub_828DB988 and sub_8293FA08 then appear in sub_828D71E8 and sub_8293FE28), and with a higher inline limit
    # that caller into its own caller (sub_828C5D60 inlines sub_828D71E8). A function whose generated body reaches
    # a known-halt function through at most four direct calls is accepted, and named with the chain.
    inlined = []
    if unknown:
        calls = generated_calls()
        for f in list(unknown):
            chain = chain_to(calls, f, known)
            if chain:
                inlined.append(f'{f} (inlines {" -> ".join(chain[1:])})')
                unknown.remove(f)
    print(f'branch-to-self in recompiled functions: {len(self_loops)} instructions in {len(functions)} functions, '
          f'{len(functions & known)} of them known guest halts'
          + (f'; {len(inlined)} more calling one that GCC inlined: {"; ".join(inlined)}' if inlined else ''))
    if unknown:
        failures.append('branch-to-self outside the known guest halts (a polling loop without its barrier?): '
                        + ', '.join(unknown[:20]))
    paired = {k: v for k, v in vector_fma.items() if KNOWN_VECTOR_FMA.get(k) == v}
    leaked = collections.Counter({k: v for k, v in vector_fma.items() if k not in paired})
    print(f'fused multiply-adds in recompiled functions: scalar {scalar_fma} (the guest\'s own), vector '
          f'{sum(leaked.values())} in {len(leaked)} functions (must be 0)'
          + (f'; {sum(paired.values())} more the guest\'s own fmadds paired by GCC (KNOWN_VECTOR_FMA: '
             f'{", ".join(sorted(paired))})' if paired else ''))
    if leaked:
        failures.append('vector fmla/fmls in recompiled code (contraction leaked, or a new pairing of the guest\'s '
                        'own fmadds to check and add to KNOWN_VECTOR_FMA): '
                        + ', '.join(f'{k} x{v}' for k, v in leaked.most_common(10)))
    if failures:
        print('\nFAILED:\n  - ' + '\n  - '.join(failures))
        sys.exit(1)
    print('\nall checks passed')


if __name__ == '__main__':
    main()
