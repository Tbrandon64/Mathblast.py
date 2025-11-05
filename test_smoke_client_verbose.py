import socket
import time

print('CLIENT: starting')
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    print('CLIENT: connecting to 127.0.0.1:5000')
    s.connect(('127.0.0.1', 5000))
    print('CLIENT: connected')
    print('CLIENT: sending JOIN')
    s.sendall(b'JOIN:VerboseTester\n')
    time.sleep(0.2)
    print('CLIENT: sending CHAT')
    s.sendall(b'CHAT:VerboseTester:Hello from verbose smoke test\n')
    # try to read responses for up to 2 seconds
    data = b''
    s.settimeout(2.0)
    try:
        while True:
            part = s.recv(4096)
            if not part:
                break
            data += part
    except Exception as e:
        print('CLIENT: recv ended with', type(e).__name__, str(e))
    print('CLIENT: RECEIVED >>>')
    print(data.decode('utf-8', errors='replace'))
except Exception as exc:
    print('CLIENT: exception', type(exc).__name__, exc)
finally:
    try:
        s.close()
    except:
        pass

print('CLIENT: done')
