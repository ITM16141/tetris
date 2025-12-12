import socket
import threading
import json
import os

HOST = "0.0.0.0"
PORT = os.environ.get("PORT", 50007)

rooms = {}
rooms_lock = threading.Lock()

def broadcast_to_room(room_id: str, message: bytes, sender_conn=None):
    with rooms_lock:
        if room_id not in rooms:
            return
        targets = list(rooms[room_id])

    for conn in targets:
        if conn is sender_conn:
            continue
        try:
            conn.sendall(message)
        except Exception:
            try:
                conn.close()
            except:
                pass
            with rooms_lock:
                if conn in rooms.get(room_id, []):
                    rooms[room_id].remove(conn)

def handle_client(conn, addr):
    print(f"[connect] {addr} connected")

    room_id = None

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                print(f"[disconnect] {addr} closed connection")
                break

            try:
                msg = json.loads(data.decode())
            except Exception:
                print(f"[error] invalid JSON from {addr}")
                continue

            if msg.get("type") == "join":
                room_id = msg.get("room")
                if room_id is None:
                    print(f"[error] no room specified by {addr}")
                    break

                with rooms_lock:
                    if room_id not in rooms:
                        rooms[room_id] = []
                    rooms[room_id].append(conn)

                print(f"[room] {addr} joined room {room_id}")
                continue

            if room_id is None:
                print(f"[warn] {addr} sent message before join")
                continue

            broadcast_to_room(room_id, data, sender_conn=conn)

        except ConnectionResetError:
            print(f"[disconnect] {addr} forcibly closed")
            break

        except Exception as e:
            print(f"[error] from {addr}: {e}")
            break
    try:
        conn.close()
    except:
        pass

    if room_id is not None:
        with rooms_lock:
            if conn in rooms.get(room_id, []):
                rooms[room_id].remove(conn)
            if len(rooms.get(room_id, [])) == 0:
                del rooms[room_id]

    print(f"[disconnect] {addr} removed from room {room_id}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

def main():
    local_ip = get_local_ip()
    print(f"[start] server starting on {local_ip}:{PORT}")

    addrinfo = socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM)

    af, socktype, proto, canonname, sa = addrinfo[0]

    with socket.socket(af, socktype, proto) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(sa)
        server_sock.listen()

        print("[ready] waiting for connections...")

        while True:
            try:
                conn, addr = server_sock.accept()
            except KeyboardInterrupt:
                print("\n[shutdown] server stopped")
                break

            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()