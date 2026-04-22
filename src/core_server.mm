#import "nexus.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>

// Protocolo TLV simple:
// [CMD:4 bytes][LEN:4 bytes][DATA:LEN bytes]
#define CMD_READ_MEM       0x01
#define CMD_WRITE_MEM      0x02
#define CMD_SCAN_SNAPSHOT  0x03
#define CMD_SCAN_DIFF      0x04
#define CMD_ENUM_MODULES   0x05
#define CMD_HOOK_SYMBOL    0x06
#define CMD_NOP_REGION     0x07
#define CMD_SET_MODE       0x08
#define CMD_BAN_SIM        0x09
#define CMD_PONG           0xFF

#pragma pack(push,1)
typedef struct {
    uint32_t cmd;
    uint32_t len;
} TLVHeader;

typedef struct {
    uintptr_t address;
    uint32_t  size;
} ReadMemPayload;

typedef struct {
    uintptr_t address;
    uint32_t  size;
    uint8_t   data[256];
} WriteMemPayload;
#pragma pack(pop)

static void handle_client(int fd) {
    nexus_log("SERVER", "Cliente conectado (fd=%d)", fd);

    while (true) {
        TLVHeader hdr;
        ssize_t n = recv(fd, &hdr, sizeof(hdr), MSG_WAITALL);
        if (n <= 0) break;

        uint8_t payload[4096] = {0};
        if (hdr.len > 0 && hdr.len <= sizeof(payload)) {
            recv(fd, payload, hdr.len, MSG_WAITALL);
        }

        switch (hdr.cmd) {
            case CMD_READ_MEM: {
                ReadMemPayload *req = (ReadMemPayload *)payload;
                uint8_t buf[512]   = {0};
                size_t  rsz = MIN((size_t)req->size, sizeof(buf));
                extern bool mem_read(uintptr_t, void*, size_t);
                bool ok = mem_read(req->address, buf, rsz);
                nexus_log("SERVER", "READ 0x%lx sz=%u ok=%d", req->address, req->size, ok);
                // Responder con los bytes leídos
                TLVHeader resp = { CMD_READ_MEM, (uint32_t)rsz };
                send(fd, &resp, sizeof(resp), 0);
                send(fd, buf,  rsz, 0);
                break;
            }
            case CMD_WRITE_MEM: {
                WriteMemPayload *req = (WriteMemPayload *)payload;
                extern bool mem_write(uintptr_t, const void*, size_t);
                bool ok = mem_write(req->address, req->data, req->size);
                nexus_log("SERVER", "WRITE 0x%lx sz=%u ok=%d", req->address, req->size, ok);
                TLVHeader resp = { CMD_WRITE_MEM, 1 };
                uint8_t  status = ok ? 1 : 0;
                send(fd, &resp, sizeof(resp), 0);
                send(fd, &status, 1, 0);
                break;
            }
            case CMD_SCAN_SNAPSHOT: {
                extern size_t mem_scan_snapshot(int, int);
                size_t count = mem_scan_snapshot(1, 200);
                nexus_log("SERVER", "SNAPSHOT: %zu entradas", count);
                TLVHeader resp = { CMD_SCAN_SNAPSHOT, 4 };
                uint32_t c32 = (uint32_t)count;
                send(fd, &resp, sizeof(resp), 0);
                send(fd, &c32, 4, 0);
                break;
            }
            case CMD_SET_MODE: {
                uint8_t mode = payload[0];
                g_nexus_mode = (mode == 1) ? NEXUS_MODE_EXPLOIT : NEXUS_MODE_RESEARCH;
                nexus_log("SERVER", "Modo: %s", mode == 1 ? "EXPLOIT" : "RESEARCH");
                TLVHeader resp = { CMD_SET_MODE, 1 };
                send(fd, &resp, sizeof(resp), 0);
                send(fd, &mode, 1, 0);
                break;
            }
            case CMD_PONG: {
                nexus_log("SERVER", "PING recibido.");
                TLVHeader resp = { CMD_PONG, 0 };
                send(fd, &resp, sizeof(resp), 0);
                break;
            }
            default:
                nexus_log("SERVER", "CMD desconocido: 0x%X", hdr.cmd);
                break;
        }
    }

    nexus_log("SERVER", "Cliente desconectado (fd=%d)", fd);
    close(fd);
}

static void *server_thread(void *arg) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { nexus_log("SERVER", "Error creando socket"); return NULL; }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(NEXUS_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        nexus_log("SERVER", "Error en bind al puerto %d", NEXUS_PORT);
        close(server_fd);
        return NULL;
    }

    listen(server_fd, 5);
    nexus_log("SERVER", "Servidor TCP listo en puerto %d", NEXUS_PORT);

    while (true) {
        struct sockaddr_in client_addr;
        socklen_t len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &len);
        if (client_fd < 0) continue;

        // Cada cliente en su propio hilo
        pthread_t t;
        int *fd_ptr = (int *)malloc(sizeof(int));
        *fd_ptr = client_fd;
        pthread_create(&t, NULL, [](void *a) -> void* {
            int fd = *(int*)a;
            free(a);
            handle_client(fd);
            return NULL;
        }, fd_ptr);
        pthread_detach(t);
    }
    return NULL;
}

void core_server_init(void) {
    pthread_t t;
    pthread_create(&t, NULL, server_thread, NULL);
    pthread_detach(t);
    nexus_log("SERVER", "Core Server inicializado.");
}
