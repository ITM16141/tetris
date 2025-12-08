import socket, threading

HOST = '0.0.0.0'
PORT = 50007
rooms = {}

def handle_client(conn, addr):
    try:
        room = conn.recv(1024).decode()
        if room not in rooms: rooms[room] = []
        rooms[room].append(conn)
        while True:
            data = conn.recv(4096)
            if not data: break
            for c in rooms[room]:
                if c != conn: c.sendall(data)
    finally:
        for r, clients in rooms.items():
            if conn in clients:
                clients.remove(conn)
                break
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT)); s.listen()
        print("Server started...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()