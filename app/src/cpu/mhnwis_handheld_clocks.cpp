// Monster High: the handheld clocks (mhnwis_handheld_gpu_mhz, mhnwis_handheld_emc_1600).
//
// The first console runs with sa2_gpu_boost (GPU 460.8 MHz, memory 1331.2) were GPU-bound: 21-27 ms of GPU work a
// frame in gameplay, 38-47 fps (log of 2026-10-20 21:28; the scene's shadow pass, resolves and three scene shaders,
// already early-Z and alpha-specialised). The docked clocks (GPU 768, memory 1600) are 1.67x the GPU, the user's call
// (2026-10-21, "make the nro with those profiles") instead of sys-clk.
//
// How, after switch_apm.cpp's lessons (sa2-nx sdk/src/ui): pcv reimposes the memory clock of the active apm
// configuration, so the memory comes from the configuration itself (0x92220007: GPU 460.8 + EMC 1600, an official
// handheld one), and the GPU is raised above it with clkrst, as sys-clk does, checked again every second (a mode change
// or waking from sleep applies the configuration's clocks again). Docked: nothing is touched. At the end the
// configuration the console had is requested again, which puts its clocks back.
// WHY IT IS EXACT: clocks, not settings: the same frames are drawn, sooner.
// RISK: more power draw and heat in handheld mode (the docked clocks, not above them).
#include "cpu/mhnwis_handheld_clocks.h"

#include <atomic>
#include <thread>

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/platform.h>

#include "cpu/sa2_enhancements.h"

#if REX_PLATFORM_SWITCH
#include <switch.h>
#endif

REXCVAR_DEFINE_INT32(mhnwis_handheld_gpu_mhz, 768, "MHNWIS",
                     "Handheld GPU clock in MHz, held by the game while it runs: 768 = the docked clock (default). "
                     "460 or less: sa2_gpu_boost's official 460.8 MHz profile instead, nothing held. Read at start")
    .range(0, 768)
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(mhnwis_handheld_emc_1600, true, "MHNWIS",
                    "With mhnwis_handheld_gpu_mhz above 460: the memory at 1600 MHz in handheld mode (the docked "
                    "clock; configuration 0x92220007) instead of 1331.2 (0x92220008). Read at start")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace mhnwis::clocks {

#if REX_PLATFORM_SWITCH
namespace {

constexpr u32 kConfigEmc1600 = 0x92220007u;  // GPU 460.8, EMC 1600
constexpr u32 kConfigEmc1331 = 0x92220008u;  // GPU 460.8, EMC 1331.2
constexpr u32 kMarginHz = 20000000u;
constexpr int kReportEverySeconds = 60;

std::atomic<bool> g_stop{false};
std::thread g_thread;
u32 g_config_original = 0;
bool g_has_original = false;

bool ClockOf(PcvModuleId module, u32 &hz) {
  hz = 0;
  ClkrstSession session{};
  if (R_FAILED(clkrstOpenSession(&session, module, 3))) return false;
  const bool ok = R_SUCCEEDED(clkrstGetClockRate(&session, &hz));
  clkrstCloseSession(&session);
  return ok;
}

bool SetClock(PcvModuleId module, u32 hz) {
  ClkrstSession session{};
  if (R_FAILED(clkrstOpenSession(&session, module, 3))) return false;
  const bool ok = R_SUCCEEDED(clkrstSetClockRate(&session, hz));
  clkrstCloseSession(&session);
  return ok;
}

void Hold(u32 gpu_hz, u32 config) {
  bool handheld_before = false;
  bool told = false;
  int raises = 0, raises_reported = 0, failures = 0;
  for (int second = 0; !g_stop.load(std::memory_order_relaxed); ++second) {
    ApmPerformanceMode mode = ApmPerformanceMode_Invalid;
    const bool handheld = R_SUCCEEDED(apmGetPerformanceMode(&mode)) && mode == ApmPerformanceMode_Normal;
    if (handheld != handheld_before) {
      REXLOG_INFO("[clocks] {}", handheld ? "handheld: holding the clocks" : "docked: the console's own clocks");
      handheld_before = handheld;
      told = false;
    }
    if (handheld) {
      u32 current = 0;
      if (R_SUCCEEDED(apmGetPerformanceConfiguration(ApmPerformanceMode_Normal, &current)) && current != config &&
          R_FAILED(apmSetPerformanceConfiguration(ApmPerformanceMode_Normal, config)) && failures++ == 0) {
        REXLOG_WARN("[clocks] configuration 0x{:08X} refused (was 0x{:08X})", config, current);
      }
      u32 gpu = 0, emc = 0;
      if (ClockOf(PcvModuleId_GPU, gpu) && gpu + kMarginHz < gpu_hz) {
        if (SetClock(PcvModuleId_GPU, gpu_hz)) {
          ++raises;
        } else if (failures++ == 0) {
          REXLOG_WARN("[clocks] clkrst refused the GPU clock {:.1f} MHz (it is at {:.1f})", gpu_hz / 1e6, gpu / 1e6);
        }
      } else if (!told && gpu && ClockOf(PcvModuleId_EMC, emc)) {
        REXLOG_INFO("[clocks] handheld: GPU {:.1f} MHz, memory {:.1f} MHz", gpu / 1e6, emc / 1e6);
        told = true;
      }
    }
    if (second % kReportEverySeconds == kReportEverySeconds - 1 && raises != raises_reported) {
      REXLOG_INFO("[clocks] the GPU was put back to {:.1f} MHz {} times in all", gpu_hz / 1e6, raises);
      raises_reported = raises;
    }
    for (int i = 0; i < 10 && !g_stop.load(std::memory_order_relaxed); ++i) svcSleepThread(100000000ULL);
  }
}

}  // namespace
#endif

void Start() {
  const int32_t mhz = REXCVAR_GET(mhnwis_handheld_gpu_mhz);
  if (mhz <= 460) {
    sa2::enh::ApplyGpuBoost();
    return;
  }
#if REX_PLATFORM_SWITCH
  if (R_FAILED(clkrstInitialize())) {
    REXLOG_WARN("[clocks] no clkrst: sa2_gpu_boost's 460.8 MHz profile instead");
    sa2::enh::ApplyGpuBoost();
    return;
  }
  g_has_original = R_SUCCEEDED(apmGetPerformanceConfiguration(ApmPerformanceMode_Normal, &g_config_original));
  const u32 config = REXCVAR_GET(mhnwis_handheld_emc_1600) ? kConfigEmc1600 : kConfigEmc1331;
  REXLOG_INFO("[clocks] handheld: GPU {} MHz over configuration 0x{:08X} (the console's: 0x{:08X})", mhz, config,
              g_has_original ? g_config_original : 0u);
  g_thread = std::thread(Hold, u32(mhz) * 1000000u, config);
#endif
}

void Stop() {
#if REX_PLATFORM_SWITCH
  if (!g_thread.joinable()) return;
  g_stop.store(true, std::memory_order_relaxed);
  g_thread.join();
  if (g_has_original) apmSetPerformanceConfiguration(ApmPerformanceMode_Normal, g_config_original);
  clkrstExit();
  REXLOG_INFO("[clocks] the console's configuration 0x{:08X} again", g_config_original);
#endif
}

}  // namespace mhnwis::clocks
