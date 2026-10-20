// Screenshots for test runs: at each second listed in mhnwis_screenshots ("20,40,60"), the image the game presents
// (the presenter's guest output, the same source as sa2-nx's sa2_capture) is written to shots/shot_<s>s.ppm next to
// the executable. It works with the window minimized and nothing can cover it, so boot tests can stay out of the way.

#include "mhnwis_screenshot.h"

#include <chrono>
#include <cstdio>
#include <filesystem>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>
#include <rex/ui/presenter.h>

REXCVAR_DEFINE_STRING(mhnwis_screenshots, "", "MHNWIS",
                      "Seconds after start at which to save the presented image to shots/ (comma-separated, e.g. "
                      "\"20,40,60\"); empty = off");

namespace mhnwis::screenshot {
namespace {

bool WritePpm(const std::filesystem::path& path, const rex::ui::RawImage& image) {
  FILE* f = std::fopen(path.string().c_str(), "wb");
  if (!f) return false;
  std::fprintf(f, "P6\n%u %u\n255\n", image.width, image.height);
  std::vector<uint8_t> row(size_t(image.width) * 3);
  for (uint32_t y = 0; y < image.height; ++y) {
    const uint8_t* src = image.data.data() + size_t(y) * image.stride;
    for (uint32_t x = 0; x < image.width; ++x) {  // R8 G8 B8 X8 -> RGB
      row[x * 3 + 0] = src[x * 4 + 0];
      row[x * 3 + 1] = src[x * 4 + 1];
      row[x * 3 + 2] = src[x * 4 + 2];
    }
    std::fwrite(row.data(), 1, row.size(), f);
  }
  return std::fclose(f) == 0;
}

}  // namespace

void Start(std::function<rex::ui::Presenter*()> get_presenter) {
  std::vector<int> seconds;
  std::stringstream list(REXCVAR_GET(mhnwis_screenshots));
  for (std::string item; std::getline(list, item, ',');) {
    if (!item.empty()) seconds.push_back(std::stoi(item));
  }
  if (seconds.empty()) return;
  std::thread([get_presenter = std::move(get_presenter), seconds = std::move(seconds)]() {
    const auto start = std::chrono::steady_clock::now();
    const auto dir = rex::filesystem::GetExecutableFolder() / "shots";
    std::error_code ec;
    std::filesystem::create_directories(dir, ec);
    for (const int s : seconds) {
      std::this_thread::sleep_until(start + std::chrono::seconds(s));
      rex::ui::Presenter* presenter = get_presenter();
      rex::ui::RawImage image;
      if (!presenter || !presenter->CaptureGuestOutput(image) || !image.width) {
        REXLOG_WARN("[shot] {} s: no presented image to capture", s);
        continue;
      }
      const auto path = dir / ("shot_" + std::to_string(s) + "s.ppm");
      if (WritePpm(path, image)) {
        REXLOG_INFO("[shot] {} s: {}x{} written to {}", s, image.width, image.height, path.string());
      } else {
        REXLOG_WARN("[shot] {} s: could not write {}", s, path.string());
      }
    }
  }).detach();
}

}  // namespace mhnwis::screenshot
