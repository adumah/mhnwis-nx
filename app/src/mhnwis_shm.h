// The guest memory's shared-memory file: see mhnwis_shm.cpp.

#pragma once

namespace mhnwis::shm {

// Before the guest memory exists: deletes this user's /dev/shm/xenia_memory_* files no running process maps (left by
// runs that were killed or crashed).
void RemoveStaleFiles();

// Once the guest memory is mapped: unlinks this process's file, so a killed run leaves nothing behind.
void UnlinkOwnFile();

}  // namespace mhnwis::shm
