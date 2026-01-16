import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization
from apps.partners.models import Contact, ContactRole
from apps.stock.models import SKU, Warehouse, UnitOfMeasure
from apps.viticulture.models import Cuvee, GrapeVariety, Appellation, Vintage
from apps.sales.models import TaxCode, PriceList, PriceItem, Quote, QuoteLine

User = get_user_model()

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de démonstration (Fournisseur, Client, Tarif, Devis, Article)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Début de la création des données de démo...'))

        # 1. Récupération de l\'organisation et de l\'utilisateur
        # On prend la première organisation active ou on en crée une
        org = Organization.objects.first()
        if not org:
            self.stdout.write('Aucune organisation trouvée, création de "Domaine de Démo"...')
            org = Organization.objects.create(name="Domaine de Démo")
        else:
            self.stdout.write(f'Utilisation de l\'organisation : {org.name}')

        user = User.objects.filter(is_superuser=True).first()
        if not user:
             user = User.objects.first()
        
        if not user:
             self.stdout.write(self.style.ERROR('Aucun utilisateur trouvé. Veuillez créer un superuser d\'abord.'))
             return

        # 2. Référentiels Viticoles (Nécessaires pour SKU/Article)
        self.stdout.write('Création des référentiels...')
        
        # Unité
        uom_bouteille, _ = UnitOfMeasure.objects.get_or_create(
            organization=org,
            code='BT',
            defaults={
                'name': 'Bouteille 75cl', 
                'base_ratio_to_l': Decimal('0.75'),
                'is_default': True
            }
        )

        # Entrepôt
        warehouse, _ = Warehouse.objects.get_or_create(
            organization=org,
            name='Chai Principal',
            defaults={'location': 'Bâtiment A'}
        )

        # Cépage
        merlot, _ = GrapeVariety.objects.get_or_create(
            organization=org,
            name_norm='merlot',
            defaults={'name': 'Merlot', 'color': 'rouge'}
        )

        # Appellation
        aoc, _ = Appellation.objects.get_or_create(
            organization=org,
            name_norm='bordeaux',
            defaults={'name': 'Bordeaux', 'type': 'aoc'}
        )

        # Millésime
        vintage, _ = Vintage.objects.get_or_create(
            organization=org,
            year=2022
        )

        # Cuvée
        cuvee, _ = Cuvee.objects.get_or_create(
            organization=org,
            name='Cuvée Prestige',
            defaults={
                'default_uom': uom_bouteille,
                'appellation': aoc,
                'vintage': vintage
            }
        )

        # 3. Article / SKU (Produit fini)
        self.stdout.write('Création de l\'article (SKU)...')
        sku, created = SKU.objects.get_or_create(
            organization=org,
            cuvee=cuvee,
            uom=uom_bouteille,
            defaults={
                'label': 'Cuvée Prestige 2022 - 75cl',
                'volume_by_uom_to_l': Decimal('0.75'),
                'code_barres': '1234567890123'
            }
        )
        if created:
            self.stdout.write(f'  - SKU créé : {sku.label}')
        else:
            self.stdout.write(f'  - SKU existant : {sku.label}')

        # 4. Clients et Fournisseurs
        self.stdout.write('Création des tiers...')

        # Création Client via le modèle Contact unifié
        client_sales, created = Contact.objects.get_or_create(
            organization=org,
            name='Restaurant La Belle Table',
            defaults={
                'partner_type': 'company',
                'segment': 'restaurant',
                'vat_number': 'FR99123456789',
            }
        )
        if created:
            # Ajouter le rôle client
            ContactRole.ensure_defaults()
            client_sales.add_role(ContactRole.ROLE_CLIENT)
        self.stdout.write(f'  - Client créé : {client_sales.name}')

        # Création Fournisseur via le modèle Contact unifié
        fournisseur, created = Contact.objects.get_or_create(
            organization=org,
            name='Verrerie du Sud-Ouest',
            defaults={
                'partner_type': 'company',
                'vat_number': 'FR88987654321',
                'country_code': 'FR',
                'email': 'contact@verrerie-so.fr',
                'phone': '+33556000000'
            }
        )
        if created:
            ContactRole.ensure_defaults()
            fournisseur.add_role(ContactRole.ROLE_SUPPLIER)
        self.stdout.write(f'  - Fournisseur créé : {fournisseur.name}')


        # 5. Données Commerciales (Taxe, Tarif)
        self.stdout.write('Création des données commerciales...')

        # Code Taxe
        tva20, _ = TaxCode.objects.get_or_create(
            organization=org,
            code='TVA20',
            defaults={
                'name': 'TVA Normale 20%',
                'rate_pct': Decimal('20.00'),
                'country': 'FR'
            }
        )

        # Grille Tarifaire
        pricelist, _ = PriceList.objects.get_or_create(
            organization=org,
            name='Tarif Restauration 2025',
            defaults={
                'currency': 'EUR',
                'valid_from': timezone.now().date()
            }
        )

        # Item de prix pour notre SKU
        price_item, created = PriceItem.objects.get_or_create(
            price_list=pricelist,
            sku=sku,
            min_qty=1,
            organization=org, # Requis par BaseSalesModel
            defaults={
                'unit_price': Decimal('15.00'), # 15€ HT la bouteille
                'discount_pct': Decimal('0.00')
            }
        )
        if created:
            self.stdout.write(f'  - Prix défini pour {sku.label} : 15.00€')


        # 6. Devis
        self.stdout.write('Création du devis...')
        
        quote = Quote.objects.create(
            organization=org,
            customer=client_sales,
            status='draft',
            valid_until=timezone.now().date() + timedelta(days=30),
            currency='EUR'
        )

        # Ligne de devis
        QuoteLine.objects.create(
            quote=quote,
            organization=org, # Requis par BaseSalesModel
            sku=sku,
            description=sku.label,
            qty=60, # 60 bouteilles
            unit_price=Decimal('15.00'),
            tax_code=tva20,
            discount_pct=Decimal('5.00') # 5% de remise
        )
        
        # Recalcul des totaux
        quote.calculate_totals()
        quote.save()
        
        self.stdout.write(self.style.SUCCESS(f'Données de démo créées avec succès !'))
        self.stdout.write(f'Organisation : {org.name}')
        self.stdout.write(f'Client : {client_sales.legal_name}')
        self.stdout.write(f'Fournisseur : {fournisseur.name}')
        self.stdout.write(f'Article (SKU) : {sku.label}')
        self.stdout.write(f'Devis créé : N°{quote.id} (Total TTC: {quote.total_ttc}€)')
