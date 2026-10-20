#!/usr/bin/env bash
# Plays the PC build normally (sound on, window shown) while recording what is needed to find slow spots afterwards:
#   out/pc/play/frames.csv    every frame's time and counters (the SDK's perf_log_csv)
#   out/pc/play/threads.csv   CPU use of every thread, each second (tools/thread_sampler.py)
#   out/pc/play/shots/        a screenshot every 10 s (to see where a slow spot was)
#   out/pc/play/game.log      the game's log
# Then: tools/perf_report.py out/pc/play
#
#   tools/play.sh [extra mhnwis options]
#   PLAY_SECONDS=120 tools/play.sh --audio_mute --window_start_minimized ...   (a timed test run)
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
export LD_LIBRARY_PATH="$sa2/sdk/out/linux-amd64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
play="$root/out/pc/play"
rm -rf "$play" "$root/out/pc/shots"
mkdir -p "$play"
cd "$root/out/pc"
shots="$(seq -s, 10 10 3600)"  # every 10 s for an hour
${PLAY_SECONDS:+timeout --signal=TERM --kill-after=10 "$PLAY_SECONDS"} ./mhnwis --perf_log_csv="$play/frames.csv" --log_file="$play/game.log" --mhnwis_screenshots="$shots" "$@" &
game=$!
# Sample the game itself: with PLAY_SECONDS, $! is the timeout wrapper, whose child is the game.
target="$game"
for _ in 1 2 3 4 5 6 7 8 9 10; do
  child="$(pgrep -P "$game" -x mhnwis | head -n 1)"
  [[ -n "$child" ]] && { target="$child"; break; }
  [[ -z "${PLAY_SECONDS:-}" ]] && break
  sleep 0.2
done
python3 "$root/tools/thread_sampler.py" "$target" "$play/threads.csv" &
wait "$game"
echo "game exited with code $?"
sleep 1.5  # the sampler notices the exit within a second
mv "$root/out/pc/shots" "$play/shots" 2>/dev/null
echo "recorded in $play; now: tools/perf_report.py $play"
