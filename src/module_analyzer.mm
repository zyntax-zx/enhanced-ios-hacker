#import "nexus.h"
#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>

void module_analyzer_init(void) {
    nexus_log("ANALYZER", "Analizando módulos cargados...");

    uint32_t count = _dyld_image_count();
    for (uint32_t i = 0; i < count; i++) {
        const char *name = _dyld_get_image_name(i);
        intptr_t slide   = _dyld_get_image_vmaddr_slide(i);
        nexus_log("ANALYZER", "[%u] %s | slide: 0x%lx", i, name ? name : "?", slide);
    }
    nexus_log("ANALYZER", "Total: %u imágenes cargadas.", count);
}

// Busca una función en un módulo específico por nombre
uintptr_t analyzer_find_symbol(const char *lib_name, const char *symbol) {
    void *handle = dlopen(lib_name, RTLD_LAZY | RTLD_NOLOAD);
    if (!handle) {
        nexus_log("ANALYZER", "No se pudo abrir %s", lib_name);
        return 0;
    }
    void *sym = dlsym(handle, symbol);
    dlclose(handle);
    if (sym) {
        nexus_log("ANALYZER", "[OK] %s::%s en 0x%lx", lib_name, symbol, (uintptr_t)sym);
        return (uintptr_t)sym;
    }
    nexus_log("ANALYZER", "[FAIL] Símbolo %s no encontrado en %s", symbol, lib_name);
    return 0;
}

// Detecta posibles funciones de anti-cheat buscando nombres sospechosos
void analyzer_detect_anticheat(void) {
    const char *suspicious[] = {
        "integrity_check", "memory_verify", "cheat_detect",
        "anti_tamper", "validate_memory", "checksum_verify",
        "IsDebuggerPresent", "ptrace", "sysctl",
        NULL
    };

    nexus_log("ANALYZER", "Buscando funciones de anti-cheat...");
    for (int i = 0; suspicious[i] != NULL; i++) {
        void *sym = dlsym(RTLD_DEFAULT, suspicious[i]);
        if (sym) {
            nexus_log("ANALYZER", "[ALERTA] Anti-cheat detectado: %s en 0x%lx",
                      suspicious[i], (uintptr_t)sym);
        }
    }
}
