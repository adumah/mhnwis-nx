# Direct3D census (for Renut's deko3d renderer)

The Switch build follows sa2-nx's `docs/deko3d-renderer-guide.md`: Renut's renderer hooks about twenty of the
game's XDK Direct3D functions and reads the device's state at fixed offsets. This file records which function is
which in Monster High's `Default.xex`, and why, as the guide asks ("name the source of every one").

Tools: `tools/d3d/fnindex.py` (listings and call graph from the generated code), `tools/d3d/census_build.py` and
`tools/d3d/census_report.py` (a diagnostic build that counts every call in 0x8264E000-0x82698000; first run
2026-10-20: boot, title, Load Game, gameplay in the courtyard; 1,545 frames in the 140-168 s window).

## The device layout is SA2's

The game links XDK 2.0.21256 (D3D9, XGRAPHC); SA2 links 2.0.21076. Every offset checked is SA2's:

| What | SA2 (sa2-nx `gpu/d3d/d3d.h`, `d3d_native.h`) | Monster High | Evidence |
|---|---|---|---|
| Device size, alignment | 0x6080, 0x80 | 0x6080, 0x80 | `sub_8265E2D8`: `li r3,24704`, `li r4,128`, then the allocator |
| Behavior flags (CreateDevice arg 4) | +24392 | +24392 | `sub_8265E2D8`: `stw r30,24392(r31)` |
| Ring, ring limit, ring guarantee | +0x30, +0x34, +0x38 | same | KickOff returns +48; BeginRingBig compares +48 + 4n with +52; the packet writers test +48 against +56 |
| Fence completion pointer, fence tag | +11024, +11036 | same | IsFencePending, BlockOnFence: `tag - fence < tag - *completion` |
| Flags bytes | +11068..+11071 | same | KickOff, KickOffSegment, the segment allocator |
| In KickOff | +13600 | same | KickOff, BlockOnFence |
| Command buffer being recorded | +13920 | same | AllocateInlineData, the segment allocator, KickOffSegment |
| Side buffer | +17136 | same | the segment allocator |
| End of inline vertices | +13844 | same | DrawVerticesUP sets the ring to it after the copy |
| Swap count | +16968 | same | Swap: `lwz r11,16968(r31)` / `addi r11,r11,1` |
| Index buffer, render targets [4], depth | +12812, +12816, +12832 | same | D3DResource_IsSet (`sub_8265BD98`), DrawIndexedVertices, ClearF |
| Stream sources [16], textures [26] | +12836, +12920 | same | D3DResource_IsSet loops 16 / 26 slots from these |
| Vertex declaration, vertex shader, pixel shader | +12240, +13072, +13068 | same | D3DResource_IsSet |
| Vertex shader: container, physical part | +0x368, +0x20 | same | XGRegisterVertexShader (`sub_8266AC10`) |
| Pixel shader: physical part | +0x18 | same | XGRegisterPixelShader (`sub_82667AE0`) |

The offsets of SA2's table not listed here are not checked yet; with this many identical ones, the working assumption is
that they are the same too, to be confirmed as the renderer reads them.

## Functions identified (21 of 22; the 22nd is not linked)

