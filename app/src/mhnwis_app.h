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
#include <rex/platform.h>
#include <rex/rex_app.h>
#include <rex/runtime.h>
#include <rex/ui/presenter.h>

#include "mhnwis_screenshot.h"
#include "mhnwis_shm.h"

#if SA2_RENUT_RENDERER
#include "renut_engine/gpu/banjo_renut_capture.h"
#include "renut_engine/gpu/banjo_renut_select.h"
#include "renut_engine/gpu/overlay/app_integration.h"
#endif

#if MHNWIS_PERF_CSV
REXCVAR_DECLARE(std::string, perf_log_csv);
#endif

class MhnwisApp : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<MhnwisApp>(new MhnwisApp(ctx, "mhnwis", PPCImageConfig));
  }

  // Defaults applied before mhnwis.toml (which may override any of them). The first boot ran without a GPU
  // ("VdInitializeRingBuffer: no GPU emulation loaded (gpu_plugin not set)", 2026-10-20): the emulated Xenos GPU is a
  // plugin, built by GPU_PLUGINS xenos in CMakeLists.txt and loaded by this setting.
  // On the Switch there is no emulated GPU: Renut on deko3d (sa2-nx's sa2_switch_defaults.toml), the game files
  // packed into one file on the SD at the first start (asset_pack_build), and, for the first console tests, the log
  // on (logs/ next to the NRO) so a run can be read back.
  std::string_view BuiltInConfig() const override {
#if REX_PLATFORM_SWITCH
    return "sa2_renderer = \"renut\"\n"
           "renut_gpu_backend = \"deko3d\"\n"
           "sa2_render_height_handheld = 720\n"
           "sa2_render_height_docked = 1080\n"
           "asset_pack = true\n"
           "asset_pack_build = true\n"
           "log_level = \"info\"\n"
           "log_to_file = true\n";
#else
    return "gpu_plugin = \"xenos\"\n";
#endif
  }

  void OnPostSetup() override {
    // The guest memory is mapped now: its /dev/shm file can go (mhnwis_shm.cpp).
    mhnwis::shm::UnlinkOwnFile();
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
#if MHNWIS_PERF_CSV
    if (!REXCVAR_GET(perf_log_csv).empty()) {
      rex::perf::SetCsvLogPath(REXCVAR_GET(perf_log_csv));
    }
#endif
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
    // Before the guest memory is created: free what killed or crashed runs left in /dev/shm (mhnwis_shm.cpp).
    mhnwis::shm::RemoveStaleFiles();
    if (!paths.game_data_root.empty()) {
      return;
    }
    std::error_code ec;
    const auto folder = rex::filesystem::GetExecutableFolder();
    for (auto candidate = folder; !candidate.empty(); candidate = candidate.parent_path()) {
      for (const auto& sub : {std::filesystem::path("game_root"), std::filesystem::path("assets") / "game_root"}) {
        const auto root = candidate / sub;
        // Or only its asset pack (the Switch: game_root.nxpack + .nxidx, which the SDK builds from the folder at the
        // first start; the folder may be deleted after that).
        auto pack = root;
        pack += ".nxpack";
        if (std::filesystem::is_regular_file(root / "Default.xex", ec) ||
            std::filesystem::is_regular_file(root / "default.xex", ec) ||
            std::filesystem::is_regular_file(pack, ec)) {
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
