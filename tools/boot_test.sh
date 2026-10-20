#!/usr/bin/env bash
# One test run of the PC build (Linux counterpart of sa2-nx tools/win/boot_test.ps1): always muted and minimized,
# stopped after N seconds (default 45), then the end of the log.
#
#   tools/boot_test.sh [seconds] [extra mhnwis options]
#
# Log: out/pc/boot.log (the game's log), out/pc/boot_stdout.log (stdout/stderr, e.g. a crash before logging starts).
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
secs="${1:-45}"
shift || true
cd "$root/out/pc"
# The SDK builds its shared libraries (librexruntime*.so, libTracyClient*.so) into its own output folder; the
# executable's RUNPATH is only $ORIGIN.
sa2="${SA2_NX:-$root/../sa2-nx}"
export LD_LIBRARY_PATH="$sa2/sdk/out/linux-amd64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
rm -f boot.log
timeout --signal=TERM --kill-after=10 "$secs" ./mhnwis --audio_mute --window_start_minimized \
  --log_file="$root/out/pc/boot.log" "$@" > boot_stdout.log 2>&1
code=$?
if [[ $code -eq 124 ]]; then echo "== still running after ${secs}s (stopped by the test)"; else echo "== exited with code $code"; fi
echo "== last lines of boot.log:"
tail -n 40 boot.log 2>/dev/null || echo "(no boot.log)"
echo "== last lines of stdout/stderr:"
tail -n 15 boot_stdout.log
