from django.db.models.signals import post_migrate
from django.dispatch import receiver

try:
    from .models_parcelle_journal import ParcelleOperationType
except Exception:  # during initial migrate
    ParcelleOperationType = None  # type: ignore

SEED_TYPES = [
    ("taille", "Taille", "scissors", 10),
    ("traitement", "Traitement", "spray", 20),
    ("travail_sol", "Travail du sol", "shovel", 30),
    ("palissage", "Palissage", "crop", 40),
    ("effeuillage", "Effeuillage", "leaf", 50),
    ("fertilisation", "Fertilisation", "droplet", 60),
    ("irrigation", "Irrigation", "water", 70),
    ("autre", "Autre", "tool", 99),
]


@receiver(post_migrate)
def seed_parcelle_operation_types(sender, **kwargs):
    # Only seed for our app
    if sender and getattr(sender, 'name', '') != 'apps.viticulture':
        return
    if ParcelleOperationType is None:
        return
    try:
        for code, label, icon, order in SEED_TYPES:
            obj, _ = ParcelleOperationType.objects.get_or_create(
                code=code,
                defaults={"label": label, "icon": icon, "order": order},
            )
            # If exists, we keep existing label/icon/order to avoid overriding user customizations
    except Exception:
        # best-effort seeding; ignore errors during partial envs
        pass
