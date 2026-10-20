// Screenshots for test runs (mhnwis_screenshots = "20,40,60"): see mhnwis_screenshot.cpp.

#pragma once

#include <functional>

namespace rex::ui {
struct RawImage;
}

namespace mhnwis::screenshot {

// Starts the screenshot thread when mhnwis_screenshots lists any seconds; returns at once otherwise. grab fills the
// image of the frame on screen and returns false when there is none.
void Start(std::function<bool(rex::ui::RawImage&)> grab);

}  // namespace mhnwis::screenshot
