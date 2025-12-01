"""
Signaux Django pour l'app accounts - Roadmap 09
Signal post-Organization create: créer automatiquement la checklist
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model
from .models import Organization, OrgSetupChecklist, UserProfile, OrgBilling

User = get_user_model()


@receiver(post_save, sender=Organization)
def create_organization_checklist(sender, instance, created, **kwargs):
    """
    Créer automatiquement une checklist d'onboarding après création d'organisation
    Signal selon roadmap 09 - Étape 1.3
    """
    if created:
        # Créer la checklist avec l'état par défaut
        OrgSetupChecklist.objects.create(
            organization=instance,
            state=OrgSetupChecklist.get_default_state()
        )


@receiver(post_save, sender=Organization)
def create_organization_billing(sender, instance, created, **kwargs):
    """
    Créer automatiquement un enregistrement de facturation après création d'organisation
    Signal selon roadmap 11 - Étape 1.2
    """
    if created:
        # Créer l'enregistrement de facturation avec valeurs par défaut
        OrgBilling.objects.create(
            organization=instance,
            legal_name='',
            billing_address_line1='',
            billing_postal_code='',
            billing_city='',
            billing_country='France',
            vat_status='not_subject_to_vat'
        )


@receiver(post_save, sender=Organization)
def create_default_unites(sender, instance, created, **kwargs):
    """
    Créer automatiquement les unités de mesure par défaut après création d'organisation
    """
    if created:
        from apps.referentiels.models import Unite
        from decimal import Decimal
        
        default_unites = [
            # Volume
            {'nom': 'Litre', 'symbole': 'L', 'type_unite': 'volume', 'facteur_conversion': Decimal('1.0000')},
            {'nom': 'Hectolitre', 'symbole': 'hL', 'type_unite': 'volume', 'facteur_conversion': Decimal('100.0000')},
            {'nom': 'Bouteille 75cl', 'symbole': 'btl', 'type_unite': 'volume', 'facteur_conversion': Decimal('0.7500')},
            {'nom': 'Magnum 1.5L', 'symbole': 'mag', 'type_unite': 'volume', 'facteur_conversion': Decimal('1.5000')},
            {'nom': 'Jéroboam 3L', 'symbole': 'jér', 'type_unite': 'volume', 'facteur_conversion': Decimal('3.0000')},
            {'nom': 'Bag-in-Box 5L', 'symbole': 'BIB5', 'type_unite': 'volume', 'facteur_conversion': Decimal('5.0000')},
            {'nom': 'Bag-in-Box 10L', 'symbole': 'BIB10', 'type_unite': 'volume', 'facteur_conversion': Decimal('10.0000')},
            # Poids
            {'nom': 'Kilogramme', 'symbole': 'kg', 'type_unite': 'poids', 'facteur_conversion': Decimal('1.0000')},
            {'nom': 'Tonne', 'symbole': 't', 'type_unite': 'poids', 'facteur_conversion': Decimal('1000.0000')},
            {'nom': 'Gramme', 'symbole': 'g', 'type_unite': 'poids', 'facteur_conversion': Decimal('0.0010')},
            # Surface
            {'nom': 'Hectare', 'symbole': 'ha', 'type_unite': 'surface', 'facteur_conversion': Decimal('1.0000')},
            {'nom': 'Are', 'symbole': 'a', 'type_unite': 'surface', 'facteur_conversion': Decimal('0.0100')},
            # Quantité
            {'nom': 'Unité', 'symbole': 'u', 'type_unite': 'quantite', 'facteur_conversion': Decimal('1.0000')},
            {'nom': 'Carton 6', 'symbole': 'cart6', 'type_unite': 'quantite', 'facteur_conversion': Decimal('6.0000')},
            {'nom': 'Carton 12', 'symbole': 'cart12', 'type_unite': 'quantite', 'facteur_conversion': Decimal('12.0000')},
            {'nom': 'Palette', 'symbole': 'pal', 'type_unite': 'quantite', 'facteur_conversion': Decimal('1.0000')},
        ]
        
        for u in default_unites:
            Unite.objects.get_or_create(
                organization=instance,
                nom=u['nom'],
                defaults={
                    'symbole': u['symbole'],
                    'type_unite': u['type_unite'],
                    'facteur_conversion': u['facteur_conversion'],
                }
            )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Créer automatiquement un profil utilisateur après création d'utilisateur
    Signal selon roadmap 10 - Étape 1.2
    """
    if created:
        # Créer le profil avec les valeurs par défaut
        UserProfile.objects.create(
            user=instance,
            locale='fr',
            timezone='Europe/Paris'
        )
