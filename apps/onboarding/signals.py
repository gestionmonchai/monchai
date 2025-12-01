from __future__ import annotations
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.onboarding.models import OnboardingState


def _state_for_org(org):
    if org is None:
        return None
    st, _ = OnboardingState.objects.get_or_create(organization=org)
    try:
        st.ensure_all_keys()
    except Exception:
        pass
    return st


# Parcelles (référentiels)
try:
    from apps.referentiels.models import Parcelle as RefParcelle
except Exception:  # pragma: no cover - import guard for partial env
    RefParcelle = None


if RefParcelle is not None:

    @receiver(post_save, sender=RefParcelle)
    def onboarding_parcelles_done(sender, instance, created, **kwargs):
        if not created:
            return
        org = getattr(instance, 'organization', None)
        st = _state_for_org(org)
        if st:
            st.mark_done('parcelles')
            st.last_step_completed = 'parcelles'
            st.save()


# Vendanges
try:
    from apps.production.models import VendangeReception, LotTechnique, MouvementLot
except Exception:  # pragma: no cover
    VendangeReception = LotTechnique = MouvementLot = None


if VendangeReception is not None:

    @receiver(post_save, sender=VendangeReception)
    def onboarding_vendanges_done(sender, instance, created, **kwargs):
        if not created:
            return
        org = getattr(instance, 'organization', None)
        st = _state_for_org(org)
        if st:
            st.mark_done('vendanges')
            st.last_step_completed = 'vendanges'
            st.save()


# Encuvages + Lots techniques (création d'un lot technique)
if LotTechnique is not None:

    @receiver(post_save, sender=LotTechnique)
    def onboarding_encuvages_lots_done(sender, instance, created, **kwargs):
        if not created:
            return
        # Derive org via related cuvée
        org = None
        try:
            org = getattr(instance.cuvee, 'organization', None)
        except Exception:
            pass
        st = _state_for_org(org)
        if st:
            # Marquer à la fois encuvages et lots techniques comme réalisés
            try:
                st.mark_done('encuvages')
            except Exception:
                pass
            try:
                st.mark_done('lots')
            except Exception:
                pass
            st.last_step_completed = 'encuvages'
            st.save()


# Pressurage & Élevage / Analyses (interventions & mesures)
try:
    from apps.viticulture.models_extended import LotIntervention, LotMeasurement
except Exception:  # pragma: no cover
    LotIntervention = LotMeasurement = None


if LotIntervention is not None:

    @receiver(post_save, sender=LotIntervention)
    def onboarding_interventions_handler(sender, instance, created, **kwargs):
        if not created:
            return
        org = getattr(instance, 'organization', None)
        st = _state_for_org(org)
        if not st:
            return
        t = getattr(instance, 'type', '')
        if t == 'pressurage':
            st.mark_done('pressurages')
            st.last_step_completed = 'pressurages'
        else:
            st.mark_done('elevage')
            st.last_step_completed = 'elevage'
        st.save()


if LotMeasurement is not None:

    @receiver(post_save, sender=LotMeasurement)
    def onboarding_measurements_handler(sender, instance, created, **kwargs):
        if not created:
            return
        org = getattr(instance, 'organization', None)
        st = _state_for_org(org)
        if st:
            st.mark_done('elevage')
            st.last_step_completed = 'elevage'
            st.save()


# Mises + Stocks bouteilles via LotCommercial (porte l'info cuvée)
try:
    from apps.produits.models import LotCommercial
except Exception:  # pragma: no cover
    LotCommercial = None


if LotCommercial is not None:

    @receiver(post_save, sender=LotCommercial)
    def onboarding_mises_stocks_done(sender, instance, created, **kwargs):
        if not created:
            return
        org = None
        try:
            org = getattr(instance.cuvee, 'organization', None)
        except Exception:
            pass
        st = _state_for_org(org)
        if st:
            try:
                st.mark_done('mises')
            except Exception:
                pass
            try:
                st.mark_done('stocks')
            except Exception:
                pass
            st.last_step_completed = 'mises'
            st.save()


# Ventes / Expéditions via Order
try:
    from apps.sales.models import Order
except Exception:  # pragma: no cover
    Order = None


if Order is not None:

    @receiver(post_save, sender=Order)
    def onboarding_ventes_done(sender, instance, created, **kwargs):
        if not created:
            return
        org = getattr(instance, 'organization', None)
        st = _state_for_org(org)
        if st:
            st.mark_done('ventes')
            st.last_step_completed = 'ventes'
            st.save()
