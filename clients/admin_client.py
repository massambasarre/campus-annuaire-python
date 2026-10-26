# clients/admin_client.py
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

def auth():
    return {"password": input("Admin password (visible): ").strip()}

def main():
    while True:
        print_menu("ADMIN", [
            ("4", "Ajouter"),
            ("5", "Supprimer"),
            ("6", "Modifier"),
            ("7", "Mettre ListeRouge"),
            ("8", "Enlever ListeRouge"),
            ("9", "SEED (exemples)"),
            ("0", "Quitter"),
        ])
        ch = input("> ").strip()

        if ch == "4":
            d = {
              "nom": input("Nom: ").strip(),
              "prenom": input("Prénom: ").strip(),
              "categorie": input("Catégorie (prof/aux/etudiant): ").strip(),
              "email": input("Email: ").strip(),
              "matricule": input("Matricule (si étudiant): ").strip(),
              "domaine": input("Domaine (si prof): ").strip(),
              "telephone": input("Téléphone ?: ").strip()
            }
            print(pretty(ask({"action":"ADD_MEMBER","auth":auth(),"data":d})))

        elif ch == "5":
            mid = input("ID membre à supprimer: ").strip()
            print(pretty(ask({"action":"DELETE_MEMBER","auth":auth(),"data":{"id":mid}})))

        elif ch == "6":
            mid = input("ID membre à modifier: ").strip()
            field = input("Champ (nom,prenom,categorie,email,matricule,domaine,telephone): ").strip()
            value = input("Nouvelle valeur: ").strip()
            print(pretty(ask({"action":"UPDATE_MEMBER","auth":auth(),"data":{"id":mid, field:value}})))

        elif ch == "7":
            mid = input("ID membre: ").strip()
            print(pretty(ask({"action":"SET_RED_FLAG","auth":auth(),"data":{"id":mid}})))

        elif ch == "8":
            mid = input("ID membre: ").strip()
            print(pretty(ask({"action":"UNSET_RED_FLAG","auth":auth(),"data":{"id":mid}})))

        elif ch == "9":
            p = auth()
            samples = [
              {"nom":"Dupont","prenom":"Alice","categorie":"prof","email":"alice.dupont@example.org","domaine":"reseaux","telephone":"514-555-0101"},
              {"nom":"Martin","prenom":"Sam","categorie":"etudiant","email":"sam.martin@example.org","matricule":"A001"},
              {"nom":"Roy","prenom":"Nora","categorie":"aux","email":"nora.roy@example.org","telephone":"514-555-0202"},
              {"nom":"Bernard","prenom":"Leo","categorie":"prof","email":"leo.bernard@example.org","domaine":"securite"},
            ]
            for d in samples:
                print(pretty(ask({"action":"ADD_MEMBER","auth":p,"data":d})))

        elif ch == "0":
            sys.exit(0)
        else:
            print("Choix invalide.")

if __name__ == "__main__":
    main()
