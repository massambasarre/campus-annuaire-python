# clients/user_client.py
import socket, sys
from common.protocol import send_json_line, recv_json_line
from common.utils import pretty, print_menu   # <-- import du helper

try:
    from clients.config import HOST, PORT
except Exception:
    HOST, PORT = "127.0.0.1", 5055

def ask(payload):
    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        send_json_line(sock, payload)
        buf = bytearray()
        return recv_json_line(sock, buf)

def main():
    while True:
        print_menu("USER", [
            ("1", "Lister par catégorie"),
            ("2", "Lister prof par domaine"),
            ("3", "Rechercher"),
            ("0", "Quitter"),
        ])
        ch = input("> ").strip()

        if ch == "1":
            cat = input("Catégorie (prof/aux/etudiant): ").strip()
            print(pretty(ask({"action":"LIST_BY_CATEGORY","data":{"categorie":cat}})))
        elif ch == "2":
            dom = input("Domaine (ex: reseaux): ").strip()
            print(pretty(ask({"action":"LIST_PROF_BY_DOMAIN","data":{"domaine":dom}})))
        elif ch == "3":
            q = input("Recherche (nom/prenom/matricule): ").strip()
            print(pretty(ask({"action":"SEARCH_MEMBER","data":{"q":q}})))
        elif ch == "0":
            sys.exit(0)
        else:
            print("Choix invalide.")

if __name__ == "__main__":
    main()
