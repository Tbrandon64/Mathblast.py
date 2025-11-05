import socket
import time


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(('127.0.0.1', 5000))
        s.sendall(b'JOIN:SmokeTester\n')
        time.sleep(0.2)
        s.sendall(b'CHAT:SmokeTester:Hello from smoke test\n')
        import socket
        import time


        def main():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            try:
                s.connect(('127.0.0.1', 5000))
                s.sendall(b'JOIN:SmokeTester\n')
                time.sleep(0.2)
                s.sendall(b'CHAT:SmokeTester:Hello from smoke test\n')
                # read a bit
                data = b''
                s.settimeout(1.0)
                try:
                    while True:
                        part = s.recv(4096)
                        if not part:
                            break
                        data += part
                except Exception:
                    pass
                print('RECEIVED:', data.decode('utf-8', errors='replace'))
            finally:
                try:
                    s.close()
                except:
                    pass


        if __name__ == '__main__':
            main()
