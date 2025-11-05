import socket
import threading
import sys
import time

HOST = "127.0.0.1"
PORT = 5000

def handle_client(conn, addr):
    """Handle a single client connection."""
    print(f"[CONNECTED] {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8", errors="ignore").strip()
            print(f"[CLIENT {addr}] {msg}")
            # Example echo reply (you can expand this to match your game protocol)
            conn.sendall(f"Server received: {msg}".encode("utf-8"))
    except Exception as e:
        print(f"[ERROR] {addr} - {e}")
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")

def start_server():
    """Start a simple threaded TCP server."""
    global PORT
    while True:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((HOST, PORT))
            server.listen(5)
            print(f"[SERVER] Running on {HOST}:{PORT}")
            break
        except OSError as e:
            print(f"[WARNING] Port {PORT} in use: {e}")
            PORT += 1
            time.sleep(1)

    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down manually.")
            break
        except Exception as e:
            print(f"[SERVER ERROR] {e}")

if __name__ == "__main__":
    print("[INIT] Starting MathBlast local server...")
    start_server()