| Function | SA2 | Monster High | Evidence |
|---|---|---|---|
| Direct3D_CreateDevice | 8254FC10 | **8265E2D8** | Allocates the 0x6080-byte device, E_OUTOFMEMORY on failure, device type 2 takes the no-hardware path, arg 4 at +24392, hardware path `sub_82683408`. Census: once. |
| CDevice::KickOff | 8254EBB8 | **82673110** | 121 callers; checks +13600 and the flags, waits on fence tag - 2 through BlockOnFence, returns the ring (+48). |
| CDevice::KickOffSegment | 8254E830 | **82672D88** | 0x388 before KickOff, as in SA2; called by KickOff; writes the segment's indirect-buffer packet (+15332, +13920). |
| CDevice::BeginRingBig | 8254EDF8 | **826733B8** | (device, count): ring + 4 * count > limit -> KickOff, then the segment allocator; returns the ring. |
| Ring segment allocator | 8254DA90 | **82671ED0** | (device, dwords); its callers are exactly SA2's: KickOffSegment, BeginRingBig, Swap. Uses +17136 and +13920. |
| RingBufferDeviceAllocate | 8254D4B8 | **826716D8** | AllocateInlineData calls it as (device, flags = 1, &size, alignment). |
| CDevice::AllocateInlineData | 8254D9A8 | **82671DE8** | (device, dwords, alignment): bytes = 4 * dwords, from the command buffer's allocator or RingBufferDeviceAllocate; 0xE8 before the segment allocator, as in SA2. |
| D3DDevice_SetRingBufferParameters | 8254EF40 | **not linked** | The ring set-up `sub_82673800` has three callers: CreateDevice's hardware path, a reset path and D3DDevice_Reset (`sub_8265DB70`, which passes the presentation parameters + 72). None takes D3DRING_BUFFER_PARAMETERS directly. |
| CDevice::BlockOnFence | 8254D6E8 | **82671A68** | (device, fence, type, no_kick): pending test, KickOff when the fence is the current one, then polls CBlocker::Check. |
| CBlocker::Check | 8254F400 | **8265D768** | The poll of BlockOnFence's loop (after the blocker's set-up `sub_8265D320`, before its end `sub_8265D350`). Census: ~315,000 calls a frame. |
| D3DDevice_IsFencePending | 8254ECF8 | **826719E8** | One argument; the device from the title or system global (KeGetCurrentProcessType == 2), as VdGlobalDevice. |
| D3DDevice_InsertCallback | 8254EEE8 | **82673600** | (device, type, callback, context): ring room, then the callback writer `sub_826726C0` (it stores into *(device + 11028) and writes an INTERRUPT packet); 22 instructions, SA2's size. |
| D3D::SynchronizeToPresentationInterval | 825589D8 | **82663DB8** | The only function setting the swap-pending flag (0x10 of +11069); 0x4C0 before Swap, as in SA2. Census: once a frame. |
| D3DDevice_Swap | 82558E98 | **82664278** | The only caller of VdSwap; increments +16968; copies the 24-byte scaler parameters. Census: once a frame. |
| D3DDevice_DrawVertices | 82565C60 | **826747A0** | Exactly 0x418 before DrawIndexedVertices, as in SA2; flushes state through `sub_82685550`. |
| D3DDevice_DrawIndexedVertices | 82566078 | **82674BB8** | Called from game code 388 times a frame; flushes the dirty state, reads the index buffer (+12812), writes the draw packets. |
| D3DDevice_DrawVerticesUP | 82565C18 | **82674178** | (device, type, count, data, stride): BeginVertices, copy count * stride, ring = +13844. |
| D3DDevice_BeginVertices | 82565758 | **82673CB8** | Called by DrawVerticesUP and the Swap path for the space the vertices go in. |
| D3DDevice_ClearF | 82563978 | **826629E0** | (device, flags, count, rects, ...): with count 0 the size comes from render target 0 (+12816) or the depth surface (+12832). 6.7 calls a frame. |
| D3DDevice_Resolve | 825656F8 | **82670E88** | A 19-instruction wrapper passing all eleven arguments (two from the stack) to the copy worker `sub_8266FD30`, which programs RB_COPY_CONTROL (0x2318) and the copy destination registers. Called by Present and game code. |
| XGRegisterVertexShader | 8255E658 | **8266AC10** | (shader, physical): type 6, reference 1, physical part at +0x20, container at +0x368. Called by CreateVertexShader (`sub_8266AD08`). Census: 1,308 calls. |
| XGRegisterPixelShader | 8255DBF8 | **82667AE0** | (shader, physical): type 7, reference 1, physical part at +0x18. Called by CreatePixelShader (`sub_8266AA98`). Census: 394 calls. |
| D3DDevice_CreateVertexDeclaration | 8255E198 | **82668088** | (elements): counts 12-byte elements to Stream 0xFF, allocates 56 + 12n, fills it with `sub_82667F98` (resource type 5), returns it. |
| D3DResource_Destroy | 8254A200 | **8265C778** | Called by D3DResource_Release (`sub_8265CA20`, the reference count at +4) when it reaches 0; waits through BlockOnFence. |

## Also found

- D3DDevice_CreateVertexShader `sub_8266AD08`, D3DDevice_CreatePixelShader `sub_8266AA98`, D3DResource_Release
  `sub_8265CA20`, D3DResource_IsSet `sub_8265BD98`, D3DDevice_Reset `sub_8265DB70`.
- D3DDevice_DrawIndexedVerticesUP: `sub_82674700` (copies vertices and indices after `sub_826741C0`). Linked, not run in
  the census, and not among SA2's hooks: Renut must cover it if the game uses it.
- The GPU interrupt callback `sub_82671458`; the hardware initialisation `sub_82682DD8` (VdInitializeEngines,
  VdSetGraphicsInterruptCallback); the ring set-up `sub_82673800`; the gamma ramp `sub_8267C7B8`.
- The functions writing DRAW_INDX with a constant header (`82691F80`, `82692EA0`, ...) and the PIX shader record
  `sub_8266CCE0` never ran: not on the game's path.

## Side finding: a busy-wait

CBlocker::Check (`sub_8265D768`, with `sub_82650958`) runs about 315,000 times a frame: Direct3D waits for the GPU by
spinning, which is why the main thread reads ~100 % CPU even at 60 fps. Renut completes fences on its own render
thread, so this wait goes away with the new renderer.
