#!/usr/bin/env bash
# The SD card folder of the Switch build (sa2-nx's tools/win/package_switch.ps1, for Linux):
#   out/nx/sdcard/switch/mhnwis-nx/mhnwis.nro
#   out/nx/sdcard/switch/mhnwis-nx/game_root/      with --with-game: a copy of your game files (assets/game_root)
# Copy out/nx/sdcard/switch to the card's root (it merges with the card's switch folder).
#
# At the first start the game packs game_root into game_root.nxpack + .nxidx next to the NRO (a few minutes; the log
# shows "[pack] packing N %"); after that the folder can be deleted. Logs go to logs/ in the same folder.
#
# Everything in this folder is for your own console only: the NRO holds the game's translated code and shaders, and
# game_root is your copy of the game. Never share either.
#
#   tools/package_switch.sh [--with-game]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
nro="$root/out/nx/mhnwis.nro"
dest="$root/out/nx/sdcard/switch/mhnwis-nx"
[[ -f "$nro" ]] || { echo "no $nro: run tools/build_switch.sh first" >&2; exit 1; }
mkdir -p "$dest"
cp "$nro" "$dest/mhnwis.nro"
if [[ "${1:-}" == "--with-game" ]]; then
  [[ -f "$root/assets/game_root/Default.xex" ]] || { echo "no assets/game_root/Default.xex" >&2; exit 1; }
  rm -rf "$dest/game_root"
  cp -rL "$root/assets/game_root" "$dest/game_root"
fi
du -sh "$dest"
find "$root/out/nx/sdcard" -maxdepth 3 | sed "s|$root/out/nx/||"
