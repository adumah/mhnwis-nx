// Monster High: the globals Renut's renderer links against that sa2-nx defines in SA2-specific files (its native
// renderer, its capture, its hot-guest code). Same definitions and defaults as sa2-nx's PC build.

#include <atomic>
#include <cstdint>

#include <rex/platform.h>

#include "cpu/sa2_enhancements.h"

// The game's swaps, counted by Renut's Swap hook (gpu/d3d/hooks/device.cpp); sa2-nx: sa2_capture.cpp.
std::atomic<uint64_t> g_sa2_game_frames{0};

// sa2-nx: me/me_native_system.cpp. Renut's frame pacing (gpu/sa2_renut_pacing.cpp) reads it: a late frame goes at
// once instead of at the next 1/60 s.
SA2_ENHANCEMENT(g_vsync_relaxed, sa2_vsync_relaxed, sa2::enh::kNonCpu, true,
                "Relaxed vsync: a frame that misses 60 fps is shown when it is ready instead of at the next vblank: no "
                "fall from 60 straight to 30");

// sa2-nx: cpu/sa2_hot_guest.cpp. Store cards (tools/store_cards.py marks in the generated code) are not generated
// for this game: Renut hashes its cached copies instead.
extern "C" const bool g_banjo_store_cards = false;

#if !REX_PLATFORM_SWITCH
// sa2-nx: me/me_pc_stubs.cpp. The Switch profiler's counters; nothing to count on the PC.
extern "C" void RexSwitchPerfCount(unsigned) {}
#endif
