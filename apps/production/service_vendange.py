from __future__ import annotations
from django.db import transaction
from .models import VendangeReception
from apps.referentiels.models import Cuvee


def affecter_cuvee(vendange_id, cuvee_id) -> None:
    """Affecte/Met à jour la cuvée cible d'une vendange.
    Soft-checks only; validation cross-org à faire dans la vue si nécessaire.
    """
    with transaction.atomic():
        v = VendangeReception.objects.select_for_update().get(pk=vendange_id)
        c = Cuvee.objects.select_for_update().get(pk=cuvee_id)
        # Same-organization policy (if both set)
        if getattr(v, 'organization_id', None) and getattr(c, 'organization_id', None):
            if v.organization_id != c.organization_id:
                raise ValueError("Organisation incohérente entre vendange et cuvée")
        # If vendange has no organization yet, adopt cuvée's
        if not getattr(v, 'organization_id', None) and getattr(c, 'organization_id', None):
            v.organization_id = c.organization_id
        v.cuvee_id = cuvee_id
        # Update workflow status
        try:
            if hasattr(v, 'statut') and v.statut in (None, '', 'brouillon', 'receptionnee'):
                v.statut = 'affectee_cuvee'
        except Exception:
            pass
        v.save(update_fields=["cuvee", "organization", "statut"] if hasattr(v, 'statut') else ["cuvee", "organization"])
