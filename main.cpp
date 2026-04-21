// main.cpp
#include "utils/utils.h"
#include "core_server/server.h"
#include "hook_engine/hook_engine.h"
#include "memory_engine/memory_engine.h"

// Declaración externa requerida porque la función está definida en exploit_framework.cpp
extern "C" void init_exploit_framework();

__attribute__((constructor))
static void init_framework() {
    utils::init_logging();
    utils::log_to_file("🚀 enhanced-ios-hacker.dylib cargado en iOS 26 jailed");

    memory_engine::init();
    hook_engine::init();
    init_exploit_framework();           // Llamada correcta
    core_server::start_tcp_server();    // Llamada correcta con namespace

    utils::log_to_file("✅ Framework inicializado correctamente - listo para ESign");
}