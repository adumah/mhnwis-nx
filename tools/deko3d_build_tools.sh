#!/usr/bin/env bash
# The PC tools the Switch build's deko3d shader chain needs (sa2-nx's tools/deko3d_build_tools.sh, for Linux), built
# into out/deko3d_tools:
#   SPIRV-Cross (KhronosGroup, Apache-2.0; pinned tag) for SPIR-V -> GLSL;
#   uam (sa2-nx's app/thirdparty/uam: SwitchWakerHD's patched 1.1.0) for GLSL -> deko3d shader binaries.
#
#   tools/deko3d_build_tools.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
out="$root/out/deko3d_tools"
spirv_cross_tag="vulkan-sdk-1.4.363.0"
mkdir -p "$out"
if [[ ! -d "$out/SPIRV-Cross/.git" ]]; then
  git clone -q --depth 1 --branch "$spirv_cross_tag" https://github.com/KhronosGroup/SPIRV-Cross.git "$out/SPIRV-Cross"
fi
cmake -S "$out/SPIRV-Cross" -B "$out/spirv-cross-build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DSPIRV_CROSS_ENABLE_TESTS=OFF -DSPIRV_CROSS_SHARED=OFF \
  -DSPIRV_CROSS_ENABLE_C_API=OFF > "$out/spirv-cross-configure.log" 2>&1
ninja -C "$out/spirv-cross-build" spirv-cross > "$out/spirv-cross-build.log" 2>&1
cmake -S "$sa2/app/thirdparty/uam" -B "$out/uam-build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ > "$out/uam-configure.log" 2>&1
ninja -C "$out/uam-build" uam_tool > "$out/uam-build.log" 2>&1
"$out/spirv-cross-build/spirv-cross" --help 2>&1 | head -n 1 || true
ls -la "$out/spirv-cross-build/spirv-cross" "$out/uam-build/uam"
