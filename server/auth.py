from server.config import ADMIN_PASSWORD

def is_admin(password: str | None) -> bool:
    return bool(password) and password == ADMIN_PASSWORD
