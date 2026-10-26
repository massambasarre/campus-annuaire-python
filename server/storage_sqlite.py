# server/storage_sqlite.py
import sqlite3, threading, uuid, json
from pathlib import Path
from common.models import Membre
from server.config import _cfg  # on réutilise le ConfigParser déjà chargé

DB_FILE = Path(_cfg.get("storage", "db_file", fallback="server/data/annuaire.sqlite3"))
JSON_FILE = Path(_cfg.get("storage", "data_file", fallback="server/data/data.json"))

_lock = threading.Lock()
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

def _conn():
    # Un connect par appel (léger). Row factory pour dict-like.
    c = sqlite3.connect(DB_FILE, timeout=5)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS membres (
            id TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            categorie TEXT NOT NULL,
            email TEXT NOT NULL,
            domaine TEXT,
            telephone TEXT,
            matricule TEXT,
            liste_rouge INTEGER NOT NULL DEFAULT 0
        )
        """)
        # index utiles
        c.execute("CREATE INDEX IF NOT EXISTS ix_cat ON membres(categorie)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_dom ON membres(domaine)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_mat ON membres(matricule)")
        c.commit()

def _row_to_public(r: sqlite3.Row):
    # respecte la liste rouge via le modèle
    return Membre(**dict(r)).to_public()

# ---------- Services lecture ----------
def list_by_category(cat: str):
    with _conn() as c:
        cur = c.execute("SELECT * FROM membres WHERE LOWER(categorie)=LOWER(?)", (cat or "",))
        return [_row_to_public(r) for r in cur.fetchall()]

def list_prof_by_domain(domain: str):
    with _conn() as c:
        cur = c.execute("""
            SELECT * FROM membres
            WHERE LOWER(categorie)='prof' AND LOWER(COALESCE(domaine,''))=LOWER(?)
        """, (domain or "",))
        return [_row_to_public(r) for r in cur.fetchall()]

def search_member(q: str):
    q = (q or "").lower()
    with _conn() as c:
        cur = c.execute("""
            SELECT * FROM membres
            WHERE LOWER(nom) LIKE ? OR LOWER(prenom) LIKE ? OR LOWER(COALESCE(matricule,''))=?
        """, (f"%{q}%", f"%{q}%", q))
        return [_row_to_public(r) for r in cur.fetchall()]

# ---------- Services écriture ----------
def add_member(payload: dict):
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("liste_rouge", False)
    with _lock:   # verrou léger pour éviter updates concurrents incohérents
        with _conn() as c:
            # unicité matricule si fourni
            mat = (payload.get("matricule") or "").strip().lower()
            if mat:
                cur = c.execute("SELECT 1 FROM membres WHERE LOWER(COALESCE(matricule,''))=?", (mat,))
                if cur.fetchone():
                    raise ValueError("DUPLICATE_MATRICULE")

            c.execute("""
                INSERT INTO membres(id, nom, prenom, categorie, email, domaine, telephone, matricule, liste_rouge)
                VALUES (:id, :nom, :prenom, :categorie, :email, :domaine, :telephone, :matricule, :liste_rouge)
            """, payload)
            c.commit()
    return payload["id"]

def delete_member(member_id: str) -> bool:
    with _lock:
        with _conn() as c:
            cur = c.execute("DELETE FROM membres WHERE id=?", (member_id,))
            c.commit()
            return cur.rowcount > 0

def update_member(member_id: str, updates: dict) -> bool:
    if not updates:
        return False
    allowed = {"nom","prenom","categorie","email","domaine","telephone","matricule","liste_rouge"}
    fields, params = [], []
    for k, v in updates.items():
        if k in allowed:
            fields.append(f"{k}=?")
            params.append(v)
    if not fields:
        return False
    params.append(member_id)
    with _lock:
        with _conn() as c:
            # unicité matricule si on le modifie
            if "matricule" in updates and (updates.get("matricule") or "").strip():
                mat = (updates["matricule"] or "").strip().lower()
                cur = c.execute("SELECT id FROM membres WHERE LOWER(COALESCE(matricule,''))=?", (mat,))
                row = cur.fetchone()
                if row and row["id"] != member_id:
                    raise ValueError("DUPLICATE_MATRICULE")

            cur = c.execute(f"UPDATE membres SET {', '.join(fields)} WHERE id=?", params)
            c.commit()
            return cur.rowcount > 0

def set_red_flag(member_id: str, value: bool) -> bool:
    return update_member(member_id, {"liste_rouge": 1 if value else 0})

# ---------- (Optionnel) Import initial depuis JSON ----------
def import_from_json_if_empty():
    """
    Si la table est vide et qu'un data.json existe, importe les entrées.
    Utile pour migrer rapidement depuis votre ancien stockage JSON.
    """
    try:
        with _conn() as c:
            cur = c.execute("SELECT COUNT(*) AS n FROM membres")
            if cur.fetchone()["n"] > 0:
                return 0
        if not JSON_FILE.exists():
            return 0
        items = json.loads(JSON_FILE.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            return 0
        count = 0
        with _lock:
            with _conn() as c:
                for r in items:
                    r = r.copy()
                    r.setdefault("id", str(uuid.uuid4()))
                    r.setdefault("liste_rouge", False)
                    c.execute("""
                        INSERT OR IGNORE INTO membres(id, nom, prenom, categorie, email, domaine, telephone, matricule, liste_rouge)
                        VALUES (:id, :nom, :prenom, :categorie, :email, :domaine, :telephone, :matricule, :liste_rouge)
                    """, r)
                    count += 1
                c.commit()
        return count
    except Exception:
        return 0
