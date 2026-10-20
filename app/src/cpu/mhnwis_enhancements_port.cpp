// Monster High: the parts of sa2-nx's enhancement framework (sa2_enhancements.cpp, taken as it is) that sa2-nx defines
// in SA2-specific files. Its codegen checks (sa2_codegen_checks.cpp) and forms self-check (sa2_forms_selfcheck.cpp)
// verify SA2's own guest code, and its GPU clock boost (sa2_gpu_boost.cpp) is for the Switch: none applies here yet.
// TODO(switch): bring sa2_gpu_boost.cpp over with the Switch build.

#include "sa2_enhancements.h"

namespace sa2::enh {

void CodegenChecksInit() {}
void CodegenChecksReport(int /*seconds*/) {}
void FormsSelfCheck() {}
void ApplyGpuBoost() {}

}  // namespace sa2::enh
