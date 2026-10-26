import json, threading, uuid
from pathlib import Path
from common.models import Membre
from server.config import DATA_FILE

_lock = threading.Lock()
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")

def _load():
    with _lock:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def _save(items):
    with _lock:
        DATA_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def _to_public_view(row: dict):
    return Membre(**row).to_public()

def list_by_category(cat: str):
    rows = _load()
    out = []
    for r in rows:
        if (r.get("categorie") or "").lower() == (cat or "").lower():
            out.append(_to_public_view(r))
    return out

def list_prof_by_domain(domain: str):
    rows = _load()
    dom = (domain or "").lower()
    out = []
    for r in rows:
        if (r.get("categorie") == "prof") and (r.get("domaine") or "").lower() == dom:
            out.append(_to_public_view(r))
    return out

def search_member(query: str):
    q = (query or "").lower()
    rows = _load()
    out = []
    for r in rows:
        nom = (r.get("nom") or "").lower()
        prenom = (r.get("prenom") or "").lower()
        mat = (r.get("matricule") or "").lower()
        if q in nom or q in prenom or q == mat:
            out.append(_to_public_view(r))
    return out

def add_member(payload: dict):
    rows = _load()
    payload = payload.copy()
    # unicité sur matricule s'il est fourni
    mat = (payload.get("matricule") or "").strip().lower()
    if mat:
        for r in rows:
            if (r.get("matricule") or "").strip().lower() == mat:
                raise ValueError("DUPLICATE_MATRICULE")

    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("liste_rouge", False)
    rows.append(payload)
    _save(rows)
    return payload["id"]


def delete_member(member_id: str) -> bool:
    rows = _load()
    new_rows = [r for r in rows if r.get("id") != member_id]
    changed = len(new_rows) != len(rows)
    if changed:
        _save(new_rows)
    return changed

def update_member(member_id: str, updates: dict) -> bool:
    if not updates:
        return False
    allowed = {"nom","prenom","categorie","email","domaine","telephone","matricule","liste_rouge"}
    rows = _load()
    changed = False
    for r in rows:
        if r.get("id") == member_id:
            for k, v in updates.items():
                if k in allowed:
                    r[k] = v
            changed = True
            break
    if changed:
        _save(rows)
    return changed

def set_red_flag(member_id: str, value: bool) -> bool:
    return update_member(member_id, {"liste_rouge": bool(value)})
