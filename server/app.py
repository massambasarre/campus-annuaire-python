import socket, threading
from server import storage_sqlite as storage
from common.protocol import recv_json_line, send_json_line, err
from server.handlers import handle
from server.config import HOST, PORT

def client_thread(conn, addr):
    buf = bytearray()
    try:
        while True:
            req = recv_json_line(conn, buf)
            if req is None:
                break
            try:
                resp = handle(req)
            except Exception as e:
                resp = err(f"SERVER_EXCEPTION:{type(e).__name__}")
            send_json_line(conn, resp)
    finally:
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(20)
        print(f"CampusAnnuaire server listening on {HOST}:{PORT}")
        # ... dans main() avant la boucle d'accept :
        storage.init_db()
        storage.import_from_json_if_empty()  # optionnel, pour migrer data.json si présent
        while True:
            conn, addr = s.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
