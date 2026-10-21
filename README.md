# mhnwis-nx

An unofficial, fan-made native port of the Xbox 360 game **Monster High: New Ghoul in School** to Linux, made by
static recompilation. The Nintendo Switch version is the goal and is not done yet.

The game's code is translated to C++ ahead of time and compiled for your PC; it is not emulated. Graphics still go
through the SDK's emulated Xbox 360 GPU (Vulkan) in this build.

> **This repository contains no game.** No game files, no game code (translated or not), no assets. You need your own
> copy of the game, and the build turns it into a program on your own machine. See [Disclaimer](#disclaimer).

## Status

| | |
|---|---|
| Linux (x86-64) | Playable: boot, intro movies, menus, gameplay, saving and loading |
| Performance | 60 fps in most places on a Steam Deck; about 53-57 fps in large open rooms with many characters (the emulated GPU's cost) |
| Controllers | Any controller plays as player 1 |
| Renut's renderer | Experimental, PC: `tools/run.sh --sa2_renderer=renut` (menus and gameplay render; the emulated GPU stays the default) |
| Nintendo Switch | Not yet (Renut's deko3d back end comes next) |

Tested on a Steam Deck running CachyOS, with clang 23.1.1.

## What you need

- **Your own copy of the game**: the Xbox 360 disc (USA), dumped and extracted to a folder. `Default.xex` must be
  title ID `373407DA`, media ID `323E519F`, version 5 (the code generator prints these). An ISO can be extracted
  with sa2-nx's `tools/extract_iso.py`.
- Linux on x86-64 with: clang, CMake 3.25 or newer, Ninja, Python 3, Git, and a Vulkan driver. The SDK also needs
  the X11/XCB and Wayland development files.
- About 10 GB of free memory to compile (the translated game is ~144 MB of C++), and a few GB of disk.
- [sa2-nx](https://github.com/ChanseyIsTheBest/sa2-nx), cloned **next to** this repository: its SDK fork and tools
  are used to build. This port was made with sa2-nx commit `adf3a4eee524dcca5cd7c1b42454ddb8a09124a1`.

## Building

```sh
# 1. This repository and sa2-nx, side by side
git clone https://github.com/adumah/mhnwis-nx.git
git clone https://github.com/ChanseyIsTheBest/sa2-nx.git
git -C sa2-nx checkout adf3a4eee524dcca5cd7c1b42454ddb8a09124a1

# 2. The code generator and the shader compiler Renut's renderer needs (once)
mhnwis-nx/tools/build_sdk.sh
mhnwis-nx/tools/fetch_dxc.sh

# 3. Your game: link your extracted disc folder (the one holding Default.xex)
mkdir -p mhnwis-nx/assets
ln -s /path/to/your/extracted/disc mhnwis-nx/assets/game_root

# 4. Translate the game's code (about 3 minutes; written to app/generated/, never committed)
mhnwis-nx/tools/codegen.sh

# 5. Build the PC program (the first build takes a while; -j 4 keeps memory use near 10 GB)
mhnwis-nx/tools/build_pc.sh -j 4

# 6. Play
mhnwis-nx/tools/run.sh
```

If sa2-nx lives somewhere else, set `SA2_NX=/path/to/sa2-nx` for every script.

Saves are written to `~/.local/share/mhnwis/`.

## Tools

| Script | What it does |
|---|---|
| `tools/build_sdk.sh` | Builds the sa2-nx SDK's code generator on Linux |
| `tools/fetch_dxc.sh` | Installs Microsoft's DirectX Shader Compiler (pinned release, checksum-checked) into the sa2-nx tree for Renut's shaders |
| `tools/codegen.sh` | Translates `Default.xex` to C++ (`app/generated/`), with `app/mhnwis_manifest.toml` |
| `tools/build_pc.sh` | Builds `out/pc/mhnwis` |
| `tools/run.sh` | Plays |
| `tools/boot_test.sh` | A muted, minimized test run with its log; takes scripted input (`--input_script=75:START`) and screenshots (`--mhnwis_screenshots=20,40`) |
| `tools/play.sh`, `tools/perf_report.py` | Plays while recording frame times, per-thread CPU and GPU load, and screenshots; then lists the slow spots |
| `tools/pointer_fixpoint.py` | Finds functions reached only through pointers (adapted from sa2-nx) |

`app/overrides.toml` holds every correction to the code generator's analysis, each with the evidence for it.

## Renut's renderer and its shaders

Renut's Direct3D-level renderer (the route to the Switch, `docs/d3d-census.md`) draws with the game's shaders
translated ahead of time. They are game data, so the first build has none: run the game once with
`--sa2_renderer=renut` (it captures every shader it lacks into `out/pc/shader_capture/`), then build again, which
translates them into the program. Places the game had not shown yet are captured on the next visit.

## Disclaimer

This is an unofficial fan project for preservation and personal use. It is not affiliated with, endorsed by or
connected to Mattel, Torus Games, the game's publisher, Microsoft or Nintendo. Monster High and all related names
and marks belong to their owners.

This repository contains **no part of the game**: no disc files, no assets, no executable, and none of the C++ the
code generator produces from the game (`app/generated/` is never committed). It holds only this project's own code,
build scripts and analysis notes (addresses and descriptions of the game's code, needed to translate it correctly).
To play, you must own the game and use your own copy. Do not ask for or share game files.

## Credits

- **[ReXGlue SDK](https://github.com/rexglue/rexglue-sdk)**, which turns Xbox 360 code into C++ and provides the
  runtime it runs on. ReXGlue builds on the [Xenia](https://github.com/xenia-project) emulator.
- **[sa2-nx](https://github.com/ChanseyIsTheBest/sa2-nx)** by ChanseyIsTheBest: its porting prompt
  (`docs/porting-a-360-game-prompt.md`) and porting guide were followed for this port, and its SDK fork and tools
  are used to build it.

Full notices and licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

GPL-3.0 (see [LICENSE](LICENSE)), because this project includes code adapted from sa2-nx. The game itself is not
covered: it is not here, and it belongs to its owners.
