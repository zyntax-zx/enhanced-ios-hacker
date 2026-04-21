#include "server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <unistd.h>
#include "../utils/utils.h"

void* server_thread(void*) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr{ AF_INET, htons(52737), {INADDR_ANY} };
    if (bind(fd, (sockaddr*)&addr, sizeof(addr)) < 0) return nullptr;
    listen(fd, 5);
    utils::log_to_file("Servidor TCP iniciado en puerto 52737");
    while (true) {
        int client = accept(fd, nullptr, nullptr);
        close(client);  // placeholder - expandir con TLV después
    }
    return nullptr;
}

void start_tcp_server() {
    pthread_t t;
    pthread_create(&t, nullptr, server_thread, nullptr);
    pthread_detach(t);
}
