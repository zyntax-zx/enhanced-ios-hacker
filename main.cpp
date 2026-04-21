// main.cpp
#include "utils/utils.h"
#include "core_server/server.h"
#include "hook_engine/hook_engine.h"
#include "memory_engine/memory_engine.h"
#include "jit_helper/jit_helper.h"

extern "C" void init_exploit_framework();

__attribute__((constructor))
static void init_framework() {
    utils::init_logging();
    utils::log_to_file("🚀 enhanced-ios-hacker.dylib cargado en iOS 26 jailed");
    utils::log_to_file("[ENV] %s", jit_helper::get_status().c_str());

    memory_engine::init();
    hook_engine::init();
    init_exploit_framework();
    core_server::start_tcp_server();

    utils::log_to_file("✅ Framework híbrido listo - Modo principal: ESign (JIT-less)");
}