# Direct3D census (for Renut's deko3d renderer)

The Switch build follows sa2-nx's `docs/deko3d-renderer-guide.md`: Renut's renderer hooks about twenty of the
game's XDK Direct3D functions and reads the device's state at fixed offsets. This file records which function is
which in Monster High's `Default.xex`, and why, as the guide asks ("name the source of every one").

Tools: `tools/d3d/fnindex.py` (listings and call graph from the generated code), `tools/d3d/census_build.py` and
`tools/d3d/census_report.py` (a diagnostic build that counts every call in 0x8264E000-0x82698000; first run
2026-10-20: boot, title, Load Game, gameplay in the courtyard; 1,545 frames in the 140-168 s window).

## The device layout is SA2's

The game links XDK 2.0.21256 (D3D9, XGRAPHC); SA2 links 2.0.21076. Every offset checked so far is SA2's:

| What | SA2 (sa2-nx `gpu/d3d/d3d.h`) | Monster High | Evidence |
|---|---|---|---|
| Device size, alignment | 0x6080, 0x80 | 0x6080, 0x80 | `sub_8265E2D8`: `li r3,24704`, `li r4,128`, then the allocator |
| Behavior flags (CreateDevice arg 4) | +24392 | +24392 | `sub_8265E2D8`: `stw r30,24392(r31)` |
| Swap count | +16968 | +16968 | `sub_82664278`: `lwz r11,16968(r31)` / `addi r11,r11,1` |
| Swap flags byte | +11069 | +11069 | `sub_82672040`: `lbz r10,11069(r3)` |
| Index buffer | +12812 | +12812 | `sub_82674BB8`: `lwz r24,12812(r31)` |

The remaining offsets of SA2's table still have to be checked one by one.

## Functions identified

| Function | SA2 | Monster High | Evidence |
|---|---|---|---|
| Direct3D_CreateDevice | 8254FC10 | **8265E2D8** | Allocates the 0x6080-byte device (128-aligned), returns E_OUTOFMEMORY (0x8007000E) on failure, device type 2 takes the no-hardware path (`cmpwi cr6,r29,2`), stores arg 4 at +24392, hardware path `sub_82683408` (calls `VdIsHSIOTrainingSucceeded`). Census: called once. |
| D3DDevice_Swap | 82558E98 | **82664278** | The only caller of `VdSwap`; increments the swap count at +16968; copies a 24-byte block from arg 2 (the scaler parameters). Census: exactly 1.00 call a frame. |
| D3DDevice_DrawIndexedVertices | 82566078 | **82674BB8** (likely) | Called directly from game code (`sub_8255A960`, `sub_8255B050`, ...); flushes the dirty state (`sub_826847A0` with register blocks 0x4000/0x4400), reads the index buffer at +12812, writes type-3 packets. Census: 388 calls a frame in gameplay; the only caller of the state flush `sub_82685550` that ran. To confirm: its arguments against SA2's hook. |

## Leads, not yet confirmed

- Ring submission: `sub_82672040` writes CP_RB_WPTR (0x7FC80714) and reads the swap flags +11069; 8 calls a frame. KickOff
  or KickOffSegment, or the code both call.
- `sub_82671458` is the GPU interrupt callback (the emulated GPU logs `SetInterruptCallback(82671458, ...)`).
- `sub_82682DD8` calls `VdInitializeEngines` and `VdSetGraphicsInterruptCallback` (the hardware initialisation).
- `sub_82673800` calls `VdInitializeRingBuffer` and `VdEnableRingBufferRPtrWriteBack`.
- `sub_8267C7B8` calls `VdGetCurrentDisplayGamma` (SA2's gamma-ramp setup `sub_825527D8` keeps the ramp at +15408).
- The other callers of the state flush `sub_82685550` (`8266EFA8`, `8266F200`, `8266FAD0`, `82673CB8`, `826741C0`,
  `826747A0`, `82675030`, ...) are draw variants that did not run in the first census (DrawVertices,
  DrawVerticesUP, BeginVertices and the tiling paths are among them).
- The functions that write DRAW_INDX packets with a constant header (`82691F80`, `82692EA0`, ...) are only reached
  through the function table and never ran: not the game's draw path.

## Side finding: a busy-wait

`sub_8265D768` and `sub_82650958` (3 instructions) run about 315,000 times a frame: Direct3D waits for the GPU by
spinning, which is why the main thread reads ~100 % CPU even at 60 fps. Renut completes fences on its own render
thread, so this wait changes with the new renderer anyway.

## Still to identify

KickOff, KickOffSegment, BeginRingBig, the ring segment allocator, RingBufferDeviceAllocate, AllocateInlineData,
SetRingBufferParameters, BlockOnFence, CBlocker::Check, IsFencePending, InsertCallback,
SynchronizeToPresentationInterval, DrawVertices, DrawVerticesUP, BeginVertices, ClearF, Resolve,
XGRegisterVertexShader, XGRegisterPixelShader, CreateVertexDeclaration, D3DResource_Destroy.
