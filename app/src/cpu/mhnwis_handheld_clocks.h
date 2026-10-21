// Monster High: the handheld clocks (mhnwis_handheld_clocks.cpp): GPU 768 MHz and memory 1600 MHz in handheld mode,
// held while the game runs; or sa2_gpu_boost's 460.8 MHz profile (mhnwis_handheld_gpu_mhz = 460).
#pragma once

namespace mhnwis::clocks {

void Start();  // once, before the guest starts (OnPreSetup)
void Stop();   // at shutdown: the console's own configuration again

}  // namespace mhnwis::clocks
