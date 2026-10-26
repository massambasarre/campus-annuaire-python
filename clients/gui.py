# clients/gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import re
from common.protocol import send_json_line, recv_json_line

# -------- Validation email --------
EMAIL_RE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
def is_valid_email(s: str) -> bool:
    return bool(EMAIL_RE.match(s or ""))

# -------- Config host/port --------
try:
    from clients.config import HOST, PORT
except Exception:
    HOST, PORT = "127.0.0.1", 5055

def rpc(payload: dict):
    """Appelle le serveur et renvoie le dict réponse, ou lève une exception lisible."""
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as s:
            send_json_line(s, payload)
            buf = bytearray()
            resp = recv_json_line(s, buf)
            if not resp:
                raise RuntimeError("Réponse vide du serveur.")
            return resp
    except ConnectionRefusedError:
        raise RuntimeError("Serveur introuvable. Lance d’abord server/app.py.")
    except TimeoutError:
        raise RuntimeError("Délai dépassé. Vérifie l’adresse/port du serveur.")
    except Exception as e:
        raise RuntimeError(f"Erreur réseau: {type(e).__name__}: {e}")

# -------------------- UI helpers --------------------
def set_text(widget: tk.Text, text: str):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    widget.config(state="disabled")

def pretty(obj):
    import json
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

# -------------------- App --------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CampusAnnuaire")
        self.geometry("870x600")
        self.minsize(820, 520)

        # ---- Styles & couleurs ----
        self.USER_COLOR = "#e6f7ff"   # bleu très clair
        self.ADMIN_COLOR = "#fff5e6"  # orange très clair

        style = ttk.Style(self)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", foreground=[("selected", "#0b5394")])  # bleu foncé quand sélectionné

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.user_tab = UserTab(nb, banner_color=self.USER_COLOR)
        self.admin_tab = AdminTab(nb, banner_color=self.ADMIN_COLOR)

        nb.add(self.user_tab, text="Utilisateur")
        nb.add(self.admin_tab, text="Administrateur")

