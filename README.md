# mhnwis-nx

An unofficial, fan-made native port of the Xbox 360 game **Monster High: New Ghoul in School** to the **Nintendo
Switch** and **Linux**, made by static recompilation.

The game is fully ported from the Xbox 360: its code is translated to C++ ahead of time and compiled for the console,
not emulated, and it draws through a native Direct3D-level renderer (Renut) on the Switch's own graphics API
(deko3d). On a Switch Lite in handheld mode it runs at **60 fps** (the heaviest scenes dip briefly into the 50s).

> **This repository contains no game.** No game files, no game code (translated or not), no shaders, no assets, and
> no ready-made NRO. **You must bring your own disc**: you dump your own copy of the game, and the build turns it into
> a program for your own console. See [Disclaimer](#disclaimer).

## Status

| | |
|---|---|
| Nintendo Switch | **Playable, 60 fps** in handheld mode, with brief dips into the 50s in the heaviest scenes (tested on a Switch Lite) |
| Linux (x86-64) | Playable (boot, intro movies, menus, gameplay, saving and loading); 60 fps in most places on a Steam Deck |
| Controllers | Any controller plays as player 1; on the Switch, A is A (buttons by letter, as the game's prompts show) |
| Docked mode | Renders at 1920x1080; not tuned like handheld mode (all testing was handheld) |

Tested on a Steam Deck running CachyOS (clang 23.1.1) and a Switch Lite running homebrew.

> **The first start on the Switch takes 4 to 7 minutes to load.** The game packs your game files into one file on the
> SD card first, on a black screen. Let it finish and do not turn the console off. Later starts are quick.

## What you need

- **Your own copy of the game**: the Xbox 360 disc (USA), dumped by you. Either the extracted disc folder or the
  `.iso` works. `Default.xex` must be title ID `373407DA`, media ID `323E519F`, version 5 (the code generator prints
  these).
- Linux on x86-64 with: clang, CMake 3.25 or newer, Ninja, Python 3, Git, a Vulkan driver, and the X11/XCB and
  Wayland development files.
- For the Switch: [devkitPro](https://devkitpro.org/wiki/Getting_Started) with devkitA64, libnx, deko3d and
  switch-tools, and a console that runs homebrew.
- About 10 GB of free memory to compile (the translated game is ~144 MB of C++), and about 10 GB of disk.
- [sa2-nx](https://github.com/ChanseyIsTheBest/sa2-nx) next to this repository: its SDK fork and tools are used to
  build. The script below clones it at the commit this port was made with
  (`adf3a4eee524dcca5cd7c1b42454ddb8a09124a1`).

## Building for the Switch, in one command

```sh
git clone https://github.com/adumah/mhnwis-nx.git
mhnwis-nx/tools/build_from_disc.sh /path/to/your/extracted/disc     # or /path/to/your/game.iso
```

It sets up sa2-nx, builds the tools, translates the game's code, builds the PC version, captures the game's shaders,
builds the Switch version and makes the SD card folder. Every step that is already done is skipped, so it can be run
again at any time.

**The game's shaders.** The game builds its shaders while it plays, so the build can only translate the ones it has
seen. The first time, the script opens the PC version of the game: play for a while (the menus, making a ghoul, a few
classes and places), then close the window. The script counts what was captured against the 1699 known shaders
(`tools/renut/known_shaders.txt`). A shader the Switch build lacks is drawn as nothing; the console saves it to
`/switch/mhnwis-nx/shader_capture`, and copying that folder to the PC and running the script again with
`--add-captures /path/to/shader_capture` adds it.

Options: `--jobs N` (default 4), `--skip-capture`, `--add-captures DIR`. If sa2-nx lives somewhere else, set
`SA2_NX=/path/to/sa2-nx`.

## Installing on the Switch

1. Copy `mhnwis-nx/out/nx/sdcard/switch` to the root of the SD card (it merges with the card's `switch` folder). It
   holds `switch/mhnwis-nx/mhnwis.nro` and your game files.
2. Open the homebrew menu **through a game** (hold R while starting any game), not through the album: the album
   gives homebrew too little memory.
3. Start **Monster High: New Ghoul in School**. **The first start takes 4 to 7 minutes** (see above); after it,
   `switch/mhnwis-nx/game_root` can be deleted to free space.

Settings (`mhnwis.toml`) and logs (`logs/`) are kept in `switch/mhnwis-nx`.

**Handheld clocks.** In handheld mode the game raises the GPU to 768 MHz and the memory to 1600 MHz, the clocks the
console uses when docked, and gives the console's own clocks back when it quits. That is what makes 60 fps; it uses
more battery and runs warmer than other handheld games. `mhnwis_handheld_gpu_mhz = 460` in `mhnwis.toml` turns it
back to Nintendo's official 460.8 MHz handheld profile (about 40 fps). If you use sys-clk, give this game no sys-clk
profile.

## Building step by step (and the Linux version)

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

# 5. Build the PC version (the first build takes a while; -j 4 keeps memory use near 10 GB) and play it
mhnwis-nx/tools/build_pc.sh -j 4
mhnwis-nx/tools/run.sh

# 6. For the Switch: capture the shaders (play a while), build again, then the Switch build
mhnwis-nx/tools/run.sh --sa2_renderer=renut
mhnwis-nx/tools/build_pc.sh -j 4
mhnwis-nx/tools/deko3d_build_tools.sh     # SPIRV-Cross and uam for the PC (once)
mhnwis-nx/tools/renut/switch_shaders.sh   # the game's shaders for deko3d
mhnwis-nx/tools/build_switch.sh -j 4      # out/nx/mhnwis.nro
python3 mhnwis-nx/tools/check_switch_build.py --sdk-vulkan /nonexistent
mhnwis-nx/tools/package_switch.sh --with-game   # out/nx/sdcard
```

On Linux, saves are written to `~/.local/share/mhnwis/`.

## Tools

| Script | What it does |
|---|---|
| `tools/build_from_disc.sh` | Everything, from your disc to the Switch's SD card folder |
| `tools/build_sdk.sh` | Builds the sa2-nx SDK's code generator on Linux |
| `tools/fetch_dxc.sh` | Installs Microsoft's DirectX Shader Compiler (pinned release, checksum-checked) into the sa2-nx tree for Renut's shaders |
| `tools/codegen.sh` | Translates `Default.xex` to C++ (`app/generated/`), with `app/mhnwis_manifest.toml` |
| `tools/build_pc.sh`, `tools/run.sh` | Builds and plays the PC version |
| `tools/deko3d_build_tools.sh`, `tools/renut/switch_shaders.sh` | The Switch's shader chain |
| `tools/build_switch.sh`, `tools/check_switch_build.py`, `tools/package_switch.sh` | Builds, checks and packages the Switch version |
| `tools/boot_test.sh` | A muted, minimized test run with its log; takes scripted input (`--input_script=75:START`) and screenshots (`--mhnwis_screenshots=20,40`) |
| `tools/play.sh`, `tools/perf_report.py` | Plays while recording frame times, per-thread CPU and GPU load, and screenshots; then lists the slow spots |
| `tools/pointer_fixpoint.py` | Finds functions reached only through pointers (adapted from sa2-nx) |
| `tools/disc_icon.py` | Makes the homebrew menu icon from your disc's dashboard art (`out/nx_icon.jpg`, run by `tools/build_switch.sh`) |
| `tools/make_icon.py` | Draws the fallback icon (`app/switch/icon.jpg`, original artwork) for a disc without dashboard art |

`app/overrides.toml` holds every correction to the code generator's analysis, each with the evidence for it.

## Disclaimer

This is an unofficial, non-commercial fan project for preservation and personal use. It is not affiliated with,
endorsed by, sponsored by or connected to Mattel, Torus Games, Little Orbit, Microsoft or Nintendo.

**Monster High** and all related titles, characters, names, logos and marks are trademarks of, and copyright
**Mattel, Inc.** *Monster High: New Ghoul in School* is © its respective owners. Xbox 360 is a trademark of Microsoft;
Nintendo Switch is a trademark of Nintendo. All other trademarks belong to their owners. The homebrew menu icon is
made at build time from your own disc's dashboard art and is not in this repository; the fallback icon
(`app/switch/icon.jpg`) is original artwork made for this project, with no art from the game or from Mattel.

This repository contains **no part of the game**: no disc files, no assets, no executable, no shaders, and none of the
C++ the code generator produces from the game (`app/generated/` is never committed). It holds only this project's own
code, build scripts and analysis notes (addresses and descriptions of the game's code, needed to translate it
correctly). **Bring your own disc**: to play, you must own the game and use your own copy. The NRO and the SD card
folder you build contain the game's translated code and your game files: they are for your own console only. **Do
not share them, and do not ask for or share game files, NROs or download links.** Please support the official
releases.

## Credits

- **The game**: *Monster High: New Ghoul in School*, developed by **Torus Games** and published by **Little Orbit**,
  based on **Mattel**'s Monster High. All credit for the game itself goes to them.
- **[ReXGlue SDK](https://github.com/rexglue/rexglue-sdk)**, which turns Xbox 360 code into C++ and provides the
  runtime it runs on. ReXGlue builds on the [Xenia](https://github.com/xenia-project) emulator.
- **[sa2-nx](https://github.com/ChanseyIsTheBest/sa2-nx)** by ChanseyIsTheBest, the Xbox 360 to Switch port of
  Sonic Adventure 2, the reference for this port: its porting prompt (`docs/porting-a-360-game-prompt.md`) and porting
  guide were followed, and its SDK fork, tools, Switch platform layer and copy of Renut's renderer are used to build
  it.
- **[reNut](https://github.com/masterspike52/reNut)** by masterspike52, the Direct3D-level renderer, with
  **banjo-nx**'s deko3d back end.
- **devkitPro** (devkitA64, libnx, deko3d), **SPIRV-Cross** and **uam**, which make the Switch build possible.

Full notices and licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

GPL-3.0 (see [LICENSE](LICENSE)), because this project includes code adapted from sa2-nx. The game itself is not
covered: it is not here, and it belongs to its owners.
