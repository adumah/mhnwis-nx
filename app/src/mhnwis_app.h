// Monster High: New Ghoul in School: the app (rex::ReXApp hooks). Renderer chosen at boot (sa2_renderer): the SDK's
// emulated Xenos GPU ("xenos", the default and the reference) or Renut's Direct3D-level renderer ("renut", the route to
// the Switch: docs/d3d-census.md).

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
#include <rex/ui/presenter.h>

#include "mhnwis_screenshot.h"

#if SA2_RENUT_RENDERER
#include "renut_engine/gpu/banjo_renut_capture.h"
#include "renut_engine/gpu/banjo_renut_select.h"
#include "renut_engine/gpu/overlay/app_integration.h"
#endif

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
    // Test-run screenshots (mhnwis_screenshots, mhnwis_screenshot.cpp), taken from the frame on screen.
#if SA2_RENUT_RENDERER
    if (banjo::renut_gpu::Active()) {
      mhnwis::screenshot::Start([](rex::ui::RawImage& image) { return renut::gpu::CaptureFrame(image); });
      return;
    }
#endif
    mhnwis::screenshot::Start([this](rex::ui::RawImage& image) {
      const auto* rt = runtime();
      const auto* graphics = rt ? rt->graphics_system() : nullptr;
      auto* presenter = graphics ? graphics->presenter() : nullptr;
      return presenter && presenter->CaptureGuestOutput(image);
    });
  }

#if SA2_RENUT_RENDERER
  // Renut's renderer (as sa2-nx's sa2_app.h wires it): no SDK graphics system and no GPU plugin; its own drawer for
  // the SDK's menus, its own swapchain resizing, started once the window exists (the paths are final then).
  void OnPreSetup(rex::RuntimeConfig& config) override {
    if (banjo::renut_gpu::Active()) {
      renut::gpu::ConfigureRuntime(config);
      REXLOG_INFO("graphics: Renut's Direct3D-level renderer (sa2_renderer = renut)");
    }
  }
  std::unique_ptr<rex::ui::ImmediateDrawer> OnCreateImmediateDrawer() override {
    if (banjo::renut_gpu::Active()) return renut::gpu::CreateOverlayDrawer();
    return rex::ReXApp::OnCreateImmediateDrawer();
  }
  void OnWindowPixelSizeChanged(uint32_t pixel_width, uint32_t pixel_height) override {
    rex::ReXApp::OnWindowPixelSizeChanged(pixel_width, pixel_height);
    if (banjo::renut_gpu::Active()) renut::gpu::OnWindowResized();
  }
  std::optional<rex::PathConfig> OnFinalizePaths(const rex::PathConfig& defaults,
                                                 std::function<void(rex::PathConfig)> resume) override {
    if (banjo::renut_gpu::Active()) renut::gpu::StartRenderer(app_context(), [this] { return imgui_drawer(); });
    return rex::ReXApp::OnFinalizePaths(defaults, std::move(resume));
  }
  void OnShutdown() override {
    if (banjo::renut_gpu::Active()) renut::gpu::ShutdownRenderer();
  }
#endif

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
