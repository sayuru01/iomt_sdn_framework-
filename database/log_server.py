# database/log_server.py
# Receives UDP packets from all 9 device simulators
# Optional — confirms packet receipt only (DB save happens in simulator)

import socket
import json

SERVER_IP   = '0.0.0.0'
SERVER_PORT = 5005

def start_log_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    print(f"[*] Log Server listening on port {SERVER_PORT}")
    print("[*] Press Ctrl+C to stop")

    try:
        while True:
            # Fix 1: increased buffer size
            data, addr = sock.recvfrom(65535)

            # Fix 2: error handling for bad packets
            try:
                payload = json.loads(data.decode('utf-8'))
                host_id = payload.get('host_id', 'unknown')
                timestamp = payload.get('timestamp', '')
                print(f"[LOG] {timestamp} | {host_id} | data received ")

            except json.JSONDecodeError:
                print(f"[LOG WARNING] Bad packet from {addr} — not JSON")
            except KeyError as e:
                print(f"[LOG WARNING] Missing field {e} from {addr}")

    # Fix 3: graceful shutdown
    except KeyboardInterrupt:
        print("\n[*] Log Server stopped")
    finally:
        sock.close()

if __name__ == '__main__':
    start_log_server()