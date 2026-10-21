#!/usr/bin/env bash
# From your own game disc to the Switch's SD card folder, in one command: every step of the README's Building and
# Switch sections, each skipped when it is already done, so the script can simply be run again.
#
#   tools/build_from_disc.sh <your extracted disc folder | your .iso> [options]
#
#   --jobs N            compile jobs (default 4: the translated game needs about 10 GB of memory at -j 4)
#   --skip-capture      do not open the PC game to capture shaders (use the ones already captured)
#   --add-captures DIR  add shaders captured elsewhere first, e.g. the Switch's /switch/mhnwis-nx/shader_capture
#                       copied to the PC
#
# Result: out/nx/sdcard/switch/mhnwis-nx (the NRO and your game files): copy out/nx/sdcard/switch to the card's root.
#
# The game's shaders: the game builds them while it plays (they are not stored plainly in its files), so the build
# can only translate the ones it has seen. The first time, this script opens the PC build: play for a while (the
# menus, making a ghoul, a few classes and places), then close it. It then counts what was captured against
# tools/renut/known_shaders.txt. A shader the Switch build lacks is drawn as nothing; the console captures it to
# /switch/mhnwis-nx/shader_capture, and --add-captures with that folder adds it at the next run.
#
# Needs: Linux x86-64 with clang, CMake 3.25+, Ninja, Python 3, Git, a Vulkan driver, the
# X11/XCB and Wayland development files, and devkitPro (devkitA64, libnx, deko3d, switch-tools).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sa2="${SA2_NX:-$root/../sa2-nx}"
sa2_commit="adf3a4eee524dcca5cd7c1b42454ddb8a09124a1"
jobs=4
capture=1
add_captures=""
game=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobs) jobs="$2"; shift 2 ;;
    --skip-capture) capture=0; shift ;;
    --add-captures) add_captures="$2"; shift 2 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) game="$1"; shift ;;
  esac
done
step() { printf '\n\033[1;35m== %s\033[0m\n' "$*"; }
die() { printf '\033[1;31m%s\033[0m\n' "$*" >&2; exit 1; }

step "Checking the tools"
for t in clang cmake ninja python3 git; do command -v "$t" >/dev/null || die "missing: $t"; done
export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
[[ -x "$DEVKITPRO/devkitA64/bin/aarch64-none-elf-gcc" ]] || die "missing: devkitPro's devkitA64 at $DEVKITPRO (set DEVKITPRO)"

step "Your game"
mkdir -p "$root/assets"
if [[ -e "$root/assets/game_root/Default.xex" || -e "$root/assets/game_root/default.xex" ]]; then
  echo "assets/game_root is already set up"
  [[ -z "$game" ]] || echo "(ignoring $game: delete assets/game_root to use another copy)"
else
  [[ -n "$game" ]] || die "give your extracted disc folder or your .iso: tools/build_from_disc.sh /path/to/game"
  if [[ -f "$game" ]]; then
    [[ -d "$sa2" ]] || git clone https://github.com/ChanseyIsTheBest/sa2-nx.git "$sa2"
    python3 "$sa2/tools/extract_iso.py" "$game" -o "$root/assets/game_root"
  else
    [[ -e "$game/Default.xex" || -e "$game/default.xex" ]] || die "no Default.xex in $game"
    ln -sfn "$(cd "$game" && pwd)" "$root/assets/game_root"
  fi
fi

step "sa2-nx (the SDK and tools), commit $sa2_commit"
if [[ ! -d "$sa2/.git" ]]; then
  git clone https://github.com/ChanseyIsTheBest/sa2-nx.git "$sa2"
fi
if [[ "$(git -C "$sa2" rev-parse HEAD)" != "$sa2_commit" ]]; then
  git -C "$sa2" checkout -q "$sa2_commit" || die "could not check out $sa2_commit in $sa2 (local changes there?)"
fi

step "The code generator and shader tools (once)"
[[ -x "$sa2/sdk/out/linux-amd64/rexglue" ]] || "$root/tools/build_sdk.sh" -j "$jobs"
"$root/tools/fetch_dxc.sh"
[[ -x "$root/out/deko3d_tools/uam-build/uam" && -x "$root/out/deko3d_tools/spirv-cross-build/spirv-cross" ]] || "$root/tools/deko3d_build_tools.sh"

step "Translating the game's code (about 3 minutes)"
"$root/tools/codegen.sh"

step "The PC build (the first one takes a while)"
"$root/tools/build_pc.sh" -j "$jobs"

dump="$root/out/renut_shader_dump"
mkdir -p "$dump"
if [[ -n "$add_captures" ]]; then
  step "Adding the shaders captured in $add_captures"
  n=0
  for f in "$add_captures"/ps_*.bin "$add_captures"/vs_*.bin; do
    [[ -f "$f" && ! -f "$dump/$(basename "$f")" ]] || continue
    cp "$f" "$dump/"; n=$((n + 1))
  done
  echo "$n new"
fi

count_shaders() {
  local have=0 known
  known=$(grep -v '^#' "$root/tools/renut/known_shaders.txt" | wc -l)
  while read -r name; do [[ -f "$dump/$name.bin" ]] && have=$((have + 1)); done \
    < <(grep -v '^#' "$root/tools/renut/known_shaders.txt")
  echo "$have of the $known known shaders captured ($(ls "$dump" | grep -c '\.bin$') in all)"
  [[ $have -ge $known ]]
}

if [[ $capture -eq 1 ]] && ! count_shaders; then
  step "Capturing the game's shaders on the PC"
  echo "The PC game opens now with the renderer the Switch uses. Play for a while: the menus, making a ghoul, a"
  echo "few classes and places. Each new place adds shaders. Close the window when you are done."
  read -r -p "Press Enter to start... " _
  "$root/tools/run.sh" --sa2_renderer=renut || true
  step "Adding them to the PC build"
  "$root/tools/build_pc.sh" -j "$jobs"
fi
count_shaders || echo "Missing ones are drawn as nothing on the Switch until captured (see the top of this script)."

step "The game's shaders for the Switch"
"$root/tools/renut/switch_shaders.sh"

step "The Switch build"
"$root/tools/build_switch.sh" -j "$jobs"
python3 "$root/tools/check_switch_build.py" --sdk-vulkan /nonexistent | tail -n 1

step "The SD card folder"
"$root/tools/package_switch.sh" --with-game

cat <<EOF

Done: $root/out/nx/sdcard/switch/mhnwis-nx
Copy out/nx/sdcard/switch to the root of your Switch's SD card, then start the game from the homebrew menu opened
through a game (hold R while starting a game), not from the album. The first start packs your game files into one
file and takes 4 to 7 minutes on a black screen: let it finish. That copy is for your own console only.
EOF
