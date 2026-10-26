from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Membre:
    id: str
    nom: str
    prenom: str
    categorie: str            # "prof", "aux", "etudiant"
    email: str
    domaine: Optional[str] = None
    telephone: Optional[str] = None
    matricule: Optional[str] = None
    liste_rouge: bool = False

    def to_public(self):
        if self.liste_rouge:
            return {"nom": self.nom, "prenom": self.prenom, "liste_rouge": True}
        return asdict(self)
