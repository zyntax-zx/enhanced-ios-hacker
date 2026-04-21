// enhanced-ios-hacker/enhanced-ios-hacker/main.cpp
#include "utils/utils.h"
#include "hook_engine/hook_engine.h"
#include "memory_engine/memory_engine.h"
#include "exploit_framework/exploit_framework.h"
#include "core_server/server.h"
#include "overlay/imgui_overlay.h"

__attribute__((constructor))
static void init_framework() {
    utils::init_logging();
    utils::log_to_file("🚀 enhanced-ios-hacker.dylib cargado (iOS 26 jailed)");

    memory_engine::init();
    hook_engine::init();
    init_imgui_overlay();
    init_exploit_framework();
    core_server::start_tcp_server();

    utils::log_to_file("✅ Framework inicializado - usa ESign para inyectar");
}
