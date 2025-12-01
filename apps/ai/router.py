import re
from typing import List, Tuple

# Module regex map and default base URLs
MODULES: List[Tuple[str, str]] = [
    ("clients",  r"(client|crm|adresse(s)?|livraison(s)?|shipping|delivery|facturation)"),
    ("cuvees",   r"cuv(ée|e|ées|es)|cuve(s)?"),
    ("ventes",   r"(commande|vente|devis|facture)(s)?"),
    ("produits", r"(produit|sku|tarif|prix)(s)?"),
    ("stocks",   r"(stock|inventaire|mouvement)(s)?"),
    ("drm",      r"(drm|douane|inao|crd)"),
    ("mises",    r"(mise\s+en\s+bouteille|mise|tirage|bouteille)(s)?"),
]

BASES = {
    "clients": "/clients/",
    "cuvees": "/produits/cuvees/",
    "ventes": "/ventes/commandes/",
    "produits": "/catalogue/produits/",
    "stocks": "/stocks/",
    "drm": "/drm/",
    "mises": "/production/mises/",
}


def resolve_page_effective(page_url: str, question: str) -> str:
    """
    Resolve the effective page from the current page URL and a natural-language question.
    - If already on a known base, keep it.
    - If on dashboard, infer module from question and map to its base URL.
    - Else, return the original page.
    """
    page_url = (page_url or "/").strip()
    if any(page_url.startswith(b) for b in BASES.values()):
        return page_url

    if page_url.startswith("/dashboard") or page_url == "/":
        q = (question or "").lower()
        for name, rx in MODULES:
            if re.search(rx, q):
                return BASES[name]

    return page_url
