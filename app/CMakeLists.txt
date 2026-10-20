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
)

if(WIN32)
    add_executable(mhnwis WIN32 ${MHNWIS_SOURCES})
else()
    add_executable(mhnwis ${MHNWIS_SOURCES})
endif()

# The emulated Xenos GPU (loaded by gpu_plugin = "xenos", src/mhnwis_app.h).
rexglue_setup_target(mhnwis GPU_PLUGINS xenos)
