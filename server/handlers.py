# server/handlers.py
import re

from server import storage_sqlite as storage
from server.auth import is_admin
from common.messages import ACTIONS
from common.protocol import ok, err

# --- validations locales ---
VALID_CATEGORIES = {"prof", "aux", "etudiant"}
# Regex simple et robuste (pas d'espaces, un @, pas de .., TLD ≥ 2)
EMAIL_RE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def handle(request: dict):
    action = request.get("action")
    data = request.get("data", {}) or {}
    auth = request.get("auth", {}) or {}

    if action == ACTIONS["PING"]:
        return ok({"pong": True})

    if action == ACTIONS["LIST_BY_CATEGORY"]:
        cat = data.get("categorie")
        if not cat:
            return err("MISSING_CATEGORY")
        return ok(storage.list_by_category(cat))

    if action == ACTIONS["LIST_PROF_BY_DOMAIN"]:
        dom = data.get("domaine")
        if not dom:
            return err("MISSING_DOMAIN")
        return ok(storage.list_prof_by_domain(dom))

    if action == ACTIONS["SEARCH_MEMBER"]:
        q = data.get("q", "")
        return ok(storage.search_member(q))

    # --- ADMIN ---
    if action == ACTIONS["ADD_MEMBER"]:
        if not is_admin(auth.get("password")):
            return err("UNAUTHORIZED")

        d = data or {}
        if (d.get("categorie") or "").lower() not in VALID_CATEGORIES:
            return err("INVALID_CATEGORY")
        if not d.get("nom") or not d.get("prenom") or not d.get("email"):
            return err("MISSING_FIELDS")
        if not EMAIL_RE.match(d["email"]):
            return err("INVALID_EMAIL")

        try:
            new_id = storage.add_member(d)
            return ok({"id": new_id})
        except ValueError as e:
            return err(str(e))

    if action == ACTIONS["DELETE_MEMBER"]:
        if not is_admin(auth.get("password")):
            return err("UNAUTHORIZED")
        return ok({"deleted": storage.delete_member(data.get("id", ""))})

    if action == ACTIONS["UPDATE_MEMBER"]:
        if not is_admin(auth.get("password")):
            return err("UNAUTHORIZED")
        mid = data.get("id", "")
        if not mid:
            return err("MISSING_ID")

        updates = {k: v for k, v in data.items() if k != "id" and v not in (None, "")}
        # validations légères si présents
        cat = updates.get("categorie")
        if cat and cat.lower() not in VALID_CATEGORIES:
            return err("INVALID_CATEGORY")
        mail = updates.get("email")
        if mail and not EMAIL_RE.match(mail):
            return err("INVALID_EMAIL")

        return ok({"updated": storage.update_member(mid, updates)})

    if action == ACTIONS["SET_RED_FLAG"]:
        if not is_admin(auth.get("password")):
            return err("UNAUTHORIZED")
        return ok({"updated": storage.set_red_flag(data.get("id", ""), True)})

    if action == ACTIONS["UNSET_RED_FLAG"]:
        if not is_admin(auth.get("password")):
            return err("UNAUTHORIZED")
        return ok({"updated": storage.set_red_flag(data.get("id", ""), False)})

    return err("UNKNOWN_ACTION")
