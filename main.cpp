// main.cpp
#include "utils/utils.h"
#include "core_server/server.h"
#include "hook_engine/hook_engine.h"
#include "memory_engine/memory_engine.h"
#include "exploit_framework/plugin_base.h"

__attribute__((constructor))
static void init_framework() {
    utils::init_logging();
    utils::log_to_file("🚀 enhanced-ios-hacker.dylib cargado en iOS 26 jailed");

    memory_engine::init();
    hook_engine::init();
    init_exploit_framework();
    core_server::start_tcp_server();

    utils::log_to_file("✅ Framework inicializado correctamente");
}

// Declaración externa del init de exploit (definido en exploit_framework.cpp)
extern "C" void init_exploit_framework();