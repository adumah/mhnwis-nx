// Screenshots for test runs (mhnwis_screenshots = "20,40,60"): see mhnwis_screenshot.cpp.

#pragma once

#include <functional>

namespace rex::ui {
class Presenter;
}

namespace mhnwis::screenshot {

// Starts the screenshot thread when mhnwis_screenshots lists any seconds; returns at once otherwise.
void Start(std::function<rex::ui::Presenter*()> get_presenter);

}  // namespace mhnwis::screenshot
