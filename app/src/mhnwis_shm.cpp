// The guest memory's shared-memory file (/dev/shm/xenia_memory_<tick>, the SDK's xmemory.cpp) is unlinked only at a
// clean shutdown (memory_posix.cpp CloseFileMappingHandle), so every run that is killed or crashes leaves its file, up
// to the whole 4.8 GB guest space in tmpfs. After a day of test runs /dev/shm was 80% full and new runs died with
// SIGBUS in Memory::Initialize and in guest memcpys (2026-10-20). The SDK never reopens the file by name: its mapping
// works from the descriptor, so unlinking it while mapped changes nothing for the running game.

#include "mhnwis_shm.h"

#include <sys/stat.h>
#include <unistd.h>

#include <filesystem>
#include <fstream>
#include <set>
#include <string>
#include <system_error>

#include <rex/logging.h>
#include <rex/platform.h>

namespace mhnwis::shm {
namespace {

constexpr const char* kShmDir = "/dev/shm";
constexpr const char* kPrefix = "xenia_memory_";

// The guest memory files some process has mapped (/proc/<pid>/maps names them), or only this process's.
std::set<std::string> MappedFiles(bool own_only) {
  std::set<std::string> mapped;
  std::error_code ec;
  auto scan = [&mapped](const std::filesystem::path& maps) {
    std::ifstream in(maps);
    for (std::string line; std::getline(in, line);) {
      const auto at = line.find(std::string(kShmDir) + "/" + kPrefix);
      if (at != std::string::npos) mapped.insert(line.substr(at, line.find(' ', at) - at));
    }
  };
  if (own_only) {
    scan("/proc/self/maps");
    return mapped;
  }
  for (const auto& entry : std::filesystem::directory_iterator("/proc", ec)) {
    const auto name = entry.path().filename().string();
    if (!name.empty() && name.find_first_not_of("0123456789") == std::string::npos) scan(entry.path() / "maps");
  }
  return mapped;
}

}  // namespace

void RemoveStaleFiles() {
#if REX_PLATFORM_LINUX
  const auto mapped = MappedFiles(false);
  std::error_code ec;
  int removed = 0;
  for (const auto& entry : std::filesystem::directory_iterator(kShmDir, ec)) {
    const auto path = entry.path().string();
    if (entry.path().filename().string().rfind(kPrefix, 0) != 0 || mapped.count(path)) continue;
    struct stat st{};
    if (::stat(path.c_str(), &st) != 0 || st.st_uid != ::getuid()) continue;  // only this user's
    if (std::filesystem::remove(entry.path(), ec)) ++removed;
  }
  if (removed) REXLOG_INFO("[shm] removed {} guest memory files left in {} by earlier runs", removed, kShmDir);
#endif
}

void UnlinkOwnFile() {
#if REX_PLATFORM_LINUX
  std::error_code ec;
  for (const auto& path : MappedFiles(true)) {
    if (std::filesystem::remove(path, ec)) REXLOG_INFO("[shm] {} unlinked (still mapped; nothing to leave behind)", path);
  }
#endif
}

}  // namespace mhnwis::shm
