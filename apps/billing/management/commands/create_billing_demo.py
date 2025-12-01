"""
Commande Django pour créer des données de démonstration pour la facturation
DB Roadmap 04 - Facturation & Comptabilité
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization
from apps.sales.models import Customer, Order, OrderLine
from apps.billing.models import AccountMap, Invoice, InvoiceLine, Payment, CreditNote, Reconciliation, GLEntry
from apps.billing.managers import BillingManager, AccountingManager

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour le système de facturation'

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
        
        self.stdout.write(f'Création des données de facturation pour "{org_name}"')
        
        # 1. Organisation (réutiliser existante)
        try:
            org = Organization.objects.get(name=org_name)
            self.stdout.write(f'[OK] Organisation existante: {org.name}')
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'[ERREUR] Organisation "{org_name}" non trouvée. '
                'Exécutez d\'abord: python manage.py create_sales_demo'
            ))
            return
        
        # Utilisateur
        try:
            user = User.objects.get(email='demo@monchai.fr')
            self.stdout.write(f'[OK] Utilisateur existant: {user.email}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '[ERREUR] Utilisateur demo@monchai.fr non trouvé. '
                'Exécutez d\'abord: python manage.py create_sales_demo'
            ))
            return
        
        # 2. Plan comptable
        self.stdout.write('\n[COMPTABILITE] Création du plan comptable...')
        
        account_maps_data = [
            # Produits
            {'type': 'product', 'key': 'default', 'code': '707', 'name': 'Ventes de marchandises'},
            {'type': 'product', 'key': 'wine', 'code': '7071', 'name': 'Ventes de vins'},
            
            # Taxes
            {'type': 'tax', 'key': 'TVA20', 'code': '4457', 'name': 'TVA collectée 20%'},
            {'type': 'tax', 'key': 'TVA10', 'code': '44571', 'name': 'TVA collectée 10%'},
            {'type': 'tax', 'key': 'TVA0', 'code': '4456', 'name': 'TVA non applicable'},
            
            # Clients
            {'type': 'customer', 'key': 'default', 'code': '411', 'name': 'Clients'},
            {'type': 'customer', 'key': 'pro', 'code': '4111', 'name': 'Clients professionnels'},
            {'type': 'customer', 'key': 'part', 'code': '4112', 'name': 'Clients particuliers'},
            
            # Méthodes de paiement
            {'type': 'payment_method', 'key': 'sepa', 'code': '512', 'name': 'Banque'},
            {'type': 'payment_method', 'key': 'card', 'code': '5124', 'name': 'Carte bancaire'},
            {'type': 'payment_method', 'key': 'cheque', 'code': '5112', 'name': 'Chèques à encaisser'},
            {'type': 'payment_method', 'key': 'cash', 'code': '530', 'name': 'Caisse'},
            {'type': 'payment_method', 'key': 'transfer', 'code': '512', 'name': 'Virement'},
        ]
        
        for account_data in account_maps_data:
            account_map, created = AccountMap.objects.get_or_create(
                organization=org,
                mapping_type=account_data['type'],
                key=account_data['key'],
                defaults={
                    'account_code': account_data['code'],
                    'account_name': account_data['name']
                }
            )
            status = '[OK] Créé' if created else '[OK] Existant'
            self.stdout.write(f'  {status}: {account_map.account_code} - {account_map.account_name}')
        
        # 3. Facturation des commandes existantes
        self.stdout.write('\n[FACTURATION] Facturation des commandes...')
        
        # Trouver les commandes expédiées non facturées
        orders = Order.objects.filter(
            organization=org,
            status='fulfilled'
        ).exclude(
            invoices__isnull=False  # Pas déjà facturées
        )
        
        invoices_created = 0
        
        for order in orders:
            try:
                invoice = BillingManager.create_invoice_from_order(order, due_days=30)
                invoices_created += 1
                self.stdout.write(f'  [OK] Facture créée: {invoice.number} - {invoice.total_ttc}€')
                
                # Émettre quelques factures
                if invoices_created <= 2:
                    BillingManager.issue_invoice(invoice, user)
                    self.stdout.write(f'    [OK] Facture émise avec écritures comptables')
                
            except Exception as e:
                self.stdout.write(f'  [WARN] Erreur facturation commande {order.id}: {str(e)}')
        
        # 4. Créer des factures manuelles si pas de commandes
        if invoices_created == 0:
            self.stdout.write('  [INFO] Aucune commande à facturer, création factures manuelles...')
            
            # Trouver des clients
            customers = Customer.objects.filter(organization=org)[:2]
            
            for i, customer in enumerate(customers):
                try:
                    # Créer facture manuelle
                    invoice = Invoice.objects.create(
                        organization=org,
                        customer=customer,
                        number=BillingManager.generate_invoice_number(org),
                        date_issue=timezone.now().date(),
                        due_date=timezone.now().date() + timezone.timedelta(days=30),
                        total_ht=Decimal('100.00') * (i + 1),
                        total_tva=Decimal('20.00') * (i + 1),
                        total_ttc=Decimal('120.00') * (i + 1)
                    )
                    
                    # Émettre la facture
                    BillingManager.issue_invoice(invoice, user)
                    invoices_created += 1
                    
                    self.stdout.write(f'  [OK] Facture manuelle: {invoice.number} - {invoice.total_ttc}€')
                    
                except Exception as e:
                    self.stdout.write(f'  [WARN] Erreur facture manuelle: {str(e)}')
        
        # 5. Paiements et lettrage
        self.stdout.write('\n[PAIEMENTS] Création des paiements...')
        
        # Trouver les factures émises
        invoices = Invoice.objects.filter(
            organization=org,
            status='issued'
        )
        
        payments_created = 0
        
        for i, invoice in enumerate(invoices[:3]):  # Limiter à 3 factures
            try:
                # Créer paiement (partiel pour la première, complet pour les autres)
                if i == 0:
                    # Paiement partiel
                    amount = invoice.total_ttc * Decimal('0.6')  # 60%
                else:
                    # Paiement complet
                    amount = invoice.total_ttc
                
                payment_methods = ['sepa', 'card', 'cheque']
                method = payment_methods[i % len(payment_methods)]
                
                payment = Payment.objects.create(
                    organization=org,
                    customer=invoice.customer,
                    method=method,
                    amount=amount,
                    date_received=timezone.now().date(),
                    reference=f'PAY-{invoice.number}'
                )
                
                # Lettrer le paiement
                reconciliation = BillingManager.allocate_payment(payment, invoice)
                payments_created += 1
                
                status_text = "Partiel" if amount < invoice.total_ttc else "Complet"
                self.stdout.write(f'  [OK] Paiement {status_text}: {amount}€ ({method}) - {invoice.number}')
                
            except Exception as e:
                self.stdout.write(f'  [WARN] Erreur paiement facture {invoice.number}: {str(e)}')
        
        # 6. Avoir de démonstration
        self.stdout.write('\n[AVOIRS] Création des avoirs...')
        
        # Créer un avoir sur la première facture payée
        paid_invoice = Invoice.objects.filter(
            organization=org,
            status='paid'
        ).first()
        
        if paid_invoice:
            try:
                credit_note = BillingManager.create_credit_note(
                    paid_invoice,
                    "Produit défectueux - retour client",
                    amount_ht=paid_invoice.total_ht * Decimal('0.3')  # 30% d'avoir
                )
                
                self.stdout.write(f'  [OK] Avoir créé: {credit_note.number} - {credit_note.total_ttc}€')
                
            except Exception as e:
                self.stdout.write(f'  [WARN] Erreur création avoir: {str(e)}')
        else:
            self.stdout.write('  [INFO] Aucune facture payée pour créer un avoir')
        
        # 7. Export journal de démonstration
        self.stdout.write('\n[EXPORT] Test export journal...')
        
        try:
            date_from = timezone.now().date()
            date_to = timezone.now().date()
            
            # Export CSV du journal des ventes
            csv_data = AccountingManager.export_journal(
                org, 'VEN', date_from, date_to, 'csv'
            )
            
            lines_count = len(csv_data.split('\n')) - 1  # -1 pour l'en-tête
            self.stdout.write(f'  [OK] Export CSV journal VEN: {lines_count} écritures')
            
            # Export JSON du journal banque
            json_data = AccountingManager.export_journal(
                org, 'BAN', date_from, date_to, 'json'
            )
            
            import json
            entries = json.loads(json_data)
            self.stdout.write(f'  [OK] Export JSON journal BAN: {len(entries)} écritures')
            
        except Exception as e:
            self.stdout.write(f'  [WARN] Erreur export: {str(e)}')
        
        # 8. Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] DONNÉES DE FACTURATION CRÉÉES'))
        self.stdout.write('='*60)
        
        # Statistiques
        
        self.stdout.write(f'[STATS] Organisation: {org.name}')
        self.stdout.write(f'[STATS] Plan comptable: {AccountMap.objects.filter(organization=org).count()} comptes')
        self.stdout.write(f'[STATS] Factures: {Invoice.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Paiements: {Payment.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Réconciliations: {Reconciliation.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Avoirs: {CreditNote.objects.filter(organization=org).count()}')
        self.stdout.write(f'[STATS] Écritures comptables: {GLEntry.objects.filter(organization=org).count()}')
        
        # Totaux financiers
        total_invoiced = sum(
            invoice.total_ttc for invoice in Invoice.objects.filter(organization=org, status__in=['issued', 'paid'])
        )
        total_paid = sum(
            payment.amount for payment in Payment.objects.filter(organization=org)
        )
        
        self.stdout.write(f'[STATS] Total facturé: {total_invoiced}€')
        self.stdout.write(f'[STATS] Total encaissé: {total_paid}€')
        
        self.stdout.write('\n[INFO] Utilisez l\'admin Django pour explorer les données créées')
        self.stdout.write('[INFO] Testez les exports comptables et le lettrage')
        self.stdout.write('[INFO] Connexion: demo@monchai.fr / demo123')