# -------------------- Onglet Utilisateur --------------------
class UserTab(ttk.Frame):
    def __init__(self, parent, banner_color="#e6f7ff"):
        super().__init__(parent)

        # Bandeau coloré en haut
        banner = tk.Frame(self, bg=banner_color, height=8)
        banner.pack(fill="x")

        # Ligne 0: PING + Effacer
        tools = ttk.Frame(self); tools.pack(fill="x", padx=10, pady=(8, 0))
        ttk.Button(tools, text="PING serveur", command=self.ping).pack(side="left")
        ttk.Button(tools, text="Effacer", command=lambda: set_text(self.user_out, "")).pack(side="right")

        # Ligne 1: Lister par catégorie
        lf1 = ttk.LabelFrame(self, text="Lister par catégorie")
        lf1.pack(fill="x", padx=10, pady=6)
        ttk.Label(lf1, text="Catégorie:").pack(side="left", padx=6, pady=6)
        self.cat_var = tk.StringVar(value="prof")
        ttk.Combobox(
            lf1, textvariable=self.cat_var, width=18,
            values=("prof", "aux", "etudiant"), state="readonly"
        ).pack(side="left", padx=6)
        ttk.Button(lf1, text="Lister", command=self.list_by_category).pack(side="left", padx=6)

        # Ligne 2: Lister prof par domaine
        lf2 = ttk.LabelFrame(self, text="Lister prof par domaine")
        lf2.pack(fill="x", padx=10, pady=6)
        ttk.Label(lf2, text="Domaine:").pack(side="left", padx=6, pady=6)
        self.dom_var = tk.StringVar(value="reseaux")
        ttk.Combobox(
            lf2, textvariable=self.dom_var, width=18,
            values=("reseaux", "securite", "programming", "ia", "autre")
        ).pack(side="left", padx=6)
        ttk.Button(lf2, text="Lister", command=self.list_prof_by_domain).pack(side="left", padx=6)

        # Ligne 3: Rechercher
        lf3 = ttk.LabelFrame(self, text="Rechercher (nom / prenom / matricule)")
        lf3.pack(fill="x", padx=10, pady=6)
        self.q_var = tk.StringVar()
        ttk.Entry(lf3, textvariable=self.q_var, width=32).pack(side="left", padx=6, pady=6)
        ttk.Button(lf3, text="Rechercher", command=self.search_member).pack(side="left", padx=6)

        # Résultats
        lf4 = ttk.LabelFrame(self, text="Résultat")
        lf4.pack(fill="both", expand=True, padx=10, pady=8)
        self.user_out = tk.Text(lf4, wrap="word", height=18, bg="#f2fbff")  # fond doux
        self.user_out.pack(fill="both", expand=True)
        self.user_out.config(state="disabled")

    # actions
    def ping(self):
        try:
            res = rpc({"action": "PING"})
            set_text(self.user_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def list_by_category(self):
        try:
            cat = self.cat_var.get().strip()
            res = rpc({"action": "LIST_BY_CATEGORY", "data": {"categorie": cat}})
            set_text(self.user_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def list_prof_by_domain(self):
        try:
            dom = self.dom_var.get().strip()
            res = rpc({"action": "LIST_PROF_BY_DOMAIN", "data": {"domaine": dom}})
            set_text(self.user_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def search_member(self):
        try:
            q = self.q_var.get().strip()
            res = rpc({"action": "SEARCH_MEMBER", "data": {"q": q}})
            set_text(self.user_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

# -------------------- Onglet Admin --------------------
class AdminTab(ttk.Frame):
    def __init__(self, parent, banner_color="#fff5e6"):
        super().__init__(parent)

        # Bandeau coloré en haut
        banner = tk.Frame(self, bg=banner_color, height=8)
        banner.pack(fill="x")

        # Auth
        authf = ttk.LabelFrame(self, text="Authentification admin")
        authf.pack(fill="x", padx=10, pady=6)
        ttk.Label(authf, text="Mot de passe:").pack(side="left", padx=6, pady=6)
        self.pwd_var = tk.StringVar()
        ttk.Entry(authf, textvariable=self.pwd_var, width=24, show="*").pack(side="left", padx=6)

        # Ajouter
        add = ttk.LabelFrame(self, text="Ajouter un membre")
        add.pack(fill="x", padx=10, pady=6)
        self.add_nom = tk.StringVar(); self.add_prenom = tk.StringVar()
        self.add_cat = tk.StringVar(value="etudiant")
        self.add_email = tk.StringVar()
        self.add_matricule = tk.StringVar()
        self.add_domaine = tk.StringVar()
        self.add_tel = tk.StringVar()

        row1 = ttk.Frame(add); row1.pack(fill="x", padx=6, pady=2)
        ttk.Label(row1, text="Nom").pack(side="left", padx=4)
        ttk.Entry(row1, textvariable=self.add_nom, width=16).pack(side="left")
        ttk.Label(row1, text="Prénom").pack(side="left", padx=8)
        ttk.Entry(row1, textvariable=self.add_prenom, width=16).pack(side="left")
        ttk.Label(row1, text="Catégorie").pack(side="left", padx=8)
        ttk.Combobox(row1, textvariable=self.add_cat, width=12,
                     values=("prof", "aux", "etudiant"), state="readonly").pack(side="left")

        row2 = ttk.Frame(add); row2.pack(fill="x", padx=6, pady=2)
        ttk.Label(row2, text="Email").pack(side="left", padx=4)
        ttk.Entry(row2, textvariable=self.add_email, width=30).pack(side="left")
        ttk.Label(row2, text="Matricule").pack(side="left", padx=8)
        ttk.Entry(row2, textvariable=self.add_matricule, width=14).pack(side="left")

        row3 = ttk.Frame(add); row3.pack(fill="x", padx=6, pady=2)
        ttk.Label(row3, text="Domaine (prof)").pack(side="left", padx=4)
        ttk.Entry(row3, textvariable=self.add_domaine, width=18).pack(side="left")
        ttk.Label(row3, text="Téléphone").pack(side="left", padx=8)
        ttk.Entry(row3, textvariable=self.add_tel, width=18).pack(side="left")
        ttk.Button(add, text="Ajouter", command=self.add_member).pack(anchor="e", padx=10, pady=4)

        # Opérations par ID (supprimer / modifier / liste rouge)
        ops = ttk.LabelFrame(self, text="Opérations sur un membre (via ID)")
        ops.pack(fill="x", padx=10, pady=6)
        self.op_id = tk.StringVar()
        ttk.Label(ops, text="ID membre").pack(side="left", padx=6, pady=6)
        ttk.Entry(ops, textvariable=self.op_id, width=44).pack(side="left", padx=6)
        ttk.Button(ops, text="Supprimer", command=self.delete_member).pack(side="left", padx=4)
        ttk.Button(ops, text="Mettre Liste Rouge", command=lambda: self.set_red(True)).pack(side="left", padx=4)
        ttk.Button(ops, text="Enlever Liste Rouge", command=lambda: self.set_red(False)).pack(side="left", padx=4)

        # Modifier un champ
        upd = ttk.LabelFrame(self, text="Modifier un champ")
        upd.pack(fill="x", padx=10, pady=6)
        self.upd_field = tk.StringVar(value="email")
        self.upd_value = tk.StringVar()

        rowu = ttk.Frame(upd);
        rowu.pack(fill="x", padx=6, pady=2)
        ttk.Label(rowu, text="Champ").pack(side="left", padx=4)

        # ⬇️ Combobox au lieu d'un Entry
        ttk.Combobox(
            rowu,
            textvariable=self.upd_field,
            width=20,
            values=("nom", "prenom", "categorie", "email", "domaine", "telephone", "matricule"),
            state="readonly"
        ).pack(side="left")

        ttk.Label(rowu, text="Nouvelle valeur").pack(side="left", padx=8)
        ttk.Entry(rowu, textvariable=self.upd_value, width=32).pack(side="left")

        ttk.Button(upd, text="Modifier", command=self.update_member).pack(anchor="e", padx=10, pady=4)

        # Sortie admin + bouton Effacer
        out = ttk.LabelFrame(self, text="Résultat")
        out.pack(fill="both", expand=True, padx=10, pady=8)
        self.admin_out = tk.Text(out, wrap="word", height=14, bg="#fff8ee")  # fond doux
        self.admin_out.pack(fill="both", expand=True)
        self.admin_out.config(state="disabled")
        btns2 = ttk.Frame(self); btns2.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(btns2, text="Effacer", command=lambda: set_text(self.admin_out, "")).pack(side="right")

    # -------- actions admin --------
    def _pwd(self):
        return {"password": self.pwd_var.get().strip()}

    def add_member(self):
        d = {
            "nom": self.add_nom.get().strip(),
            "prenom": self.add_prenom.get().strip(),
            "categorie": self.add_cat.get().strip(),
            "email": self.add_email.get().strip(),
            "matricule": self.add_matricule.get().strip(),
            "domaine": self.add_domaine.get().strip(),
            "telephone": self.add_tel.get().strip(),
        }
        # Vérif email GUI avant RPC
        if not is_valid_email(d["email"]):
            messagebox.showwarning("Email invalide", "Merci de saisir un email valide (ex: nom@domaine.tld).")
            return
        try:
            res = rpc({"action": "ADD_MEMBER", "auth": self._pwd(), "data": d})
            set_text(self.admin_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def delete_member(self):
        mid = self.op_id.get().strip()
        if not mid:
            messagebox.showwarning("Champ manquant", "Saisis un ID membre.")
            return
        try:
            res = rpc({"action": "DELETE_MEMBER", "auth": self._pwd(), "data": {"id": mid}})
            set_text(self.admin_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def set_red(self, value: bool):
        mid = self.op_id.get().strip()
        if not mid:
            messagebox.showwarning("Champ manquant", "Saisis un ID membre.")
            return
        try:
            action = "SET_RED_FLAG" if value else "UNSET_RED_FLAG"
            res = rpc({"action": action, "auth": self._pwd(), "data": {"id": mid}})
            set_text(self.admin_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def update_member(self):
        mid = self.op_id.get().strip()
        fld = self.upd_field.get().strip()
        val = self.upd_value.get().strip()
        if not mid or not fld or not val:
            messagebox.showwarning("Champs manquants", "ID, champ et valeur sont requis.")
            return
        # Si on modifie l'email, vérifie le format côté GUI
        if fld.lower() == "email" and not is_valid_email(val):
            messagebox.showwarning("Email invalide", "Merci de saisir un email valide (ex: nom@domaine.tld).")
            return
        try:
            res = rpc({"action": "UPDATE_MEMBER", "auth": self._pwd(), "data": {"id": mid, fld: val}})
            set_text(self.admin_out, pretty(res))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    App().mainloop()
