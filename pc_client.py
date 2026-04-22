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

    def scan_snapshot(self):
        print("[*] Solicitando Snapshot de memoria (Fase 1)...")
        self._send_cmd(CMD_SCAN_SNAPSHOT)
        cmd, payload = self._recv_resp()
        if cmd == CMD_SCAN_SNAPSHOT and len(payload) == 4:
            count = struct.unpack('<I', payload)[0]
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

def interactive_shell(client):
    while True:
        try:
            cmd = input("\n[NEXUS Shell] > ").strip().lower()
            if not cmd or cmd == 'help':
                print("Comandos disponibles:")
                print("  ping       - Verificar conexión")
                print("  snap       - Tomar snapshot (valores 1-200)")
                print("  diff <val> - Filtrar snapshot por nuevo valor (ej: diff 160)")
                print("  write <addr> <val> - Escribir un valor entero en una dirección")
                print("  mode <0|1> - 0=RESEARCH, 1=EXPLOIT")
                print("  exit       - Salir")
            elif cmd == 'ping':
                client.ping()
            elif cmd == 'snap':
                client.scan_snapshot()
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
