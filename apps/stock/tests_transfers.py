"""
Tests pour les transferts de stock - Roadmap 32
Tests d'acceptation et de robustesse selon la roadmap
"""

import uuid
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.accounts.models import Organization, Membership
from apps.viticulture.models import Lot, Warehouse, Cuvee, Appellation, Vintage, UnitOfMeasure
from .models import StockTransfer, StockVracBalance, StockVracMove
from .services import StockService

User = get_user_model()


class StockTransferTestCase(TestCase):
    """Tests du modèle StockTransfer et du service"""
    
    def setUp(self):
        # Organisation et utilisateur
        self.organization = Organization.objects.create(
            name="Test Domaine",
            siret="12345678901234"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role='editor'
        )
        
        # Données de base
        self.appellation = Appellation.objects.create(
            organization=self.organization,
            name="Test AOC",
            type="aoc"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.organization,
            year=2023
        )
        
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        self.warehouse_a = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt A"
        )
        
        self.warehouse_b = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt B"
        )
        
        self.cuvee = Cuvee.objects.create(
            organization=self.organization,
            name="Test Cuvée",
            appellation=self.appellation,
            vintage=self.vintage,
            default_uom=self.uom
        )
        
        self.lot = Lot.objects.create(
            organization=self.organization,
            code="LOT001",
            cuvee=self.cuvee,
            warehouse=self.warehouse_a,
            volume_l=Decimal('1000.00'),
            alcohol_pct=Decimal('13.5')
        )
        
        # Stock initial dans warehouse_a
        self.balance_a = StockVracBalance.objects.create(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a,
            qty_l=Decimal('500.00')
        )
    
    def test_transfer_creation_success(self):
        """AC-32-01: Transfert 50 L → moves out source & in dest ; balances mises à jour"""
        volume_l = Decimal('50.00')
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        # Création du transfert
        transfer, created = StockTransfer.create_transfer(
            organization=self.organization,
            lot=self.lot,
            from_warehouse=self.warehouse_a,
            to_warehouse=self.warehouse_b,
            volume_l=volume_l,
            user=self.user,
            client_token=client_token
        )
        
        self.assertTrue(created)
        self.assertEqual(transfer.volume_l, volume_l)
        self.assertEqual(transfer.lot, self.lot)
        self.assertEqual(transfer.from_warehouse, self.warehouse_a)
        self.assertEqual(transfer.to_warehouse, self.warehouse_b)
        
        # Vérifier les mouvements créés
        moves = StockVracMove.objects.filter(
            organization=self.organization,
            lot=self.lot,
            move_type='transfert',
            ref_type='transfer',
            ref_id=transfer.id
        ).order_by('created_at')
        
        self.assertEqual(moves.count(), 2)
        
        # Mouvement de sortie
        out_move = moves[0]
        self.assertEqual(out_move.src_warehouse, self.warehouse_a)
        self.assertIsNone(out_move.dst_warehouse)
        self.assertEqual(out_move.qty_l, volume_l)
        
        # Mouvement d'entrée
        in_move = moves[1]
        self.assertIsNone(in_move.src_warehouse)
        self.assertEqual(in_move.dst_warehouse, self.warehouse_b)
        self.assertEqual(in_move.qty_l, volume_l)
        
        # Vérifier les balances
        balance_a = StockVracBalance.objects.get(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a
        )
        self.assertEqual(balance_a.qty_l, Decimal('450.00'))  # 500 - 50
        
        balance_b = StockVracBalance.objects.get(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_b
        )
        self.assertEqual(balance_b.qty_l, Decimal('50.00'))
    
    def test_insufficient_stock_error(self):
        """AC-32-02: Volume > solde source → 422 ; rien écrit"""
        volume_l = Decimal('600.00')  # Plus que les 500L disponibles
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        with self.assertRaises(ValidationError) as cm:
            StockTransfer.create_transfer(
                organization=self.organization,
                lot=self.lot,
                from_warehouse=self.warehouse_a,
                to_warehouse=self.warehouse_b,
                volume_l=volume_l,
                user=self.user,
                client_token=client_token
            )
        
        self.assertIn("Solde insuffisant", str(cm.exception))
        
        # Vérifier qu'aucun transfert n'a été créé
        self.assertEqual(StockTransfer.objects.count(), 0)
        
        # Vérifier qu'aucun mouvement n'a été créé
        self.assertEqual(StockVracMove.objects.count(), 0)
        
        # Vérifier que la balance n'a pas changé
        balance_a = StockVracBalance.objects.get(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a
        )
        self.assertEqual(balance_a.qty_l, Decimal('500.00'))
    
    def test_idempotence_same_token(self):
        """AC-32-03: Double submit (même token) → un seul transfert appliqué"""
        volume_l = Decimal('50.00')
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        # Premier appel
        transfer1, created1 = StockTransfer.create_transfer(
            organization=self.organization,
            lot=self.lot,
            from_warehouse=self.warehouse_a,
            to_warehouse=self.warehouse_b,
            volume_l=volume_l,
            user=self.user,
            client_token=client_token
        )
        
        self.assertTrue(created1)
        
        # Deuxième appel avec le même token
        transfer2, created2 = StockTransfer.create_transfer(
            organization=self.organization,
            lot=self.lot,
            from_warehouse=self.warehouse_a,
            to_warehouse=self.warehouse_b,
            volume_l=volume_l,
            user=self.user,
            client_token=client_token
        )
        
        self.assertFalse(created2)
        self.assertEqual(transfer1.id, transfer2.id)
        
        # Vérifier qu'un seul transfert existe
        self.assertEqual(StockTransfer.objects.count(), 1)
        
        # Vérifier que seulement 2 mouvements existent (pas 4)
        self.assertEqual(StockVracMove.objects.count(), 2)
        
        # Vérifier la balance finale
        balance_a = StockVracBalance.objects.get(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a
        )
        self.assertEqual(balance_a.qty_l, Decimal('450.00'))  # Seulement une déduction
    
    def test_validation_same_warehouse(self):
        """Test validation: entrepôts source et destination différents"""
        volume_l = Decimal('50.00')
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        with self.assertRaises(ValidationError) as cm:
            StockTransfer.create_transfer(
                organization=self.organization,
                lot=self.lot,
                from_warehouse=self.warehouse_a,
                to_warehouse=self.warehouse_a,  # Même entrepôt
                volume_l=volume_l,
                user=self.user,
                client_token=client_token
            )
        
        self.assertIn("différents", str(cm.exception))
    
    def test_validation_negative_volume(self):
        """Test validation: volume positif"""
        volume_l = Decimal('-10.00')
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        with self.assertRaises(ValidationError) as cm:
            StockTransfer.create_transfer(
                organization=self.organization,
                lot=self.lot,
                from_warehouse=self.warehouse_a,
                to_warehouse=self.warehouse_b,
                volume_l=volume_l,
                user=self.user,
                client_token=client_token
            )
        
        self.assertIn("positif", str(cm.exception))
    
    def test_cross_organization_isolation(self):
        """Test isolation multi-tenant"""
        # Autre organisation
        other_org = Organization.objects.create(
            name="Other Domaine",
            siret="98765432109876"
        )
        
        volume_l = Decimal('50.00')
        client_token = f"test_{uuid.uuid4().hex[:8]}"
        
        # Validation avec lot d'une autre organisation
        validation_errors = StockService.validate_transfer_request(
            other_org, self.lot, self.warehouse_a, self.warehouse_b, volume_l
        )
        
        self.assertIn("n'appartient pas à cette organisation", validation_errors[0])


