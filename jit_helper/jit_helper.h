#pragma once
#include <string>

namespace jit_helper {
    bool is_jit_enabled();
    bool is_jit_less_mode();
    void* allocate_executable_memory(size_t size);
    void enable_fast_scanning();
    std::string get_status();
}
