// utils/utils.cpp
#include "utils.h"
#include <stdio.h>
#include <stdarg.h>
#include <mach-o/dyld.h>
#include <string>

namespace utils {
    static FILE* log_file = nullptr;

    void init_logging() {
        char path[1024];
        uint32_t size = sizeof(path);
        _NSGetExecutablePath(path, &size);

        // Carpeta Documents del juego (estándar en ESign)
        std::string log_path = std::string(path) + "/../Documents/ENHANCED_LOGS.TXT";
        log_file = fopen(log_path.c_str(), "a");

        if (log_file) {
            log_to_file("🚀 enhanced-ios-hacker.dylib cargado en iOS 26 jailed");
            log_to_file("[LOG] Archivo creado en: %s", log_path.c_str());
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