#import "nexus.h"
#include <mach/mach.h>
#include <vector>

void memory_engine_init(void) {
    nexus_log("MEM", "Memory Engine inicializado.");
}

// Lectura segura usando vm_read_overwrite
bool mem_read(uintptr_t addr, void *out, size_t size) {
    vm_size_t actual = 0;
    kern_return_t kr = vm_read_overwrite(mach_task_self(), addr, size, (vm_address_t)out, &actual);
    return (kr == KERN_SUCCESS && actual == size);
}

// Escritura usando vm_write
bool mem_write(uintptr_t addr, const void *data, size_t size) {
    kern_return_t kr = vm_write(mach_task_self(), addr, (vm_offset_t)data, (mach_msg_type_number_t)size);
    return (kr == KERN_SUCCESS);
}

// NOP region (ARM64: 0x1F2003D5)
bool mem_nop_region(uintptr_t addr, size_t instruction_count) {
    uint32_t nop = 0x1F2003D5;
    for (size_t i = 0; i < instruction_count; i++) {
        if (!mem_write(addr + i * 4, &nop, 4)) return false;
    }
    nexus_log("MEM", "NOP aplicado en 0x%lx (%zu instrucciones)", addr, instruction_count);
    return true;
}

// Scan diferencial (para encontrar valores que cambian)
struct ScanEntry { uintptr_t addr; int val; };
static std::vector<ScanEntry> g_scan_snapshot;

size_t mem_scan_snapshot(int min_val, int max_val) {
    g_scan_snapshot.clear();
    g_scan_snapshot.reserve(100000);

    vm_address_t addr = 0;
    vm_size_t    size = 0;
    while (true) {
        vm_region_basic_info_data_64_t info;
        mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
        mach_port_t obj = MACH_PORT_NULL;
        kern_return_t kr = vm_region_64(mach_task_self(), &addr, &size,
                                         VM_REGION_BASIC_INFO_64,
                                         (vm_region_info_t)&info, &count, &obj);
        if (kr != KERN_SUCCESS) break;

        bool rw = (info.protection & VM_PROT_READ) && (info.protection & VM_PROT_WRITE);
        bool ok = size <= (8 * 1024 * 1024); // Excluir regiones > 8MB

        if (rw && ok) {
            uint8_t buf[4096];
            for (vm_address_t p = addr; p < addr + size; p += 4096) {
                vm_size_t actual = 0;
                vm_size_t to_read = MIN(4096UL, (addr + size) - p);
                if (vm_read_overwrite(mach_task_self(), p, to_read,
                                      (vm_address_t)buf, &actual) != KERN_SUCCESS) continue;
                for (vm_size_t off = 0; off + 4 <= actual; off += 4) {
                    int v = *(int *)(buf + off);
                    if (v >= min_val && v <= max_val) {
                        g_scan_snapshot.push_back({(uintptr_t)(p + off), v});
                    }
                }
                usleep(200);
            }
        }
        addr += size;
    }
    nexus_log("MEM", "Snapshot tomado: %zu entradas.", g_scan_snapshot.size());
    return g_scan_snapshot.size();
}

// Retorna las direcciones donde el valor cambió respecto al snapshot
std::vector<uintptr_t> mem_scan_diff(int new_min, int new_max) {
    std::vector<uintptr_t> results;
    for (auto &e : g_scan_snapshot) {
        int curr = 0;
        vm_size_t actual = 0;
        if (vm_read_overwrite(mach_task_self(), e.addr, 4,
                              (vm_address_t)&curr, &actual) != KERN_SUCCESS) continue;
        int delta = e.val - curr;
        if (curr >= new_min && curr <= new_max && delta != 0) {
            results.push_back(e.addr);
        }
    }
    nexus_log("MEM", "Diff: %zu candidatos.", results.size());
    return results;
}

// AOB Scanner para encontrar patrones como "48 8B 05 ?? ?? ?? ??"
std::vector<uintptr_t> mem_aob_scan(const char *pattern) {
    std::vector<int> pat;
    const char *p = pattern;
    while (*p) {
        if (*p == ' ') p++;
        else if (*p == '?') { pat.push_back(-1); p++; if(*p=='?') p++; }
        else { pat.push_back(strtol(p, nullptr, 16)); p+=2; }
    }
    
    std::vector<uintptr_t> results;
    if (pat.empty()) return results;

    vm_address_t addr = 0;
    vm_size_t size = 0;
    while (true) {
        vm_region_basic_info_data_64_t info;
        mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
        mach_port_t obj = MACH_PORT_NULL;
        kern_return_t kr = vm_region_64(mach_task_self(), &addr, &size, VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &count, &obj);
        if (kr != KERN_SUCCESS) break;

        // Buscamos código ejecutable y datos (r-x, rw-, r--) para encontrar tanto patrones de código como punteros
        if ((info.protection & VM_PROT_READ)) {
            // Leer en bloques seguros de 1MB con superposición
            const size_t BLOCK_SIZE = 1024 * 1024;
            uint8_t *buf = (uint8_t*)malloc(BLOCK_SIZE);
            if (buf) {
                for (vm_address_t block = addr; block < addr + size; block += BLOCK_SIZE - pat.size()) {
                    vm_size_t to_read = MIN((vm_size_t)BLOCK_SIZE, (addr + size) - block);
                    vm_size_t actual = 0;
                    if (vm_read_overwrite(mach_task_self(), block, to_read, (vm_address_t)buf, &actual) == KERN_SUCCESS) {
                        for (size_t i = 0; i <= actual - pat.size(); i++) {
                            bool match = true;
                            for (size_t j = 0; j < pat.size(); j++) {
                                if (pat[j] != -1 && buf[i+j] != pat[j]) {
                                    match = false; break;
                                }
                            }
                            if (match) results.push_back(block + i);
                        }
                    }
                }
                free(buf);
            }
        }
        addr += size;
    }
    nexus_log("MEM", "AOB Scan completado. %zu coincidencias.", results.size());
    return results;
}
