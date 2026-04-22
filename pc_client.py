import socket
import struct
import time
import sys

# --- CONSTANTES DEL PROTOCOLO NEXUS ---
PORT = 27042

CMD_READ_MEM       = 0x01
CMD_WRITE_MEM      = 0x02
CMD_SCAN_SNAPSHOT  = 0x03
CMD_SCAN_DIFF      = 0x04
CMD_ENUM_MODULES   = 0x05
CMD_HOOK_SYMBOL    = 0x06
CMD_NOP_REGION     = 0x07
CMD_SET_MODE       = 0x08
CMD_BAN_SIM        = 0x09
CMD_AOB_SCAN       = 0x0A
CMD_PONG           = 0xFF

class NexusClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None

    def connect(self):
        print(f"[*] Conectando a {self.ip}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        print("[+] Conectado exitosamente al servidor NEXUS.")

    def disconnect(self):
        if self.sock:
            self.sock.close()
            print("[*] Desconectado.")

    def _send_cmd(self, cmd, payload=b''):
        # Header: [CMD: 4 bytes] [LEN: 4 bytes]
        header = struct.pack('<II', cmd, len(payload))
        self.sock.sendall(header + payload)

    def _recv_resp(self):
        # Recibir Header de respuesta
        header_data = self.sock.recv(8)
        if not header_data or len(header_data) < 8:
            return None, None
        
        cmd, length = struct.unpack('<II', header_data)
        
        # Recibir Payload
        payload = b''
        while len(payload) < length:
            chunk = self.sock.recv(length - len(payload))
            if not chunk:
                break
            payload += chunk
            
        return cmd, payload

    def ping(self):
        print("[*] Enviando PING...")
        self._send_cmd(CMD_PONG)
        cmd, payload = self._recv_resp()
        if cmd == CMD_PONG:
            print("[+] PONG recibido. Conexión estable.")
        else:
            print("[-] PING falló.")

    def scan_snapshot(self, min_val=1, max_val=200):
        print(f"[*] Solicitando Snapshot de memoria para valores entre {min_val} y {max_val} (Fase 1)...")
        payload = struct.pack('<II', min_val, max_val)
        self._send_cmd(CMD_SCAN_SNAPSHOT, payload)
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_SCAN_SNAPSHOT and len(resp_payload) == 4:
            count = struct.unpack('<I', resp_payload)[0]
            print(f"[+] Snapshot tomado exitosamente: {count} candidatos encontrados.")
        else:
            print("[-] Error tomando snapshot.")

    def set_mode(self, exploit_mode=False):
        mode_val = 1 if exploit_mode else 0
        mode_str = "EXPLOIT" if exploit_mode else "RESEARCH"
        print(f"[*] Cambiando modo a {mode_str}...")
        
        payload = struct.pack('<B', mode_val)
        self._send_cmd(CMD_SET_MODE, payload)
        
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_SET_MODE:
            print(f"[+] Modo {mode_str} activado en el dispositivo.")
        else:
            print("[-] Error cambiando el modo.")

    def scan_diff(self, new_min, new_max):
        print(f"[*] Escaneando diferencias (Fase 2) para valores entre {new_min} y {new_max}...")
        payload = struct.pack('<II', new_min, new_max)
        self._send_cmd(CMD_SCAN_DIFF, payload)
        
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_SCAN_DIFF and len(resp_payload) >= 4:
            count = struct.unpack('<I', resp_payload[:4])[0]
            print(f"[+] Diff completado: {count} candidatos restantes.")
            
            # Leer hasta 100 punteros si count <= 100
            if count > 0 and count <= 100:
                ptr_data = resp_payload[4:]
                num_ptrs = len(ptr_data) // 8
                if num_ptrs > 0:
                    ptrs = struct.unpack('<' + 'Q'*num_ptrs, ptr_data)
                    for i, p in enumerate(ptrs):
                        print(f"    [{i+1}] 0x{p:016x}")
            return count
        else:
            print("[-] Error en scan_diff.")
            return -1

    def write_mem(self, address, value):
        print(f"[*] Escribiendo valor {value} en 0x{address:016x}...")
        # Empaquetamos la direccion (8 bytes), el tamaño (4 bytes) y el valor de 4 bytes (int)
        payload = struct.pack('<QI', address, 4) + struct.pack('<i', value)
        # Rellenamos hasta 256 bytes de data (segun WriteMemPayload)
        payload += b'\x00' * (256 - 4)
        
        self._send_cmd(CMD_WRITE_MEM, payload)
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_WRITE_MEM and len(resp_payload) >= 1:
            status = resp_payload[0]
            if status == 1:
                print("[+] Escritura exitosa.")
            else:
                print("[-] Fallo al escribir (posible memoria de solo lectura).")
        else:
            print("[-] Error en la comunicación.")

    def enum_modules(self, filter_name=None):
        print("[*] Solicitando lista de módulos...")
        self._send_cmd(CMD_ENUM_MODULES)
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_ENUM_MODULES and len(resp_payload) >= 4:
            count = struct.unpack('<I', resp_payload[:4])[0]
            print(f"[+] {count} módulos recibidos.")
            offset = 4
            entry_size = 144 # 8 + 8 + 128
            for i in range(count):
                if offset + entry_size > len(resp_payload):
                    break
                base_addr, slide = struct.unpack('<QQ', resp_payload[offset:offset+16])
                name_bytes = resp_payload[offset+16:offset+144]
                name = name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
                
                if not filter_name or filter_name.lower() in name.lower():
                    print(f"  [{i:03d}] 0x{base_addr:016x} (Slide: 0x{slide:016x}) | {name}")
                
                offset += entry_size
        else:
            print("[-] Error obteniendo módulos.")

    def read_pointer(self, address):
        payload = struct.pack('<QI', address, 8)
        self._send_cmd(CMD_READ_MEM, payload)
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_READ_MEM and len(resp_payload) >= 8:
            return struct.unpack('<Q', resp_payload[:8])[0]
        return 0

    def dump_memory(self, address, length=256):
        """Lee N bytes de memoria y los muestra como hex dump profesional."""
        length = min(length, 512)  # El servidor limita a 512 bytes
        payload = struct.pack('<QI', address, length)
        self._send_cmd(CMD_READ_MEM, payload)
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_READ_MEM and len(resp_payload) > 0:
            data = resp_payload
            print(f"[+] Dump de {len(data)} bytes desde 0x{address:016x}:")
            print(f"  {'Offset':>12s}  {'Hex':48s}  ASCII")
            print(f"  {'─'*12}  {'─'*48}  {'─'*16}")
            for i in range(0, len(data), 16):
                row = data[i:i+16]
                hex_part = ' '.join(f'{b:02X}' for b in row)
                ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
                print(f"  0x{address+i:012X}  {hex_part:<48s}  {ascii_part}")
            return data
        else:
            print("[-] Error leyendo memoria.")
            return None

    def read_chain(self, base_address, offsets):
        ptr = base_address
        print(f"[*] Recorriendo cadena desde 0x{base_address:016x}...")
        for offset in offsets[:-1]:
            new_ptr = self.read_pointer(ptr + offset)
            print(f"    -> 0x{ptr:016x} + 0x{offset:X} = 0x{new_ptr:016x}")
            ptr = new_ptr
            if ptr == 0:
                print("[-] Puntero nulo detectado en la cadena.")
                return 0
        final_addr = ptr + offsets[-1]
        print(f"[+] Dirección final resuelta: 0x{final_addr:016x}")
        return final_addr

    def aob_scan(self, pattern):
        print(f"[*] Escaneando AOB para: '{pattern}' ...")
        payload = pattern.encode('utf-8')
        self._send_cmd(CMD_AOB_SCAN, payload)
        
        cmd, resp_payload = self._recv_resp()
        if cmd == CMD_AOB_SCAN and len(resp_payload) >= 4:
            count = struct.unpack('<I', resp_payload[:4])[0]
            print(f"[+] AOB Scan completado: {count} coincidencias.")
            if count > 0 and count <= 100:
                ptr_data = resp_payload[4:]
                num_ptrs = len(ptr_data) // 8
                if num_ptrs > 0:
                    ptrs = struct.unpack('<' + 'Q'*num_ptrs, ptr_data)
                    for i, p in enumerate(ptrs):
                        print(f"    [{i+1}] 0x{p:016x}")
            return count
        else:
            print("[-] Error en AOB Scan.")
            return -1

def interactive_shell(client):
    while True:
        try:
            cmd = input("\n[NEXUS Shell] > ").strip().lower()
            if not cmd or cmd == 'help':
                print("Comandos disponibles:")
                print("  ping       - Verificar conexión")
                print("  mod [name] - Listar módulos (ej: mod, mod wuthering)")
                print("  dump <addr> [len] - Dump de memoria (ej: dump 0x11029409e 128)")
                print("  readptr <addr> - Leer un puntero de 64 bits (ej: readptr 0x10038c000)")
                print("  scanptr <addr> - Buscar qué parte de la RAM apunta a esta dirección")
                print("  aob <pattern> - Buscar AOB (ej: aob 48 8B 05 ? ? ? ? 48 85 C0)")
                print("  snap <val> - Tomar snapshot (ej: snap 1090)")
                print("  diff <val> - Filtrar snapshot (ej: diff 875)")
                print("  write <addr> <val> - Escribir un valor (ej: write 0x123 99)")
                print("  mode <0|1> - 0=RESEARCH, 1=EXPLOIT")
                print("  exit       - Salir")
            elif cmd == 'ping':
                client.ping()
            elif cmd.startswith('mod'):
                parts = cmd.split(' ')
                if len(parts) > 1:
                    client.enum_modules(parts[1])
                else:
                    client.enum_modules()
            elif cmd.startswith('dump '):
                try:
                    parts = cmd.split()
                    addr = int(parts[1], 16)
                    length = int(parts[2]) if len(parts) > 2 else 256
                    client.dump_memory(addr, length)
                except Exception as e:
                    print(f"Uso: dump <hex_addr> [longitud] (Error: {e})")
            elif cmd.startswith('readptr '):
                try:
                    addr = int(cmd.split(' ')[1], 16)
                    val = client.read_pointer(addr)
                    print(f"[+] Puntero en 0x{addr:016x} -> 0x{val:016x}")
                except Exception as e:
                    print("Uso: readptr <hex_addr> (Error:", e, ")")
            elif cmd.startswith('scanptr '):
                try:
                    addr = int(cmd.split(' ')[1], 16)
                    # Convertir la dirección a little-endian (8 bytes) y formatearla como AOB
                    packed = struct.pack('<Q', addr)
                    aob_pattern = ' '.join([f"{b:02X}" for b in packed])
                    print(f"[*] Escaneando referencias a 0x{addr:016x} (Patrón: {aob_pattern})")
                    client.aob_scan(aob_pattern)
                except Exception as e:
                    print("Uso: scanptr <hex_addr> (Error:", e, ")")
            elif cmd.startswith('aob '):
                pattern = cmd[4:].strip().upper()
                client.aob_scan(pattern)
            elif cmd.startswith('snap'):
                parts = cmd.split(' ')
                if len(parts) == 1:
                    client.scan_snapshot()
                elif len(parts) == 2:
                    val = int(parts[1])
                    client.scan_snapshot(val, val)
                elif len(parts) == 3:
                    client.scan_snapshot(int(parts[1]), int(parts[2]))
                else:
                    print("Uso: snap O snap <valor> O snap <min> <max>")
            elif cmd.startswith('diff '):
                try:
                    val = int(cmd.split(' ')[1])
                    client.scan_diff(val, val)
                except Exception as e:
                    print("Uso: diff <valor_actual> (Error:", e, ")")
            elif cmd.startswith('write '):
                parts = cmd.split(' ')
                if len(parts) == 3:
                    try:
                        addr = int(parts[1], 16)
                        val = int(parts[2])
                        client.write_mem(addr, val)
                    except Exception as e:
                        print("Error parseando parámetros:", e)
                else:
                    print("Uso: write 0xDireccion Valor (ej: write 0x158ab76c4 9999)")
            elif cmd.startswith('mode '):
                try:
                    val = int(cmd.split(' ')[1])
                    client.set_mode(exploit_mode=(val==1))
                except:
                    print("Uso: mode <0|1>")
            elif cmd == 'exit' or cmd == 'quit':
                break
            else:
                print("Comando desconocido. Escribe 'help'.")
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python pc_client.py <IP_DEL_IPHONE>")
        sys.exit(1)
        
    target_ip = sys.argv[1]
    client = NexusClient(target_ip, PORT)
    try:
        client.connect()
        client.ping()
        interactive_shell(client)
    except Exception as e:
        print(f"[-] Error de conexión: {e}")
    finally:
        client.disconnect()
