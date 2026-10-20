#!/usr/bin/env bash
# Configures (first time) and builds the Linux PC build: out/pc/mhnwis. Logs: out/pc_configure.log, out/pc_build.log.
#
#   tools/build_pc.sh [-j N]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
build="$root/out/pc"
jobs="${2:-$(nproc)}"
mkdir -p "$root/out"
if [[ ! -f "$build/build.ninja" ]]; then
  cmake -S "$root/app" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_C_FLAGS=-march=x86-64-v2 -DCMAKE_CXX_FLAGS=-march=x86-64-v2 \
    -DREXSDK_DIR="$sa2/sdk" > "$root/out/pc_configure.log" 2>&1 \
    || { tail -n 30 "$root/out/pc_configure.log"; exit 1; }
fi
set +e
cmake --build "$build" --target mhnwis -j "$jobs" > "$root/out/pc_build.log" 2>&1
code=$?
set -e
grep -E 'error:|FAILED' "$root/out/pc_build.log" | head -n 40 || true  # no match is the good case
tail -n 3 "$root/out/pc_build.log"
exit $code
