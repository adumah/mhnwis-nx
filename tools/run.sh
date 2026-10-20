#!/usr/bin/env bash
# Plays the PC build (out/pc/mhnwis). Options are passed on, e.g. tools/run.sh --audio_mute
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
# The SDK builds its shared libraries (librexruntime*.so, ...) into its own output folder; the executable's RUNPATH
# is only $ORIGIN.
export LD_LIBRARY_PATH="$sa2/sdk/out/linux-amd64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
[[ -x "$root/out/pc/mhnwis" ]] || { echo "out/pc/mhnwis not found: build it first (tools/build_pc.sh)" >&2; exit 1; }
cd "$root/out/pc"
exec ./mhnwis "$@"
