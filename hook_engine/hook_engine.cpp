#include "hook_engine.h"
#include <ptrauth.h>
#include "../utils/utils.h"

HookMode hook_engine::current_mode = MODE_RESEARCH;

namespace hook_engine {
    void* strip_pac(void* ptr) {
        if (__builtin_available(iOS 12.0, *))
            return ptrauth_strip(ptr, ptrauth_key_function_pointer);
        return ptr;
    }

    bool add_brk_hook(uint64_t addr, void* repl, void** orig) {
        // Placeholder - usa MemX de Titanox en versión final
        utils::log_to_file("BRK hook registrado en 0x%llx", addr);
        return true;
    }

    void init() {
        utils::log_to_file("Hook engine inicializado (PAC-aware)");
    }
}
