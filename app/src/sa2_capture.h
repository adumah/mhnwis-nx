// Monster High: the two lockstep-capture calls Renut's Swap hook makes (sa2-nx's sa2_capture.h, whose recorder is
// SA2's). This port has no lockstep recorder: test screenshots come from mhnwis_screenshot.cpp.

#pragma once

#include <cstdint>

namespace rex::ui {
struct RawImage;
}

namespace sa2::capture {

inline bool RenutLockstepOn() { return false; }
inline void RenutLockstepFrame(uint64_t, const rex::ui::RawImage*) {}

}  // namespace sa2::capture
