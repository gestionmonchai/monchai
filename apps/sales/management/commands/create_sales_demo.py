"""
Commande Django pour créer des données de démonstration pour les ventes
DB Roadmap 03 - Ventes, Clients & Pricing
"""

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization, Membership
from apps.viticulture.models import UnitOfMeasure, GrapeVariety, Appellation, Vintage, Cuvee, Warehouse
from apps.stock.models import SKU, StockSKUBalance, StockManager
from apps.sales.models import (
    TaxCode, Customer, PriceList, PriceItem, CustomerPriceList,
    Quote, QuoteLine, Order, OrderLine
)
from apps.sales.managers import SalesManager

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour le système de ventes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-name',
            type=str,
            default='Domaine de Démonstration',
            help='Nom de l\'organisation (défaut: "Domaine de Démonstration")'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        org_name = options['org_name']
        
        self.stdout.write(f'Création des données de ventes pour "{org_name}"')
        
        # 1. Organisation et utilisateur (réutiliser existants ou créer)
        try:
            org = Organization.objects.get(name=org_name)
            self.stdout.write(f'[OK] Organisation existante: {org.name}')
        except Organization.DoesNotExist:
            siret_demo = f"9876543210{random.randint(1000, 9999)}"
            org = Organization.objects.create(
                name=org_name,
                siret=siret_demo,
                address='123 Route des Vignes',
                postal_code='33000',
                city='Bordeaux',
                country='France'
            )
            self.stdout.write(f'[OK] Organisation créée: {org.name}')
        
        # Utilisateur
        user, created = User.objects.get_or_create(
            email='demo@monchai.fr',
            defaults={
                'username': 'demo',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'[OK] Utilisateur créé: {user.email}')
        else:
            self.stdout.write(f'[OK] Utilisateur existant: {user.email}')
        
        # Membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': 'admin'}
        )
        
        # 2. Codes taxes
        self.stdout.write('\n[TAXES] Création des codes taxes...')
        
        tax_codes = {}
        taxes_data = [
            {'code': 'TVA20', 'name': 'TVA 20%', 'rate': Decimal('20.00'), 'country': 'FR'},
            {'code': 'TVA10', 'name': 'TVA 10%', 'rate': Decimal('10.00'), 'country': 'FR'},
            {'code': 'TVA0', 'name': 'TVA 0%', 'rate': Decimal('0.00'), 'country': 'FR'},
            {'code': 'VAT20', 'name': 'VAT 20%', 'rate': Decimal('20.00'), 'country': 'GB'},
        ]
        
        for tax_data in taxes_data:
            tax_code, created = TaxCode.objects.get_or_create(
                organization=org,
                code=tax_data['code'],
                defaults={
                    'name': tax_data['name'],
                    'rate_pct': tax_data['rate'],
                    'country': tax_data['country']
                }
            )
            tax_codes[tax_data['code']] = tax_code
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {tax_code.code} - {tax_code.rate_pct}%')
        
        # 3. Clients de démonstration
        self.stdout.write('\n[CLIENTS] Création des clients...')
        
        customers = {}
        customers_data = [
            {
                'type': 'part',
                'legal_name': 'Jean Dupont',
                'billing_address': '15 Rue de la République',
                'billing_postal_code': '75001',
                'billing_city': 'Paris',
                'billing_country': 'FR',
                'currency': 'EUR'
            },
            {
                'type': 'part',
                'legal_name': 'Marie Martin',
                'billing_address': '42 Avenue des Champs',
                'billing_postal_code': '69001',
                'billing_city': 'Lyon',
                'billing_country': 'FR',
                'currency': 'EUR'
            },
            {
                'type': 'pro',
                'legal_name': 'Vins & Spiritueux SARL',
                'vat_number': 'FR12345678901',
                'billing_address': '123 Zone Industrielle',
                'billing_postal_code': '33300',
                'billing_city': 'Bordeaux',
                'billing_country': 'FR',
                'currency': 'EUR',
                'payment_terms': '30j'
            },
            {
                'type': 'pro',
                'legal_name': 'Wine Import Ltd',
                'vat_number': 'GB987654321',
                'billing_address': '456 Business Park',
                'billing_postal_code': 'SW1A 1AA',
                'billing_city': 'London',
                'billing_country': 'GB',
                'currency': 'EUR',
                'payment_terms': '45j'
            },
            {
                'type': 'pro',
                'legal_name': 'Weinhandel GmbH',
                'vat_number': 'DE555666777',
                'billing_address': '789 Hauptstraße',
                'billing_postal_code': '10115',
                'billing_city': 'Berlin',
                'billing_country': 'DE',
                'currency': 'EUR',
                'payment_terms': '30j'
            }
        ]
        
        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                organization=org,
                legal_name=customer_data['legal_name'],
                defaults=customer_data
            )
            customers[customer_data['legal_name']] = customer
            status = '[OK] Créé' if created else '[OK] Existant'
            client_type = customer.get_type_display()
            self.stdout.write(f'  {status}: {customer.legal_name} ({client_type})')
        
        # 4. Grilles tarifaires
        self.stdout.write('\n[PRIX] Création des grilles tarifaires...')
        
        # Vérifier qu'on a des SKUs (créés par create_stock_demo)
        skus = list(SKU.objects.filter(organization=org))
        if not skus:
            self.stdout.write(self.style.WARNING(
                '  [WARN] Aucun SKU trouvé. Exécutez d\'abord: python manage.py create_stock_demo'
            ))
            return
        
        price_lists = {}
        price_lists_data = [
            {
                'name': 'Tarif Public',
                'currency': 'EUR',
                'valid_from': timezone.now().date(),
                'is_default': True
            },
            {
                'name': 'Tarif Professionnel',
                'currency': 'EUR',
                'valid_from': timezone.now().date(),
                'is_default': False
            },
            {
                'name': 'Tarif VIP',
                'currency': 'EUR',
                'valid_from': timezone.now().date(),
                'is_default': False
            }
        ]
        
        for pl_data in price_lists_data:
            price_list, created = PriceList.objects.get_or_create(
                organization=org,
                name=pl_data['name'],
                defaults={
                    'currency': pl_data['currency'],
                    'valid_from': pl_data['valid_from']
                }
            )
            price_lists[pl_data['name']] = price_list
            status = '[OK] Créée' if created else '[OK] Existante'
            self.stdout.write(f'  {status}: {price_list.name}')
            
            # Créer les prix pour chaque SKU
            if created:
                base_prices = {
                    'Tarif Public': Decimal('18.00'),
                    'Tarif Professionnel': Decimal('15.00'),
                    'Tarif VIP': Decimal('12.00')
                }
                
                base_price = base_prices[pl_data['name']]
                
                for i, sku in enumerate(skus):
                    # Prix variable selon le produit
                    if 'Magnum' in sku.label:
                        unit_price = base_price * Decimal('2.2')  # Magnum plus cher
                    elif 'Bouteille' in sku.label:
                        unit_price = base_price
                    else:
                        unit_price = base_price * Decimal('1.1')
                    
                    # Prix unitaire
                    PriceItem.objects.create(
                        organization=org,
                        price_list=price_list,
                        sku=sku,
                        unit_price=unit_price,
                        min_qty=1
                    )
                    
                    # Prix par 6 (remise 5%)
                    if pl_data['name'] != 'Tarif VIP':  # VIP a déjà le meilleur prix
                        PriceItem.objects.create(
                            organization=org,
                            price_list=price_list,
                            sku=sku,
                            unit_price=unit_price,
                            min_qty=6,
                            discount_pct=Decimal('5.00')
                        )
                    
                    # Prix par 12 (remise 10%)
                    if pl_data['name'] == 'Tarif Public':
                        PriceItem.objects.create(
                            organization=org,
                            price_list=price_list,
                            sku=sku,
                            unit_price=unit_price,
                            min_qty=12,
                            discount_pct=Decimal('10.00')
                        )
                
                self.stdout.write(f'    [OK] {len(skus)} prix créés pour {price_list.name}')
        
        # 5. Associations clients-grilles
        self.stdout.write('\n[ASSOCIATIONS] Liaison clients-grilles...')
        
        # Particuliers → Tarif Public
        for customer_name in ['Jean Dupont', 'Marie Martin']:
            if customer_name in customers:
                CustomerPriceList.objects.get_or_create(
                    customer=customers[customer_name],
                    price_list=price_lists['Tarif Public'],
                    defaults={'priority': 1}
                )
        
        # Professionnels → Tarif Professionnel
        for customer_name in ['Vins & Spiritueux SARL', 'Wine Import Ltd']:
            if customer_name in customers:
                CustomerPriceList.objects.get_or_create(
                    customer=customers[customer_name],
                    price_list=price_lists['Tarif Professionnel'],
                    defaults={'priority': 1}
                )
        
        # VIP → Tarif VIP
        if 'Weinhandel GmbH' in customers:
            CustomerPriceList.objects.get_or_create(
                customer=customers['Weinhandel GmbH'],
                price_list=price_lists['Tarif VIP'],
                defaults={'priority': 1}
            )
        
        self.stdout.write('  [OK] Associations clients-grilles créées')
        
        # 6. Devis de démonstration
        self.stdout.write('\n[DEVIS] Création des devis...')
        
        quotes_created = 0
        
        # Devis pour Jean Dupont (particulier)
        if 'Jean Dupont' in customers and len(skus) >= 2:
            cart_items = [
                {'sku': skus[0], 'qty': 6},  # 6 bouteilles
                {'sku': skus[1], 'qty': 2},  # 2 magnums
            ]
            
            try:
                quote = SalesManager.create_quote_from_cart(
                    customers['Jean Dupont'], 
                    cart_items,
                    valid_days=30
                )
                quotes_created += 1
                self.stdout.write(f'  [OK] Devis créé pour {customers["Jean Dupont"].legal_name}: {quote.total_ttc}€')
            except Exception as e:
                self.stdout.write(f'  [WARN] Erreur devis Jean Dupont: {str(e)}')
        
        # Devis pour professionnel
        if 'Vins & Spiritueux SARL' in customers and len(skus) >= 1:
            cart_items = [
                {'sku': skus[0], 'qty': 24},  # Commande professionnelle
            ]
            
            try:
                quote = SalesManager.create_quote_from_cart(
                    customers['Vins & Spiritueux SARL'], 
                    cart_items,
                    valid_days=45
                )
                quotes_created += 1
                self.stdout.write(f'  [OK] Devis créé pour {customers["Vins & Spiritueux SARL"].legal_name}: {quote.total_ttc}€')
            except Exception as e:
                self.stdout.write(f'  [WARN] Erreur devis professionnel: {str(e)}')
        
        # 7. Commandes de démonstration
        self.stdout.write('\n[COMMANDES] Création des commandes...')
        
        orders_created = 0
        
        # Convertir un devis en commande si possible
        quotes = Quote.objects.filter(organization=org, status='draft')
        if quotes.exists():
            quote = quotes.first()
            quote.status = 'accepted'
            quote.save()
            
            try:
                order = SalesManager.convert_quote_to_order(quote)
                
                # Confirmer la commande si stock disponible
                warehouses = Warehouse.objects.filter(organization=org)
                if warehouses.exists():
                    try:
                        reservations = SalesManager.confirm_order(order, warehouses.first())
                        orders_created += 1
                        self.stdout.write(f'  [OK] Commande confirmée: {order.total_ttc}€ ({len(reservations)} réservations)')
                    except Exception as e:
                        self.stdout.write(f'  [WARN] Confirmation échouée: {str(e)}')
                        
            except Exception as e:
                self.stdout.write(f'  [WARN] Conversion devis échouée: {str(e)}')
        
        # 8. Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] DONNÉES DE VENTES CRÉÉES'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'[STATS] Organisation: {org.name}')
        self.stdout.write(f'[STATS] Codes taxes: {TaxCode.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Clients: {Customer.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Grilles tarifaires: {PriceList.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Éléments de prix: {PriceItem.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Devis: {Quote.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Commandes: {Order.objects.filter(organization=org).count()}')
        
        self.stdout.write('\n[INFO] Utilisez l\'admin Django pour explorer les données créées')
        self.stdout.write('[INFO] Testez la résolution de prix et les commandes')
        self.stdout.write('[INFO] Connexion: demo@monchai.fr / demo123')
