#!/usr/bin/env bash
# Builds the code generator (rexglue) of the sa2-nx SDK fork on Linux. Run once after cloning sa2-nx next to this
# repository (or set SA2_NX). Logs: <sa2-nx>/out_host_configure.log, <sa2-nx>/out_host_build.log.
#
#   tools/build_sdk.sh [-j N]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
jobs="${2:-$(nproc)}"
[[ -d "$sa2/sdk" ]] || { echo "sa2-nx not found at $sa2: clone it there or set SA2_NX" >&2; exit 1; }
cd "$sa2"
python3 tools/fetch_thirdparty.py
# -march=x86-64-v2: the SDK's byte-swapping helpers use SSSE3 (tools/win/env.ps1 sets the same on Windows).
cmake -S sdk -B out/host -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_C_FLAGS=-march=x86-64-v2 -DCMAKE_CXX_FLAGS=-march=x86-64-v2 > out_host_configure.log 2>&1 \
  || { tail -n 30 out_host_configure.log; exit 1; }
cmake --build out/host --target rexglue -j "$jobs" > out_host_build.log 2>&1 \
  || { grep -E 'error:|FAILED' out_host_build.log | head -n 40; exit 1; }
echo "built $sa2/sdk/out/linux-amd64/rexglue"
