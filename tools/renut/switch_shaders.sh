#!/usr/bin/env bash
# The game's shaders for the Switch build, from the PC build (sa2-nx docs/renut-renderer.md, "Shaders for the
# Switch"): XenosRecomp's SPIR-V of every container in out/renut_shader_dump (captured by Renut on the PC), its GLSL
# for uam with fixed bindings, banjo-nx's GLSL passes (each output compiled with the PC uam: --check), the GLSL
# package and the SPIR-V cache the NRO links (out/renut_switch). Game data: never committed, never distributed.
#
#   tools/renut/switch_shaders.sh          (after tools/build_pc.sh and tools/deko3d_build_tools.sh)
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tools="$root/tools/renut"
sh="$root/out/deko3d_shaders"
recomp="$root/out/pc/xenos_recomp/build/XenosRecomp/XenosRecomp"
common="$root/app/src/renut_engine/gpu/shaders/xenos/shader_common.h"
[[ -x "$recomp" ]] || { echo "no $recomp: build the PC tree first (tools/build_pc.sh)" >&2; exit 1; }
cd "$root"

echo "== SPIR-V (XenosRecomp, the PC build's early alpha HLSL)"
rm -rf "$sh/spirv" && mkdir -p "$sh/spirv"
BANJO_DEKO3D_SPIRV_DIR="$sh/spirv" BANJO_HLSL_OVERRIDE="$root/out/pc/renut_gpu/early_alpha_hlsl" \
  "$recomp" "$root/out/renut_shader_dump" "$sh/spirv_pass.cpp" "$common" > "$sh/spirv_pass.log" 2>&1
echo "$(ls "$sh/spirv" | wc -l) SPIR-V files"

echo "== GLSL for uam"
rm -rf "$sh/glsl"
python3 "$tools/deko3d_shaders.py" --spirv "$sh/spirv" --out "$sh/glsl" --no-uam | tail -n 3

echo "== banjo-nx's passes, each checked with uam"
rm -rf "$sh/glsl_opt"
python3 "$tools/deko3d_glsl_opt.py" --in "$sh/glsl/glsl" --out "$sh/glsl_opt" --check | tail -n 5

echo "== the package and the SPIR-V cache"
python3 "$tools/deko3d_shader_package.py" --glsl "$sh/glsl_opt" --out "$root/out/renut_switch" | tail -n 3
python3 "$tools/renut_switch_shader_cache.py" --pc "$root/out/pc" | tail -n 3
ls -la "$root/out/renut_switch"
