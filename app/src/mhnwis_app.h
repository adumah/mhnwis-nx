// Monster High: New Ghoul in School: the app (rex::ReXApp hooks). Stage 3, first boot: the SDK's emulated Xenos GPU,
// no game-specific hooks yet.

#pragma once

#include <filesystem>
#include <string>
#include <system_error>

#include <rex/cvar.h>
#include <rex/perf/counter.h>

#include <rex/filesystem.h>
#include <rex/input/device_assignment.h>
#include <rex/input/input_system.h>
#include <rex/rex_app.h>
#include <rex/runtime.h>

#include "mhnwis_screenshot.h"

REXCVAR_DECLARE(std::string, perf_log_csv);

class MhnwisApp : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<MhnwisApp>(new MhnwisApp(ctx, "mhnwis", PPCImageConfig));
  }

  // Defaults applied before mhnwis.toml (which may override any of them). The first boot ran without a GPU
  // ("VdInitializeRingBuffer: no GPU emulation loaded (gpu_plugin not set)", 2026-10-20): the emulated Xenos GPU is a
  // plugin, built by GPU_PLUGINS xenos in CMakeLists.txt and loaded by this setting.
  std::string_view BuiltInConfig() const override { return "gpu_plugin = \"xenos\"\n"; }

  void OnPostSetup() override {
    // Every controller plays as user 0, the only signed-in user (XamUserGetSigninState reports users 1-3 signed out).
    // With the SDK's default slot policy a second pad was user 1: Start on it at the title screen left the main menu
    // without its panel (background only), most likely waiting on a sign-in for user 1 (player's run, 2026-10-20:
    // Steam Deck controls = pad 0, Xbox Series X controller = pad 1; the same Start from user 0, by input_script, shows
    // the menu). Inferred from those two runs, not traced in the game code.
    if (auto* input = dynamic_cast<rex::input::InputSystem*>(runtime()->input_system())) {
      input->SetDeviceAssignment(std::make_unique<rex::input::SharedAssignment>());
    }
    // The SDK defines perf_log_csv (a per-frame CSV of its perf counters, written at each Flip) but nothing opens the
    // file: open it here. tools/play.sh records with it.
    if (!REXCVAR_GET(perf_log_csv).empty()) {
      rex::perf::SetCsvLogPath(REXCVAR_GET(perf_log_csv));
    }
    // Test-run screenshots (mhnwis_screenshots, mhnwis_screenshot.cpp), taken from the presented image.
    mhnwis::screenshot::Start([this]() -> rex::ui::Presenter* {
      const auto* rt = runtime();
      const auto* graphics = rt ? rt->graphics_system() : nullptr;
      return graphics ? graphics->presenter() : nullptr;
    });
  }

  // The game files: assets/game_root (a link to the disc folder) in the executable's folder or any folder above it,
  // unless the config or command line already set game_data_root. The disc names the executable Default.xex; the
  // guest's own lookups are case-insensitive, but this check runs on the host filesystem, so both spellings count.
  void OnConfigurePaths(rex::PathConfig& paths) override {
    if (!paths.game_data_root.empty()) {
      return;
    }
    std::error_code ec;
    const auto folder = rex::filesystem::GetExecutableFolder();
    for (auto candidate = folder; !candidate.empty(); candidate = candidate.parent_path()) {
      for (const auto& sub : {std::filesystem::path("game_root"), std::filesystem::path("assets") / "game_root"}) {
        const auto root = candidate / sub;
        if (std::filesystem::is_regular_file(root / "Default.xex", ec) ||
            std::filesystem::is_regular_file(root / "default.xex", ec)) {
          paths.game_data_root = root;
          return;
        }
      }
      if (candidate == candidate.parent_path()) {
        break;
      }
    }
  }
};
