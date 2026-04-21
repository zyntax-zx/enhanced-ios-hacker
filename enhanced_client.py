import socket
import struct

USB_MODE = True
HOST = "127.0.0.1" if USB_MODE else "TU_IP_IPHONE"
PORT = 52737

def send_packet(opcode, data=b""):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        packet = struct.pack("<II", opcode, len(data)) + data
        s.sendall(packet)
        resp_size = struct.unpack("<I", s.recv(4))[0]
        response = s.recv(resp_size)
        print(f"[CLIENT] Respuesta: {response.hex()[:80]}...")

if __name__ == "__main__":
    print("Enhanced Client - ESign mode")
    while True:
        cmd = input("\nComando (read / toggle / quit): ").strip().lower()
        if cmd == "quit": break
        # Añade más comandos según necesites