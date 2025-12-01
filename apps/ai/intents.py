import re
from typing import Optional, Dict, Any

# Minimal intents per module (RAG light)
INTENTS: Dict[str, Dict[str, Any]] = {
    "clients.create": {
        "match": r"(nouveau|ajouter|cr[eé]er).*(client)",
        "steps": [
            "Ouvrir Clients → Liste.",
            "Cliquer Nouveau client et choisir le type (Particulier / Pro / Caviste / Export).",
            "Renseigner identité, contacts et adresses.",
            "Onglet Conditions : liste de prix, remise, TVA.",
            "Enregistrer.",
        ],
        "see_also": "/clients/",
    },
    "cuvees.edit": {
        "match": r"(éditer|modifier).*(cuv(ée|e|ées|es)|cuve)",
        "steps": [
            "Produits → Cuvées, sélectionner la cuvée puis Éditer.",
            "Mettre à jour nom, millésime, appellation, statut.",
            "Onglet Assemblage : rattacher/retirer des lots techniques et sauvegarder.",
            "Onglet Conformité : vérifier les mentions légales.",
            "Enregistrer.",
        ],
        "see_also": "/produits/cuvees/",
    },
    # Ajoute 1–2 intents par module si besoin
}


def intent_for(question: str) -> Optional[Dict[str, Any]]:
    q = (question or "").lower()
    for key, obj in INTENTS.items():
        rx = obj.get("match")
        if rx and re.search(rx, q):
            return obj
    return None
