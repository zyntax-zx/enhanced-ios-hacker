#import <Foundation/Foundation.h>
#include "jit_helper.h"
#include "../utils/utils.h"
#include <sys/mman.h>

bool jit_helper::is_jit_enabled() {
    return false; // ESign por defecto = JIT-less
}

bool jit_helper::is_jit_less_mode() {
    return !is_jit_enabled();
}

void* jit_helper::allocate_executable_memory(size_t size) {
    if (is_jit_less_mode()) return nullptr;
    void* ptr = mmap(nullptr, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANON, -1, 0);
    utils::log_to_file("[JIT] RWX en 0x%llx", (uint64_t)ptr);
    return ptr;
}

void jit_helper::enable_fast_scanning() {
    utils::log_to_file(is_jit_less_mode() ? 
        "[JIT-LESS] Modo seguro activado (ESign)" : 
        "[JIT] Escaneo rápido activado");
}

std::string jit_helper::get_status() {
    return is_jit_less_mode() ? 
        "JIT-LESS MODE (ESign - estable)" : 
        "FULL JIT ENABLED";
}
