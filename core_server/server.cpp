// core_server/server.cpp
#include "server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <unistd.h>
#include "../utils/utils.h"

namespace core_server {

    void* server_thread(void*) {
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        if (fd < 0) {
            utils::log_to_file("❌ Error creando socket");
            return nullptr;
        }

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(52737);
        addr.sin_addr.s_addr = INADDR_ANY;

        if (bind(fd, (sockaddr*)&addr, sizeof(addr)) < 0) {
            utils::log_to_file("❌ Error en bind del servidor");
            close(fd);
            return nullptr;
        }

        listen(fd, 5);
        utils::log_to_file("✅ Servidor TCP iniciado en puerto 52737 (listo para cliente PC)");

        while (true) {
            int client = accept(fd, nullptr, nullptr);
            if (client >= 0) {
                // Placeholder para protocolo TLV (se expandirá después)
                close(client);
            }
        }
        return nullptr;
    }

    void start_tcp_server() {
        pthread_t t;
        pthread_create(&t, nullptr, server_thread, nullptr);
        pthread_detach(t);
    }

} // namespace core_server