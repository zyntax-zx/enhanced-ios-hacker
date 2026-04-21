// utils/utils.cpp
#include "utils.h"
#include <stdio.h>
#include <stdarg.h>
#include <mach-o/dyld.h>
#include <string>

namespace utils {
    static FILE* log_file = nullptr;

    void init_logging() {
        // Ruta principal: carpeta Documents del juego (como DNA-Inside)
        char path[1024];
        uint32_t size = sizeof(path);
        _NSGetExecutablePath(path, &size);

        std::string log_path = std::string(path) + "/../Documents/ENHANCED_LOGS.TXT";

        log_file = fopen(log_path.c_str(), "a");

        if (log_file) {
            log_to_file("🚀 enhanced-ios-hacker.dylib cargado correctamente");
            log_to_file("[LOG] Archivo creado en Documents del juego");
            log_to_file("[PATH] %s", log_path.c_str());
            return;
        }

        // Fallback 2: /tmp (visible con file manager o ESign)
        log_file = fopen("/tmp/ENHANCED_LOGS.TXT", "a");
        if (log_file) {
            log_to_file("🚀 dylib cargado - usando /tmp como fallback");
            log_to_file("[PATH] /tmp/ENHANCED_LOGS.TXT");
            return;
        }
    }

    void log_to_file(const char* fmt, ...) {
        if (!log_file) return;
        va_list args;
        va_start(args, fmt);
        vfprintf(log_file, fmt, args);
        va_end(args);
        fprintf(log_file, "\n");
        fflush(log_file);
    }
}