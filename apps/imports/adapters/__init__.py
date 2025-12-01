"""
Adapters d'entités pour le système d'import générique
Configuration spécifique par type d'entité
"""

from .grape_variety import GrapeVarietyImportAdapter
from .parcelle import ParcelleImportAdapter
from .unite import UniteImportAdapter
from .cuvee import CuveeImportAdapter
from .entrepot import EntrepotImportAdapter

# Registry des adapters disponibles
IMPORT_ADAPTERS = {
    'grape_variety': GrapeVarietyImportAdapter,
    'parcelle': ParcelleImportAdapter,
    'unite': UniteImportAdapter,
    'cuvee': CuveeImportAdapter,
    'entrepot': EntrepotImportAdapter,
}

def get_adapter(entity_type: str):
    """Récupère l'adapter pour un type d'entité"""
    if entity_type not in IMPORT_ADAPTERS:
        raise ValueError(f"Adapter non trouvé pour l'entité '{entity_type}'")
    return IMPORT_ADAPTERS[entity_type]()
