#pragma once
#include <cstdint>

enum HookMode { MODE_RESEARCH, MODE_EXPLOIT, MODE_STEALTH };

namespace hook_engine {
    void init();
    bool add_brk_hook(uint64_t addr, void* replacement, void** original);
    extern HookMode current_mode;
}
