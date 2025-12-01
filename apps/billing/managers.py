"""
Gestionnaires métier pour la facturation et comptabilité
DB Roadmap 04 - Facturation & Comptabilité
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict

from apps.sales.models import Order


class BillingManager:
    """
    Gestionnaire pour les opérations de facturation
    Création factures, avoirs, lettrage
    """
    
    @staticmethod
    def generate_invoice_number(organization, date_issue=None):
        """
        Génère un numéro de facture séquentiel français
        Format: YYYY-NNNN (ex: 2025-0001)
        """
        from .models import Invoice
        
        if date_issue is None:
            date_issue = timezone.now().date()
        
        year = date_issue.year
        
        # Trouver le dernier numéro de l'année
        last_invoice = Invoice.objects.filter(
            organization=organization,
            number__startswith=f"{year}-"
        ).order_by('-number').first()
        
        if last_invoice:
            # Extraire le numéro séquentiel
            try:
                last_seq = int(last_invoice.number.split('-')[1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{year}-{next_seq:04d}"
    
    @staticmethod
    def generate_credit_note_number(organization, date_issue=None):
        """
        Génère un numéro d'avoir séquentiel français
        Format: AV-YYYY-NNNN (ex: AV-2025-0001)
        """
        from .models import CreditNote
        
        if date_issue is None:
            date_issue = timezone.now().date()
        
        year = date_issue.year
        
        # Trouver le dernier numéro de l'année
        last_credit_note = CreditNote.objects.filter(
            organization=organization,
            number__startswith=f"AV-{year}-"
        ).order_by('-number').first()
        
        if last_credit_note:
            try:
                last_seq = int(last_credit_note.number.split('-')[2])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"AV-{year}-{next_seq:04d}"
    
    @staticmethod
    @transaction.atomic
    def create_invoice_from_order(order, due_days=30):
        """
        Crée une facture à partir d'une commande
        
        Args:
            order: Instance Order
            due_days: Nombre de jours pour l'échéance
        
        Returns:
            Invoice: Instance de la facture créée
        """
        from .models import Invoice, InvoiceLine
        
        if order.status != 'fulfilled':
            raise ValidationError("Seules les commandes expédiées peuvent être facturées")
        
        # Vérifier qu'il n'y a pas déjà une facture
        if order.invoices.exists():
            raise ValidationError("Cette commande a déjà été facturée")
        
        # Créer la facture
        date_issue = timezone.now().date()
        due_date = date_issue + timezone.timedelta(days=due_days)
        
        invoice = Invoice.objects.create(
            organization=order.organization,
            customer=order.customer,
            order=order,
            number=BillingManager.generate_invoice_number(order.organization, date_issue),
            date_issue=date_issue,
            due_date=due_date,
            currency=order.currency
        )
        
        # Copier les lignes de commande
        for order_line in order.lines.all():
            InvoiceLine.objects.create(
                organization=order.organization,
                invoice=invoice,
                sku=order_line.sku,
                description=order_line.description,
                qty=order_line.qty,
                unit_price=order_line.unit_price,
                discount_pct=order_line.discount_pct,
                tax_code=order_line.tax_code
            )
        
        # Recalculer les totaux
        invoice.calculate_totals()
        invoice.save()
        
        return invoice
    
    @staticmethod
    @transaction.atomic
    def issue_invoice(invoice, user):
        """
        Émet une facture (passage de draft à issued)
        Génère les écritures comptables
        
        Args:
            invoice: Instance Invoice
            user: Utilisateur émettant la facture
        
        Returns:
            List[GLEntry]: Écritures comptables créées
        """
        if invoice.status != 'draft':
            raise ValidationError("Seules les factures en brouillon peuvent être émises")
        
        # Marquer comme émise
        invoice.status = 'issued'
        invoice.save()
        
        # Générer les écritures comptables
        gl_entries = AccountingManager.create_invoice_entries(invoice)
        
        return gl_entries
    
    @staticmethod
    @transaction.atomic
    def create_credit_note(invoice, reason, amount_ht=None):
        """
        Crée un avoir pour une facture
        
        Args:
            invoice: Instance Invoice
            reason: Motif de l'avoir
            amount_ht: Montant HT (None = avoir total)
        
        Returns:
            CreditNote: Instance de l'avoir créé
        """
        from .models import CreditNote
        
        if invoice.status not in ['issued', 'paid']:
            raise ValidationError("Seules les factures émises peuvent faire l'objet d'un avoir")
        
        # Montant par défaut = total facture
        if amount_ht is None:
            amount_ht = invoice.total_ht
        
        if amount_ht > invoice.total_ht:
            raise ValidationError("Le montant de l'avoir ne peut pas dépasser le montant de la facture")
        
        # Calculer les montants proportionnels avec arrondi
        from decimal import ROUND_HALF_UP
        
        ratio = amount_ht / invoice.total_ht if invoice.total_ht > 0 else Decimal('0')
        amount_tva = (invoice.total_tva * ratio).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        amount_ttc = (invoice.total_ttc * ratio).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        # Créer l'avoir (montants négatifs)
        credit_note = CreditNote.objects.create(
            organization=invoice.organization,
            invoice=invoice,
            number=BillingManager.generate_credit_note_number(invoice.organization),
            reason=reason,
            total_ht=-amount_ht,
            total_tva=-amount_tva,
            total_ttc=-amount_ttc
        )
        
        # Générer les écritures comptables
        AccountingManager.create_credit_note_entries(credit_note)
        
        return credit_note
    
    @staticmethod
    @transaction.atomic
    def allocate_payment(payment, invoice, amount=None):
        """
        Alloue un paiement à une facture (lettrage)
        
        Args:
            payment: Instance Payment
            invoice: Instance Invoice
            amount: Montant à allouer (None = maximum possible)
        
        Returns:
            Reconciliation: Instance de réconciliation créée
        """
        from .models import Reconciliation
        
        # Montant maximum allouable
        max_payment = payment.amount_unallocated
        max_invoice = invoice.amount_due
        max_amount = min(max_payment, max_invoice)
        
        if amount is None:
            amount = max_amount
        
        if amount > max_amount:
            raise ValidationError(f"Montant maximum allouable: {max_amount}€")
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif")
        
        # Créer la réconciliation
        reconciliation = Reconciliation.objects.create(
            organization=payment.organization,
            payment=payment,
            invoice=invoice,
            amount_allocated=amount
        )
        
        # Vérifier si la facture est entièrement payée
        if invoice.amount_due <= Decimal('0.01'):  # Tolérance d'arrondi
            invoice.status = 'paid'
            invoice.save()
        
        # Générer l'écriture de paiement
        AccountingManager.create_payment_entries(payment, reconciliation)
        
        return reconciliation


class AccountingManager:
    """
    Gestionnaire pour les opérations comptables
    Génération d'écritures, exports
    """
    
    # Plan comptable français standard
    ACCOUNT_CODES = {
        'sales': '707',           # Ventes de marchandises
        'vat_collected': '4457',  # TVA collectée
        'customer': '411',        # Clients
        'bank': '512',           # Banque
        'cash': '530',           # Caisse
    }
    
    @staticmethod
    def get_account_code(organization, mapping_type, key):
        """
        Résout un code compte via AccountMap ou défaut
        """
        from .models import AccountMap
        
        try:
            account_map = AccountMap.objects.get(
                organization=organization,
                mapping_type=mapping_type,
                key=key
            )
            return account_map.account_code
        except AccountMap.DoesNotExist:
            # Codes par défaut
            if mapping_type == 'tax':
                return AccountingManager.ACCOUNT_CODES['vat_collected']
            elif mapping_type == 'product':
                return AccountingManager.ACCOUNT_CODES['sales']
            elif mapping_type == 'customer':
                return AccountingManager.ACCOUNT_CODES['customer']
            elif mapping_type == 'payment_method':
                if key in ['sepa', 'transfer', 'card']:
                    return AccountingManager.ACCOUNT_CODES['bank']
                else:
                    return AccountingManager.ACCOUNT_CODES['cash']
            
            return '999999'  # Compte d'attente
    
    @staticmethod
    @transaction.atomic
    def create_invoice_entries(invoice):
        """
        Crée les écritures comptables pour une facture émise
        
        Schéma:
        - Débit 411 (Client) = Total TTC
        - Crédit 707 (Ventes) = Total HT
        - Crédit 4457 (TVA) = Total TVA
        """
        from .models import GLEntry
        
        entries = []
        
        # Débit client (Total TTC)
        customer_account = AccountingManager.get_account_code(
            invoice.organization, 'customer', str(invoice.customer.id)
        )
        
        entry_customer = GLEntry.objects.create(
            organization=invoice.organization,
            journal='VEN',
            date=invoice.date_issue,
            doc_type='invoice',
            doc_id=invoice.id,
            doc_number=invoice.number,
            account_code=customer_account,
            debit=invoice.total_ttc,
            credit=Decimal('0'),
            label=f"Facture {invoice.number} - {invoice.customer.legal_name}"
        )
        entries.append(entry_customer)
        
        # Agrégation par code TVA
        tax_totals = {}
        sales_total = Decimal('0')
        
        for line in invoice.lines.all():
            # Ventes
            sales_total += line.total_ht
            
            # TVA par code
            tax_code = line.tax_code.code
            if tax_code not in tax_totals:
                tax_totals[tax_code] = {
                    'rate': line.tax_code.rate_pct,
                    'amount': Decimal('0')
                }
            tax_totals[tax_code]['amount'] += line.total_tva
        
        # Crédit ventes (Total HT)
        sales_account = AccountingManager.get_account_code(
            invoice.organization, 'product', 'default'
        )
        
        entry_sales = GLEntry.objects.create(
            organization=invoice.organization,
            journal='VEN',
            date=invoice.date_issue,
            doc_type='invoice',
            doc_id=invoice.id,
            doc_number=invoice.number,
            account_code=sales_account,
            debit=Decimal('0'),
            credit=sales_total,
            label=f"Ventes facture {invoice.number}"
        )
        entries.append(entry_sales)
        
        # Crédit TVA par code
        for tax_code, tax_data in tax_totals.items():
            if tax_data['amount'] > 0:
                vat_account = AccountingManager.get_account_code(
                    invoice.organization, 'tax', tax_code
                )
                
                entry_vat = GLEntry.objects.create(
                    organization=invoice.organization,
                    journal='VEN',
                    date=invoice.date_issue,
                    doc_type='invoice',
                    doc_id=invoice.id,
                    doc_number=invoice.number,
                    account_code=vat_account,
                    debit=Decimal('0'),
                    credit=tax_data['amount'],
                    label=f"TVA {tax_code} facture {invoice.number}"
                )
                entries.append(entry_vat)
        
        return entries
    
    @staticmethod
    @transaction.atomic
    def create_credit_note_entries(credit_note):
        """
        Crée les écritures comptables pour un avoir
        Écritures inverses de la facture
        """
        from .models import GLEntry
        
        entries = []
        invoice = credit_note.invoice
        
        # Crédit client (montant négatif = débit négatif)
        customer_account = AccountingManager.get_account_code(
            invoice.organization, 'customer', str(invoice.customer.id)
        )
        
        entry_customer = GLEntry.objects.create(
            organization=credit_note.organization,
            journal='VEN',
            date=credit_note.date_issue,
            doc_type='credit_note',
            doc_id=credit_note.id,
            doc_number=credit_note.number,
            account_code=customer_account,
            debit=Decimal('0'),
            credit=-credit_note.total_ttc,  # Montant positif car total_ttc est négatif
            label=f"Avoir {credit_note.number} - {invoice.customer.legal_name}"
        )
        entries.append(entry_customer)
        
        # Débit ventes
        sales_account = AccountingManager.get_account_code(
            invoice.organization, 'product', 'default'
        )
        
        entry_sales = GLEntry.objects.create(
            organization=credit_note.organization,
            journal='VEN',
            date=credit_note.date_issue,
            doc_type='credit_note',
            doc_id=credit_note.id,
            doc_number=credit_note.number,
            account_code=sales_account,
            debit=-credit_note.total_ht,  # Montant positif
            credit=Decimal('0'),
            label=f"Annulation ventes avoir {credit_note.number}"
        )
        entries.append(entry_sales)
        
        # Débit TVA si applicable
        if credit_note.total_tva != 0:
            vat_account = AccountingManager.get_account_code(
                invoice.organization, 'tax', 'TVA20'  # Simplification
            )
            
            entry_vat = GLEntry.objects.create(
                organization=credit_note.organization,
                journal='VEN',
                date=credit_note.date_issue,
                doc_type='credit_note',
                doc_id=credit_note.id,
                doc_number=credit_note.number,
                account_code=vat_account,
                debit=-credit_note.total_tva,  # Montant positif
                credit=Decimal('0'),
                label=f"Annulation TVA avoir {credit_note.number}"
            )
            entries.append(entry_vat)
        
        return entries
    
    @staticmethod
    @transaction.atomic
    def create_payment_entries(payment, reconciliation):
        """
        Crée les écritures comptables pour un paiement
        
        Schéma:
        - Débit 512/530 (Banque/Caisse) = Montant
        - Crédit 411 (Client) = Montant
        """
        from .models import GLEntry
        
        entries = []
        
        # Débit banque/caisse
        payment_account = AccountingManager.get_account_code(
            payment.organization, 'payment_method', payment.method
        )
        
        entry_payment = GLEntry.objects.create(
            organization=payment.organization,
            journal='BAN',
            date=payment.date_received,
            doc_type='payment',
            doc_id=payment.id,
            doc_number=payment.reference or f"PAY-{payment.id.hex[:8]}",
            account_code=payment_account,
            debit=reconciliation.amount_allocated,
            credit=Decimal('0'),
            label=f"Paiement {payment.get_method_display()} - {payment.customer.legal_name}"
        )
        entries.append(entry_payment)
        
        # Crédit client
        customer_account = AccountingManager.get_account_code(
            payment.organization, 'customer', str(payment.customer.id)
        )
        
        entry_customer = GLEntry.objects.create(
            organization=payment.organization,
            journal='BAN',
            date=payment.date_received,
            doc_type='payment',
            doc_id=payment.id,
            doc_number=payment.reference or f"PAY-{payment.id.hex[:8]}",
            account_code=customer_account,
            debit=Decimal('0'),
            credit=reconciliation.amount_allocated,
            label=f"Règlement facture {reconciliation.invoice.number}"
        )
        entries.append(entry_customer)
        
        return entries
    
    @staticmethod
    def export_journal(organization, journal_code, date_from, date_to, format='csv'):
        """
        Exporte un journal comptable
        
        Args:
            organization: Organisation
            journal_code: Code journal (VEN, BAN, OD)
            date_from: Date de début
            date_to: Date de fin
            format: Format d'export ('csv', 'json')
        
        Returns:
            str: Données exportées
        """
        from .models import GLEntry
        import csv
        import json
        from io import StringIO
        
        entries = GLEntry.objects.filter(
            organization=organization,
            journal=journal_code,
            date__range=[date_from, date_to]
        ).order_by('date', 'doc_number')
        
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output, delimiter=';')
            
            # En-têtes
            writer.writerow([
                'Date', 'Journal', 'Pièce', 'Compte', 'Libellé', 'Débit', 'Crédit'
            ])
            
            # Données
            for entry in entries:
                writer.writerow([
                    entry.date.strftime('%d/%m/%Y'),
                    entry.journal,
                    entry.doc_number,
                    entry.account_code,
                    entry.label,
                    str(entry.debit).replace('.', ',') if entry.debit > 0 else '',
                    str(entry.credit).replace('.', ',') if entry.credit > 0 else ''
                ])
            
            return output.getvalue()
        
        elif format == 'json':
            data = []
            for entry in entries:
                data.append({
                    'date': entry.date.isoformat(),
                    'journal': entry.journal,
                    'doc_number': entry.doc_number,
                    'account_code': entry.account_code,
                    'label': entry.label,
                    'debit': str(entry.debit),
                    'credit': str(entry.credit)
                })
            
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        else:
            raise ValueError("Format non supporté")
