def pretty(obj):
    import json
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)
# common/utils.py

def print_menu(title: str, options: list[tuple[str, str]]):
    """
    Affiche un menu aligné:
      title  : en-tête (ex: "USER" ou "ADMIN")
      options: liste de tuples (touche, libellé)
    """
    # Largeurs
    key_w = max(len(k) for k, _ in options)
    text_w = max(len(lbl) for _, lbl in options)
    total_w = 4 + key_w + 3 + text_w + 2  # marges + " ) " + libellé + marges

    sep = "-" * total_w
    print(f"\n[{title}]")
    print(sep)
    for k, lbl in options:
        #   espace + clé alignée à droite + ") " + libellé aligné à gauche
        print(f" {k:>{key_w}}) {lbl:<{text_w}} ")
    print(sep)
