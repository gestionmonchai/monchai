"""
Commande de test pour créer des données et tester l'UI des ventes
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization
from apps.sales.models import Customer as SalesCustomer, Order, Quote
from apps.billing.models import Invoice
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de test pour les modules ventes et affiche les URLs de test'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🧪 TEST UI MODULES VENTES\n'))
        
        # 1. Vérifier organisation et utilisateur
        org = Organization.objects.first()
        if not org:
            self.stdout.write(self.style.ERROR('❌ Aucune organisation trouvée'))
            return
        
        user = User.objects.filter(is_active=True).first()
        if not user:
            self.stdout.write(self.style.ERROR('❌ Aucun utilisateur trouvé'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Organisation : {org.name}'))
        self.stdout.write(self.style.SUCCESS(f'✅ Utilisateur : {user.email}'))
        
        # 2. Créer des clients de test
        self.stdout.write(self.style.WARNING('\n📋 Création de clients de test...'))
        
        clients_data = [
            {
                'legal_name': 'Domaine Dupont',
                'type': 'pro',
                'billing_city': 'Bordeaux',
            },
            {
                'legal_name': 'Cave Martin',
                'type': 'pro',
                'billing_city': 'Lyon',
            },
            {
                'legal_name': 'Restaurant Le Gourmet',
                'type': 'pro',
                'billing_city': 'Paris',
            },
            {
                'legal_name': 'Particulier Durand',
                'type': 'part',
                'billing_city': 'Marseille',
            },
        ]
        
        clients = []
        for data in clients_data:
            client, created = SalesCustomer.objects.get_or_create(
                organization=org,
                legal_name=data['legal_name'],
                defaults={
                    'type': data['type'],
                    'billing_address': '1 rue Test',
                    'billing_postal_code': '75001',
                    'billing_city': data['billing_city'],
                    'billing_country': 'FR',
                    'payment_terms': '30j',
                    'currency': 'EUR',
                    'is_active': True,
                }
            )
            clients.append(client)
            status = '✨ Créé' if created else '✓ Existe'
            self.stdout.write(f'  {status} : {client.legal_name}')
        
        # 3. Créer des devis de test
        self.stdout.write(self.style.WARNING('\n📄 Création de devis de test...'))
        
        for i, client in enumerate(clients[:2]):
            quote, created = Quote.objects.get_or_create(
                organization=org,
                customer=client,
                defaults={
                    'currency': 'EUR',
                    'status': 'draft',
                    'valid_until': date.today() + timedelta(days=30),
                    'total_ht': Decimal('100.00'),
                    'total_tax': Decimal('20.00'),
                    'total_ttc': Decimal('120.00'),
                }
            )
            status = '✨ Créé' if created else '✓ Existe'
            self.stdout.write(f'  {status} : Devis pour {client.legal_name}')
        
        # 4. Créer des commandes de test
        self.stdout.write(self.style.WARNING('\n🛒 Création de commandes de test...'))
        
        for i, client in enumerate(clients[:2]):
            order, created = Order.objects.get_or_create(
                organization=org,
                customer=client,
                defaults={
                    'currency': 'EUR',
                    'status': 'draft',
                    'payment_status': 'unpaid',
                    'total_ht': Decimal('200.00'),
                    'total_tax': Decimal('40.00'),
                    'total_ttc': Decimal('240.00'),
                }
            )
            status = '✨ Créé' if created else '✓ Existe'
            self.stdout.write(f'  {status} : Commande pour {client.legal_name}')
        
        # 5. Créer des factures de test
        self.stdout.write(self.style.WARNING('\n🧾 Création de factures de test...'))
        
        from apps.billing.managers import BillingManager
        
        for i, client in enumerate(clients[:2]):
            # Vérifier si une facture existe déjà pour ce client
            existing = Invoice.objects.filter(organization=org, customer=client).first()
            if existing:
                self.stdout.write(f'  ✓ Existe : Facture {existing.number} pour {client.legal_name}')
            else:
                number = BillingManager.generate_invoice_number(org)
                invoice = Invoice.objects.create(
                    organization=org,
                    customer=client,
                    number=number,
                    date_issue=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    currency='EUR',
                    status='draft',
                    total_ht=Decimal('300.00'),
                    total_tax=Decimal('60.00'),
                    total_ttc=Decimal('360.00'),
                )
                self.stdout.write(f'  ✨ Créé : Facture {invoice.number} pour {client.legal_name}')
        
        # 6. Afficher les statistiques
        self.stdout.write(self.style.SUCCESS('\n📊 STATISTIQUES'))
        self.stdout.write(f'  Clients : {SalesCustomer.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Devis : {Quote.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Commandes : {Order.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Factures : {Invoice.objects.filter(organization=org).count()}')
        
        # 7. Afficher les URLs de test
        self.stdout.write(self.style.SUCCESS('\n🌐 URLS DE TEST'))
        self.stdout.write(self.style.WARNING('\n  📄 DEVIS'))
        self.stdout.write('    Liste : http://127.0.0.1:8000/ventes/devis/')
        self.stdout.write('    Nouveau : http://127.0.0.1:8000/ventes/devis/nouveau/')
        
        self.stdout.write(self.style.WARNING('\n  🛒 COMMANDES'))
        self.stdout.write('    Liste : http://127.0.0.1:8000/ventes/commandes/')
        self.stdout.write('    Nouveau : http://127.0.0.1:8000/ventes/commandes/nouveau/')
        
        self.stdout.write(self.style.WARNING('\n  🧾 FACTURES'))
        self.stdout.write('    Liste : http://127.0.0.1:8000/ventes/factures/')
        self.stdout.write('    Nouveau : http://127.0.0.1:8000/ventes/factures/nouveau/')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Données de test créées avec succès !'))
        self.stdout.write(self.style.SUCCESS('🚀 Démarrez le serveur : python manage.py runserver\n'))
