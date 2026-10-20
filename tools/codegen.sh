#!/usr/bin/env bash
# Translates Default.xex to C++ with the sa2-nx host code generator (Linux counterpart of sa2-nx tools/codegen.ps1).
#
#   tools/codegen.sh [extra rexglue codegen options, e.g. --ignore-stamp]
#
# Input:   assets/game_root/Default.xex, app/mhnwis_manifest.toml
# Output:  app/generated/ (not committed), out/codegen.log, out/default_image.bin (the decrypted image)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
rexglue="${REXGLUE:-$sa2/sdk/out/linux-amd64/rexglue}"
[[ -x "$rexglue" ]] || { echo "rexglue not found at $rexglue; build it first" >&2; exit 1; }
mkdir -p "$root/out"
export REX_MAX_JUMP_TABLE_ENTRIES=1024
export REXGLUE_DUMP_IMAGE="$root/out/default_image.bin"
cd "$root/app"
set +e
"$rexglue" codegen mhnwis_manifest.toml "$@" > "$root/out/codegen.log" 2>&1
code=$?
set -e
tail -n 30 "$root/out/codegen.log"
exit $code
