import socket
import struct

USB_MODE = True                    # True = USB con iproxy (más stealth)
HOST = "127.0.0.1" if USB_MODE else "TU_IP_DEL_IPHONE"
PORT = 52737

def send_packet(opcode, data=b""):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        packet = struct.pack("<II", opcode, len(data)) + data
        s.sendall(packet)
        resp_size = struct.unpack("<I", s.recv(4))[0]
        response = s.recv(resp_size)
        print(f"[CLIENT] Respuesta opcode {opcode}: {response.hex()[:80]}...")

if __name__ == "__main__":
    print("Enhanced Client - Conecta con USB (iproxy) o Wireless")
    while True:
        cmd = input("\nComando (read / toggle / quit): ").strip().lower()
        if cmd == "quit": break
        elif cmd == "read":
            addr = int(input("Dirección hex (ej: 0x12345678): "), 16)
            size = int(input("Tamaño bytes: "))
            data = struct.pack("<QI", addr, size)
            send_packet(1, data)   # OP_READ_MEM
        elif cmd == "toggle":
            hid = int(input("Hook ID: "))
            send_packet(5, struct.pack("<I", hid))