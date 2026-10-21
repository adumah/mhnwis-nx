#!/usr/bin/env bash
# Configures (first time) and builds the Nintendo Switch NRO: out/nx/mhnwis.nro (sa2-nx's tools/win/build_switch.ps1,
# for Linux). Logs: out/nx_configure.log, out/nx_build.log.
#
# Before the first build: tools/build_pc.sh (the generated code and the game's shaders come from the PC tree),
# tools/deko3d_build_tools.sh and tools/renut/switch_shaders.sh.
#
# Renut draws on deko3d, so the NRO has no Vulkan driver (REXGLUE_SWITCH_NO_NVK). The SDK and plume still want an
# "NVK SDK" folder for their checks and Vulkan headers: out/nvk-stub holds the Khronos headers of the SDK and an empty
# libvulkan.a that is never linked.
#
#   tools/build_switch.sh [-j N]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
build="$root/out/nx"
jobs="${2:-$(nproc)}"
export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
stub="$root/out/nvk-stub"
if [[ ! -f "$stub/lib/libvulkan.a" ]]; then
  mkdir -p "$stub/lib"
  ln -sfn "$sa2/sdk/thirdparty/vulkan-headers/include" "$stub/include"
  "$DEVKITPRO/devkitA64/bin/aarch64-none-elf-ar" rcs "$stub/lib/libvulkan.a"
fi
mkdir -p "$root/out"
if [[ ! -f "$build/build.ninja" ]]; then
  cmake -S "$root/app" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE="$sa2/tools/switch/cmake/switch-devkitA64.cmake" -DDEVKITPRO="$DEVKITPRO" \
    -DREXSDK_DIR="$sa2/sdk" -DREXGLUE_SWITCH_NVK_SDK="$stub" -DREXGLUE_SWITCH_NO_NVK=ON \
    > "$root/out/nx_configure.log" 2>&1 || { tail -n 40 "$root/out/nx_configure.log"; exit 1; }
fi
set +e
cmake --build "$build" --target mhnwis -j "$jobs" > "$root/out/nx_build.log" 2>&1
code=$?
set -e
grep -E 'error:|FAILED|undefined reference' "$root/out/nx_build.log" | head -n 40 || true
tail -n 3 "$root/out/nx_build.log"
[[ $code -eq 0 ]] && ls -la "$build/mhnwis.nro"
exit $code
