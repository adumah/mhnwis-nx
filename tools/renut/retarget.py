#!/usr/bin/env python3
"""Retargets sa2-nx's Renut hooks (app/src/renut_engine, copied from sa2-nx) from SA2's Direct3D addresses to
Monster High's (docs/d3d-census.md). Only the code part of each line changes; comments keep describing SA2.

  - every SA2 address of the census table -> ours (hooks, REX_EXTERN, __imp__ calls);
  - BANJO_RENUT_HOOK_SHARED / _RAW_SHARED -> BANJO_RENUT_HOOK / _RAW: in sa2-nx, SA2's own native renderer hooks
    those six functions and yields to Renut; this port has no other renderer, so Renut's hooks must replace them;
  - the SetRingBufferParameters hook is dropped (not linked in this game);
  - the VdGlobalDevice import slot and the global qword copied into every device.

Idempotent: run again after re-copying renut_engine from sa2-nx. Prints every changed line.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE = os.path.join(ROOT, 'app', 'src', 'renut_engine')

ADDRESSES = {  # SA2 -> Monster High (docs/d3d-census.md)
    '8254FC10': '8265E2D8',  # Direct3D_CreateDevice
    '8254EBB8': '82673110',  # CDevice::KickOff
    '8254E830': '82672D88',  # CDevice::KickOffSegment
    '8254EDF8': '826733B8',  # CDevice::BeginRingBig
    '8254DA90': '82671ED0',  # ring segment allocator
    '8254D4B8': '826716D8',  # RingBufferDeviceAllocate
    '8254D9A8': '82671DE8',  # CDevice::AllocateInlineData
    '8254D6E8': '82671A68',  # CDevice::BlockOnFence
    '8254F400': '8265D768',  # CBlocker::Check
    '8254ECF8': '826719E8',  # D3DDevice_IsFencePending
    '8254EEE8': '82673600',  # D3DDevice_InsertCallback
    '825589D8': '82663DB8',  # D3D::SynchronizeToPresentationInterval
    '82558E98': '82664278',  # D3DDevice_Swap
    '82565C60': '826747A0',  # D3DDevice_DrawVertices
    '82566078': '82674BB8',  # D3DDevice_DrawIndexedVertices
    '82565C18': '82674178',  # D3DDevice_DrawVerticesUP
    '82565758': '82673CB8',  # D3DDevice_BeginVertices
    '82563978': '826629E0',  # D3DDevice_ClearF
    '825656F8': '82670E88',  # D3DDevice_Resolve
    '8255E658': '8266AC10',  # XGRegisterVertexShader
    '8255DBF8': '82667AE0',  # XGRegisterPixelShader
    '8255E198': '82668088',  # D3DDevice_CreateVertexDeclaration
    '8254A200': '8265C778',  # D3DResource_Destroy
    '8255CB20': '82683188',  # D3D::InitializePresentationParameters
    '8255C150': '826827B8',  # D3D::InitializeApiState
}
CONSTANTS = {
    'kVdGlobalDeviceImportSlot = 0x82000710': 'kVdGlobalDeviceImportSlot = 0x82000794',
    'kGlobalQwordVa = 0x82980268': 'kGlobalQwordVa = 0x82C68C38',
}
DROP = re.compile(r'^\s*BANJO_RENUT_HOOK\w*\(sub_8254EF40\b')  # SetRingBufferParameters: not linked
FILES = ['gpu/d3d/hooks/device.cpp', 'gpu/d3d/hooks/draw.cpp', 'gpu/d3d/hooks/shader.cpp', 'gpu/d3d/hooks/resource.cpp',
         'gpu/banjo_shared_hooks.h']


def retarget(code):
    code = code.replace('BANJO_RENUT_HOOK_RAW_SHARED(', 'BANJO_RENUT_HOOK_RAW(')
    code = code.replace('BANJO_RENUT_HOOK_SHARED(', 'BANJO_RENUT_HOOK(')
    code = re.sub(r'sub_([0-9A-F]{8})\b', lambda m: 'sub_' + ADDRESSES.get(m.group(1), m.group(1)), code)
    for a, b in CONSTANTS.items():
        code = code.replace(a, b)
    return code


changed = 0
for rel in FILES:
    path = os.path.join(ENGINE, rel)
    out = []
    for n, line in enumerate(open(path).read().split('\n'), 1):
        if DROP.match(line):
            print(f'{rel}:{n}: dropped: {line.strip()}')
            out.append('// mhnwis: SetRingBufferParameters is not linked in this game (docs/d3d-census.md); its hook '
                       'is dropped.')
            changed += 1
            continue
        stripped = line.lstrip()
        if stripped.startswith('//'):
            out.append(line)
            continue
        cut = line.find('//')
        code, comment = (line, '') if cut < 0 else (line[:cut], line[cut:])
        new = retarget(code) + comment
        if new != line:
            print(f'{rel}:{n}: {new.strip()[:150]}')
            changed += 1
        out.append(new)
    open(path, 'w').write('\n'.join(out))
print(f'{changed} lines changed', file=sys.stderr)
