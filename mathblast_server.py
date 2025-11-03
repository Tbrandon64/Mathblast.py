#!/usr/bin/env python3
"""
Simple local lobby server for MathBlast space-lobby testing.
Protocol (line-oriented UTF-8 messages):
- JOIN:<name>            -> broadcast that player joined
- CHAT:<name>:<text>     -> broadcast chat message
- READY:<name>:<0|1>     -> broadcast ready status
- LIST?                  -> client requests current player list (server responds with LIST:<name1>,<name2>,...)

This is intentionally tiny and insecure — for local testing only.
"""
import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

HOST = '127.0.0.1'
PORT = 5000

clients = {}  # map sock -> {'sock':sock, 'addr':addr, 'name':name, 'level':1, 'ready':0}
clients_lock = threading.Lock()


def _serialize_players():
    """Return a compact serialized player list: name,level,ready;..."""
    with clients_lock:
        parts = []
        for info in clients.values():
            n = info.get('name') or ''
            lvl = str(info.get('level', 1))
            rd = str(info.get('ready', 0))
            parts.append(f"{n},{lvl},{rd}")
        return ";".join(parts)


def broadcast(line, exclude_sock=None):
    data = (line + '\n').encode('utf-8')
    with clients_lock:
        for info in list(clients.values()):
            s = info['sock']
            try:
                if s is exclude_sock:
                    continue
                s.sendall(data)
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass
                clients.pop(s, None)


def handle_client(sock, addr):
    name = None
    try:
        with sock:
            buf = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        line = line.decode('utf-8')
                    except Exception:
                        continue
                    if line.startswith('JOIN:'):
                        name = line.split(':', 1)[1]
                        with clients_lock:
                            info = clients.get(sock)
                            if info is not None:
                                info['name'] = name
                        logging.info(f"{name} joined from {addr}")
                        # broadcast join and updated list
                        broadcast(f"JOIN:{name}")
                        broadcast(f"LIST:{_serialize_players()}")
                    elif line.startswith('CHAT:'):
                        # forwarded as-is
                        broadcast(line)
                    elif line.startswith('READY:'):
                        # READY:name:0|1
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            rn = parts[1]; rv = parts[2]
                            with clients_lock:
                                info = clients.get(sock)
                                if info is not None:
                                    info['ready'] = int(rv)
                            broadcast(line)
                            # broadcast updated player list
                            broadcast(f"LIST:{_serialize_players()}")
                            # if all named clients are ready and count>0, auto-start
                            with clients_lock:
                                named = [c for c in clients.values() if c.get('name')]
                                if named and all(c.get('ready',0) for c in named):
                                    logging.info('All players ready -> broadcasting START')
                                    broadcast('START:')
                    elif line == 'LIST?':
                        sock.sendall(("LIST:" + _serialize_players() + '\n').encode('utf-8'))
                    elif line.startswith('LEVEL:'):
                        # LEVEL:name:level
                        parts = line.split(':',2)
                        if len(parts) >= 3:
                            ln = parts[1]; lv = parts[2]
                            with clients_lock:
                                info = clients.get(sock)
                                if info is not None:
                                    try:
                                        info['level'] = int(lv)
                                    except Exception:
                                        info['level'] = 1
                            broadcast(f"LIST:{_serialize_players()}")
                    elif line == 'START?':
                        # client asked whether to start; reply with START if all ready
                        with clients_lock:
                            named = [c for c in clients.values() if c.get('name')]
                            if named and all(c.get('ready',0) for c in named):
                                sock.sendall(b'START:\n')
                    else:
                        # unknown commands are simply broadcasted
                        broadcast(line)
    finally:
        with clients_lock:
            info = clients.pop(sock, None)
            if info and info.get('name'):
                broadcast(f"LEAVE:{info.get('name')}")
            # broadcast updated list
            broadcast(f"LIST:{_serialize_players()}")
        logging.info(f"Connection closed: {addr}")


def accept_loop(server_sock):
    try:
        while True:
            sock, addr = server_sock.accept()
            with clients_lock:
                clients[sock] = {'sock': sock, 'addr': addr, 'name': None, 'level':1, 'ready':0}
            threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()
            logging.info(f"Accepted connection from {addr}")
    except Exception as e:
        logging.error(f"Server accept loop error: {e}")


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(16)
    logging.info(f"MathBlast test server listening on {HOST}:{PORT}")
    # start accept loop in thread, and allow console commands
    t = threading.Thread(target=accept_loop, args=(server_sock,), daemon=True)
    t.start()
    try:
        while True:
            cmd = input().strip().lower()
            if cmd in ('quit', 'exit'):
                break
            if cmd == 'list':
                logging.info('Players: ' + _serialize_players())
            if cmd == 'start':
                logging.info('Admin: broadcasting START')
                broadcast('START:')
    except KeyboardInterrupt:
        logging.info("Server shutting down")
    finally:
        try:
            server_sock.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