class StockTransferViewsTestCase(TestCase):
    """Tests des vues de transfert"""
    
    def setUp(self):
        # Organisation et utilisateur
        self.organization = Organization.objects.create(
            name="Test Domaine",
            siret="12345678901234"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role='editor'
        )
        
        # Données de base (similaire au test précédent)
        self.appellation = Appellation.objects.create(
            organization=self.organization,
            name="Test AOC",
            type="aoc"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.organization,
            year=2023
        )
        
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        self.warehouse_a = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt A"
        )
        
        self.warehouse_b = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt B"
        )
        
        self.cuvee = Cuvee.objects.create(
            organization=self.organization,
            name="Test Cuvée",
            appellation=self.appellation,
            vintage=self.vintage,
            default_uom=self.uom
        )
        
        self.lot = Lot.objects.create(
            organization=self.organization,
            code="LOT001",
            cuvee=self.cuvee,
            warehouse=self.warehouse_a,
            volume_l=Decimal('1000.00'),
            alcohol_pct=Decimal('13.5')
        )
        
        # Stock initial
        self.balance_a = StockVracBalance.objects.create(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a,
            qty_l=Decimal('500.00')
        )
        
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_view(self):
        """Test vue dashboard stocks"""
        response = self.client.get(reverse('stock:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Stocks')
    
    def test_transferts_list_view(self):
        """Test vue liste des transferts"""
        response = self.client.get(reverse('stock:transferts_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transferts entre entrepôts')
    
    def test_transfert_create_get(self):
        """Test affichage formulaire de création"""
        response = self.client.get(reverse('stock:transfert_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouveau transfert')
        self.assertContains(response, self.lot.code)
        self.assertContains(response, self.warehouse_a.name)
    
    def test_transfert_create_post_success(self):
        """Test création transfert via formulaire"""
        data = {
            'lot': str(self.lot.id),
            'from_warehouse': str(self.warehouse_a.id),
            'to_warehouse': str(self.warehouse_b.id),
            'volume_l': '50.00',
            'notes': 'Test transfert'
        }
        
        response = self.client.post(reverse('stock:transfert_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect après succès
        
        # Vérifier le transfert créé
        self.assertEqual(StockTransfer.objects.count(), 1)
        transfer = StockTransfer.objects.first()
        self.assertEqual(transfer.volume_l, Decimal('50.00'))
        self.assertEqual(transfer.notes, 'Test transfert')
    
    def test_transfert_create_post_validation_error(self):
        """Test gestion erreurs de validation"""
        data = {
            'lot': str(self.lot.id),
            'from_warehouse': str(self.warehouse_a.id),
            'to_warehouse': str(self.warehouse_a.id),  # Même entrepôt
            'volume_l': '50.00'
        }
        
        response = self.client.post(reverse('stock:transfert_create'), data)
        self.assertEqual(response.status_code, 200)  # Reste sur la page avec erreurs
        
        # Vérifier qu'aucun transfert n'a été créé
        self.assertEqual(StockTransfer.objects.count(), 0)
        
        # Vérifier les messages d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('différents' in str(m) for m in messages))


class StockServiceTestCase(TestCase):
    """Tests du service StockService"""
    
    def setUp(self):
        # Configuration similaire aux autres tests
        self.organization = Organization.objects.create(
            name="Test Domaine",
            siret="11111111111111"
        )
        
        self.appellation = Appellation.objects.create(
            organization=self.organization,
            name="Test AOC",
            type="aoc"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.organization,
            year=2023
        )
        
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        self.warehouse_a = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt A"
        )
        
        self.warehouse_b = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt B"
        )
        
        self.cuvee = Cuvee.objects.create(
            organization=self.organization,
            name="Test Cuvée",
            appellation=self.appellation,
            vintage=self.vintage,
            default_uom=self.uom
        )
        
        self.lot = Lot.objects.create(
            organization=self.organization,
            code="LOT001",
            cuvee=self.cuvee,
            warehouse=self.warehouse_a,
            volume_l=Decimal('1000.00'),
            alcohol_pct=Decimal('13.5')
        )
        
        # Stocks dans les deux entrepôts
        StockVracBalance.objects.create(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_a,
            qty_l=Decimal('300.00')
        )
        
        StockVracBalance.objects.create(
            organization=self.organization,
            lot=self.lot,
            warehouse=self.warehouse_b,
            qty_l=Decimal('200.00')
        )
    
    def test_get_lot_balance(self):
        """Test récupération solde d'un lot dans un entrepôt"""
        balance = StockService.get_lot_balance(
            self.organization, self.lot, self.warehouse_a
        )
        self.assertEqual(balance, Decimal('300.00'))
        
        # Entrepôt sans stock
        warehouse_c = Warehouse.objects.create(
            organization=self.organization,
            name="Entrepôt C"
        )
        balance_empty = StockService.get_lot_balance(
            self.organization, self.lot, warehouse_c
        )
        self.assertEqual(balance_empty, Decimal('0.00'))
    
    def test_get_lot_balances_by_warehouse(self):
        """Test récupération de tous les soldes d'un lot"""
        balances = StockService.get_lot_balances_by_warehouse(
            self.organization, self.lot
        )
        
        self.assertEqual(len(balances), 2)
        self.assertEqual(balances[self.warehouse_a], Decimal('300.00'))
        self.assertEqual(balances[self.warehouse_b], Decimal('200.00'))
    
    def test_get_organization_stock_summary(self):
        """Test résumé global des stocks"""
        summary = StockService.get_organization_stock_summary(self.organization)
        
        self.assertEqual(summary['total_volume_l'], Decimal('500.00'))
        self.assertEqual(len(summary['warehouse_summaries']), 2)
        
        # Vérifier les résumés par entrepôt
        warehouse_summaries = {
            ws['warehouse']: ws for ws in summary['warehouse_summaries']
        }
        
        self.assertEqual(
            warehouse_summaries[self.warehouse_a]['total_volume_l'], 
            Decimal('300.00')
        )
        self.assertEqual(
            warehouse_summaries[self.warehouse_b]['total_volume_l'], 
            Decimal('200.00')
        )
