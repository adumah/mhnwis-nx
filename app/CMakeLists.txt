# Monster High: New Ghoul in School - ReXGlue recompiled project (the SDK's init template).
#
# SDK boilerplate lives in generated/rexglue.cmake (written by the code generator). Configure with
# -DREXSDK_DIR=<sa2-nx>/sdk; tools/build_pc.sh does it.

cmake_minimum_required(VERSION 3.25)
project(mhnwis LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

set(MHNWIS_SOURCES
    src/main.cpp
    src/mhnwis_screenshot.cpp
    src/mhnwis_shm.cpp
)

# Diagnostic sources added for one build only, e.g. the Direct3D census (tools/d3d/census_build.py). Empty normally.
set(MHNWIS_EXTRA_SOURCES "" CACHE STRING "Extra source files (diagnostic builds only)")
list(APPEND MHNWIS_SOURCES ${MHNWIS_EXTRA_SOURCES})

if(WIN32)
    add_executable(mhnwis WIN32 ${MHNWIS_SOURCES})
else()
    add_executable(mhnwis ${MHNWIS_SOURCES})
endif()

# The emulated Xenos GPU (loaded by gpu_plugin = "xenos", src/mhnwis_app.h). The Switch build links it too, as
# sa2-nx's does: there the SDK's plugin loader calls the plugin's entry points directly (no dynamic libraries), so the
# link needs one. It is never started there: Renut draws on deko3d, and without a Vulkan driver it could not run.
rexglue_setup_target(mhnwis GPU_PLUGINS xenos)

# The SDK builds its perf counters (and perf_log_csv) only into builds other than Release (its own directory scope).
target_compile_definitions(mhnwis PRIVATE $<$<NOT:$<CONFIG:Release>>:MHNWIS_PERF_CSV=1>)

# As sa2-nx: the SDK compiles itself with these, but they do not reach the generated game code built here. Without
# -ffp-contract=off the compiler fuses the guest's separate multiplies and adds into FMAs (GCC does by default, clang
# within a statement), and results drift from the Xbox 360's; strict aliasing is unsafe for recompiled code.
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    foreach(_mhnwis_target mhnwis mhnwis_recomp)
        if(TARGET ${_mhnwis_target})
            target_compile_options(${_mhnwis_target} PRIVATE -ffp-contract=off -fno-strict-aliasing)
        endif()
    endforeach()
endif()

if(REXGLUE_PLATFORM_SWITCH)
    # Where the NRO is on the SD card when no loader passes its path (an emulator): its folder holds the settings,
    # the logs, the shader caches and the game files.
    if(TARGET rexcore)
        target_compile_definitions(rexcore PRIVATE REX_SWITCH_FALLBACK_EXE="/switch/mhnwis-nx/mhnwis.nro")
    endif()
    # The homebrew menu's entry, with libnx's default icon (no game artwork).
    rexglue_switch_add_nro(mhnwis
        NAME "Monster High: New Ghoul in School"
        AUTHOR "mhnwis-nx (unofficial)"
        VERSION "0.1.0")
endif()

# Renut's Direct3D-level renderer (the route to the Switch: docs/d3d-census.md), chosen at boot with
# sa2_renderer = "renut"; the emulated GPU stays the default and the reference.
option(MHNWIS_RENUT_RENDERER "Link Renut's Direct3D-level renderer (sa2_renderer = renut)" ON)
if(MHNWIS_RENUT_RENDERER)
    include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/mhnwis_renut_gpu.cmake")
endif()
