# Third-party notices and credits

This project is a port made with other people's work. None of it would exist without them.

## ReXGlue SDK

- Project: https://github.com/rexglue/rexglue-sdk
- Role: the static recompiler that translates the game's Xbox 360 PowerPC code to C++, and the runtime it runs on
  (kernel, filesystem, input, audio, and the emulated Xenos GPU used by this build).
- Used as: the fork in sa2-nx's `sdk/` folder, built from source (it is not included in this repository).
- ReXGlue builds on the Xenia Xbox 360 emulator (https://github.com/xenia-project) and was inspired by XenonRecomp
  (https://github.com/hedge-dev/XenonRecomp) and rexdex's recompiler (https://github.com/rexdex/recompiler).

Its license (BSD 3-Clause), as it appears in the SDK:

```
Copyright (c) 2026, Tom Clay <tomc@tctechstuff.com>

Portions of this software are derived from the Xenia project:
Copyright (c) 2022, Ben Vanik and Xenia project contributors
https://xenia.jp

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## sa2-nx

- Project: https://github.com/ChanseyIsTheBest/sa2-nx (GPL-3.0), the Nintendo Switch port of Sonic Adventure 2.
- Role:
  - its porting prompt, `docs/porting-a-360-game-prompt.md`, and porting guide, `docs/porting-guide.md`: this port
    followed their method, stage by stage;
  - its SDK fork (`sdk/`) and analysis tools (`tools/`), which this project builds with and calls;
  - `tools/pointer_fixpoint.py` in this repository is a modified copy of sa2-nx's tool of the same name (the
    changes are listed at its top).
- Because of that copied and adapted code, this project is distributed under the GPL-3.0 as well (see `LICENSE`).

## Renut's renderer (reNut, banjo-nx, sa2-nx)

- `app/src/renut_engine` is sa2-nx's copy of **reNut** by masterspike52 (https://github.com/masterspike52/reNut), the
  Direct3D-level renderer, as **banjo-nx** (Banjo-Kazooie: Nuts & Bolts) carries it with its deko3d back end and
  shader pipeline, retargeted by sa2-nx to SA2 and here to Monster High (`tools/renut/retarget.py`,
  `docs/d3d-census.md`). reNut has no licence file; its author permits reuse by these ports. banjo-nx's and
  sa2-nx's parts are GPL-3.0.
- `app/src/cpu/sa2_enhancements.*`, `app/src/me/sa2_render_mode.*` and `app/src/me/me_platform_compat.h` are sa2-nx's
  files, taken as they are (GPL-3.0).
- Used from the sa2-nx tree at build time, not included here: **plume** (MIT; with banjo-nx's deko3d back end),
  Renut's **XenosRecomp** (MIT) with zstd, smol-v and xxHash, **Dear ImGui** (MIT), and Microsoft's
  **DirectX Shader Compiler** (University of Illinois/NCSA and LLVM licences), installed into that tree from its
  official release.

## Switch build tools

- **deko3d**, **libnx** and devkitA64 from devkitPro (installed separately).
- **SPIRV-Cross** (KhronosGroup, Apache-2.0), tag vulkan-sdk-1.4.363.0, built by `tools/deko3d_build_tools.sh`.
- **uam** (zlib; SwitchWakerHD's patched 1.1.0, as sa2-nx carries it), built from the sa2-nx tree.
- `tools/renut/deko3d_*.py`, `tools/renut/renut_switch_shader_cache.py` and `tools/check_switch_build.py` are copies of
  sa2-nx's (and through it banjo-nx's, sasrt-nx's and nfsmw-nx's) tools, GPL-3.0, adapted as each file's header says.

## Game

Monster High: New Ghoul in School (developed by Torus Games, published by Little Orbit; Monster High is a trademark
of Mattel, Inc.) is not part of this repository, in any form. See the disclaimer in `README.md`. The homebrew menu
icon is made at build time from the player's own disc (`tools/disc_icon.py`) and is not in this repository; the
fallback icon (`app/switch/icon.jpg`, drawn by `tools/make_icon.py`) is original artwork, with no art from the game
or Mattel.
