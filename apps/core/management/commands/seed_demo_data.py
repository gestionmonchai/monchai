import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization
from apps.clients.models import Customer
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

        # Client
        client, created = Customer.objects.get_or_create(
            organization=org,
            name='Jean Dupont', # Le modèle utilise 'name', sales.Customer utilise 'legal_name' ? Vérifions sales.models
            # sales.models.Customer a 'legal_name', clients.models.Customer a 'name'.
            # Le prompt demande "un client", je vais créer un client dans le module `clients` car c'est le nouveau module,
            # MAIS le module `sales` a son propre modèle `Customer`. 
            # D'après l'analyse des fichiers, `apps.sales.models.Customer` semble être celui utilisé par Quote/Order.
            # Je vais donc créer un `apps.sales.models.Customer` pour que le devis fonctionne.
        )
        
        # ATTENTION: Il y a deux modèles Customer !
        # apps.clients.models.Customer (Nouveau)
        # apps.sales.models.Customer (Ancien/Actuel pour les ventes)
        # Pour satisfaire la demande "créer un devis", je dois utiliser le Customer de `sales`.
        
        # Création Client Ventes (Sales)
        from apps.sales.models import Customer as SalesCustomer
        client_sales, created = SalesCustomer.objects.get_or_create(
            organization=org,
            legal_name='Restaurant La Belle Table',
            defaults={
                'type': 'pro',
                'vat_number': 'FR99123456789',
                'billing_address': '10 Rue de la Gastronomie',
                'billing_postal_code': '75001',
                'billing_city': 'Paris',
            }
        )
        self.stdout.write(f'  - Client (Ventes) créé : {client_sales.legal_name}')

        # Création Fournisseur (Clients module - nouveau standard)
        # Le module `clients` gère les segments, dont 'supplier'.
        fournisseur, created = Customer.objects.get_or_create(
            organization=org,
            name='Verrerie du Sud-Ouest',
            defaults={
                'segment': 'supplier',
                'vat_number': 'FR88987654321',
                'country_code': 'FR',
                'email': 'contact@verrerie-so.fr',
                'phone': '+33556000000'
            }
        )
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
