"""
Commande pour initialiser les unités par défaut pour toutes les organisations existantes.
Usage: python manage.py init_default_unites
"""
from django.core.management.base import BaseCommand
from decimal import Decimal

from apps.accounts.models import Organization
from apps.referentiels.models import Unite


DEFAULT_UNITES = [
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


class Command(BaseCommand):
    help = 'Initialize default units for all existing organizations'

    def handle(self, *args, **options):
        orgs = Organization.objects.all()
        total_created = 0
        
        for org in orgs:
            created_count = 0
            for u in DEFAULT_UNITES:
                obj, created = Unite.objects.get_or_create(
                    organization=org,
                    nom=u['nom'],
                    defaults={
                        'symbole': u['symbole'],
                        'type_unite': u['type_unite'],
                        'facteur_conversion': u['facteur_conversion'],
                    }
                )
                if created:
                    created_count += 1
            
            if created_count > 0:
                self.stdout.write(f"  {org.name}: {created_count} unités créées")
                total_created += created_count
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal: {total_created} unités créées pour {orgs.count()} organisations"))
