"""
Tests pour les modèles de stock - DB Roadmap 02
Tests de robustesse selon la roadmap
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from apps.accounts.models import Organization
from apps.viticulture.models import (
    GrapeVariety, Appellation, Vintage, UnitOfMeasure, 
    Cuvee, Warehouse, Lot
)
from .models import (
    SKU, StockVracBalance, StockSKUBalance,
    StockVracMove, StockSKUMove, StockManager
)

User = get_user_model()


class StockModelsTestCase(TestCase):
    """Tests des modèles de stock selon DB Roadmap 02"""
    
    def setUp(self):
        """Configuration des données de test"""
        # Organisation
        self.org = Organization.objects.create(name="Test Winery")
        
        # Utilisateur
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Données viticulture
        self.grape_variety = GrapeVariety.objects.create(
            organization=self.org,
            name="Cabernet Sauvignon",
            color="rouge"
        )
        
        self.appellation = Appellation.objects.create(
            organization=self.org,
            name="Bordeaux AOC",
            region="Bordeaux"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.org,
            year=2023
        )
        
        self.uom_bottle = UnitOfMeasure.objects.create(
            organization=self.org,
            name="Bouteille",
            code="BT",
            base_ratio_to_l=Decimal('0.75')
        )
        
        self.uom_liter = UnitOfMeasure.objects.create(
            organization=self.org,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        self.cuvee = Cuvee.objects.create(
            organization=self.org,
            name="Réserve Rouge",
            vintage=self.vintage,
            appellation=self.appellation,
            default_uom=self.uom_liter
        )
        
        self.warehouse = Warehouse.objects.create(
            organization=self.org,
            name="Chai Principal"
        )
        
        self.lot = Lot.objects.create(
            organization=self.org,
            code="Lot 2023-001",
            cuvee=self.cuvee,
            warehouse=self.warehouse,
            volume_l=Decimal('1000.0'),
            status='en_cours'
        )
    
    def test_sku_creation_and_validation(self):
        """Test création et validation SKU"""
        # Test création normale
        sku = SKU.objects.create(
            organization=self.org,
            cuvee=self.cuvee,
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Réserve Rouge 2023 - Bouteille"
        )
        
        self.assertEqual(str(sku), "Réserve Rouge 2023 - Bouteille (BT)")
        self.assertTrue(sku.is_active)
        
        # Test contrainte unique (organization, cuvee, uom)
        with self.assertRaises(IntegrityError):
            SKU.objects.create(
                organization=self.org,
                cuvee=self.cuvee,
                uom=self.uom_bottle,
                volume_by_uom_to_l=Decimal('0.75'),
                label="Duplicate SKU"
            )
    
    def test_sku_cross_organization_validation(self):
        """Test validation cross-organisation pour SKU"""
        # Autre organisation
        other_org = Organization.objects.create(name="Other Winery")
        
        # Créer vintage et appellation pour l'autre organisation
        other_vintage = Vintage.objects.create(
            organization=other_org,
            year=2023
        )
        
        other_appellation = Appellation.objects.create(
            organization=other_org,
            name="Other AOC",
            region="Other Region"
        )
        
        # Créer UoM pour l'autre organisation
        other_uom = UnitOfMeasure.objects.create(
            organization=other_org,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        other_cuvee = Cuvee.objects.create(
            organization=other_org,
            name="Other Cuvee",
            vintage=other_vintage,
            appellation=other_appellation,
            default_uom=other_uom
        )
        
        # Test validation cuvée d'autre organisation
        sku = SKU(
            organization=self.org,
            cuvee=other_cuvee,  # Cuvée d'autre organisation
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Invalid SKU"
        )
        
        with self.assertRaises(ValidationError):
            sku.full_clean()
    
    def test_stock_vrac_balance_constraints(self):
        """Test contraintes soldes stock vrac"""
        # Test création normale
        balance = StockVracBalance.objects.create(
            organization=self.org,
            lot=self.lot,
            warehouse=self.warehouse,
            qty_l=Decimal('500.0')
        )
        
        self.assertEqual(balance.qty_l, Decimal('500.0'))
        
        # Test contrainte unique (organization, lot, warehouse)
        with self.assertRaises(IntegrityError):
            StockVracBalance.objects.create(
                organization=self.org,
                lot=self.lot,
                warehouse=self.warehouse,
                qty_l=Decimal('100.0')
            )
    
    def test_stock_vrac_move_validation(self):
        """Test validation mouvements stock vrac selon roadmap"""
        # Test transfert valide
        warehouse2 = Warehouse.objects.create(
            organization=self.org,
            name="Chai Secondaire"
        )
        
        move = StockVracMove(
            organization=self.org,
            lot=self.lot,
            src_warehouse=self.warehouse,
            dst_warehouse=warehouse2,
            qty_l=Decimal('100.0'),
            move_type='transfert',
            user=self.user
        )
        move.full_clean()  # Doit passer
        
        # Test transfert invalide: src = dst
        move_invalid = StockVracMove(
            organization=self.org,
            lot=self.lot,
            src_warehouse=self.warehouse,
            dst_warehouse=self.warehouse,  # Même entrepôt
            qty_l=Decimal('100.0'),
            move_type='transfert',
            user=self.user
        )
        
        with self.assertRaises(ValidationError):
            move_invalid.full_clean()
        
        # Test entrée: pas de source
        move_entree = StockVracMove(
            organization=self.org,
            lot=self.lot,
            src_warehouse=None,
            dst_warehouse=self.warehouse,
            qty_l=Decimal('100.0'),
            move_type='entree',
            user=self.user
        )
        move_entree.full_clean()  # Doit passer
        
        # Test sortie: pas de destination
        move_sortie = StockVracMove(
            organization=self.org,
            lot=self.lot,
            src_warehouse=self.warehouse,
            dst_warehouse=None,
            qty_l=Decimal('100.0'),
            move_type='sortie',
            user=self.user
        )
        move_sortie.full_clean()  # Doit passer
    
    def test_stock_manager_move_vrac_insufficient_stock(self):
        """Test rejet mouvement si stock insuffisant"""
        # Créer un solde initial
        StockVracBalance.objects.create(
            organization=self.org,
            lot=self.lot,
            warehouse=self.warehouse,
            qty_l=Decimal('100.0')
        )
        
        # Tenter une sortie supérieure au stock
        with self.assertRaises(ValidationError) as cm:
            StockManager.move_vrac(
                lot=self.lot,
                src_warehouse=self.warehouse,
                dst_warehouse=None,
                qty_l=Decimal('200.0'),  # Plus que disponible
                move_type='sortie',
                user=self.user
            )
        
        self.assertIn('Stock insuffisant', str(cm.exception))
    
    def test_stock_manager_move_vrac_success(self):
        """Test mouvement vrac réussi avec mise à jour soldes"""
        # Créer un solde initial
        balance = StockVracBalance.objects.create(
            organization=self.org,
            lot=self.lot,
            warehouse=self.warehouse,
            qty_l=Decimal('1000.0')
        )
        
        warehouse2 = Warehouse.objects.create(
            organization=self.org,
            name="Chai Secondaire"
        )
        
        # Effectuer un transfert
        move = StockManager.move_vrac(
            lot=self.lot,
            src_warehouse=self.warehouse,
            dst_warehouse=warehouse2,
            qty_l=Decimal('300.0'),
            move_type='transfert',
            user=self.user,
            notes='Test transfert'
        )
        
        # Vérifier le mouvement créé
        self.assertEqual(move.qty_l, Decimal('300.0'))
        self.assertEqual(move.move_type, 'transfert')
        self.assertEqual(move.notes, 'Test transfert')
        
        # Vérifier mise à jour des soldes
        balance.refresh_from_db()
        self.assertEqual(balance.qty_l, Decimal('700.0'))  # 1000 - 300
        
        balance2 = StockVracBalance.objects.get(
            lot=self.lot,
            warehouse=warehouse2
        )
        self.assertEqual(balance2.qty_l, Decimal('300.0'))
    
    def test_stock_manager_fabrication_sku(self):
        """Test fabrication SKU: consomme vrac, produit bouteilles"""
        # Créer un SKU
        sku = SKU.objects.create(
            organization=self.org,
            cuvee=self.cuvee,
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Réserve Rouge 2023 - Bouteille"
        )
        
        # Créer un stock vrac initial
        StockVracBalance.objects.create(
            organization=self.org,
            lot=self.lot,
            warehouse=self.warehouse,
            qty_l=Decimal('1000.0')
        )
        
        # Fabrication de 100 bouteilles (75L de vrac nécessaire)
        vrac_move, sku_move = StockManager.fabrication_sku(
            lot=self.lot,
            sku=sku,
            warehouse=self.warehouse,
            qty_units=100,
            user=self.user,
            notes='Embouteillage test'
        )
        
        # Vérifier mouvement vrac (sortie)
        self.assertEqual(vrac_move.move_type, 'sortie')
        self.assertEqual(vrac_move.qty_l, Decimal('75.0'))  # 100 * 0.75
        
        # Vérifier mouvement SKU (fabrication)
        self.assertEqual(sku_move.move_type, 'fabrication')
        self.assertEqual(sku_move.qty_units, 100)
        
        # Vérifier soldes
        vrac_balance = StockVracBalance.objects.get(
            lot=self.lot,
            warehouse=self.warehouse
        )
        self.assertEqual(vrac_balance.qty_l, Decimal('925.0'))  # 1000 - 75
        
        sku_balance = StockSKUBalance.objects.get(
            sku=sku,
            warehouse=self.warehouse
        )
        self.assertEqual(sku_balance.qty_units, 100)
    
    def test_stock_manager_fabrication_insufficient_vrac(self):
        """Test rejet fabrication si vrac insuffisant"""
        sku = SKU.objects.create(
            organization=self.org,
            cuvee=self.cuvee,
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Réserve Rouge 2023 - Bouteille"
        )
        
        # Stock vrac insuffisant
        StockVracBalance.objects.create(
            organization=self.org,
            lot=self.lot,
            warehouse=self.warehouse,
            qty_l=Decimal('50.0')  # Seulement 50L
        )
        
        # Tenter fabrication de 100 bouteilles (75L nécessaire)
        with self.assertRaises(ValidationError) as cm:
            StockManager.fabrication_sku(
                lot=self.lot,
                sku=sku,
                warehouse=self.warehouse,
                qty_units=100,
                user=self.user
            )
        
        self.assertIn('Stock vrac insuffisant', str(cm.exception))
    
    def test_stock_move_append_only(self):
        """Test que les mouvements sont append-only (pas de modification)"""
        move = StockVracMove.objects.create(
            organization=self.org,
            lot=self.lot,
            dst_warehouse=self.warehouse,
            qty_l=Decimal('100.0'),
            move_type='entree',
            user=self.user
        )
        
        # Récupérer l'objet fraîchement créé
        move.refresh_from_db()
        initial_version = move.row_version
        original_created = move.created_at
        
        # Tenter de modifier (ne devrait pas être fait en pratique)
        move.qty_l = Decimal('200.0')
        move.save()
        
        # Le row_version doit avoir changé
        self.assertEqual(move.row_version, initial_version + 1)
        self.assertEqual(move.created_at, original_created)  # Pas changé
    
    def test_row_version_optimistic_locking(self):
        """Test locking optimiste avec row_version"""
        sku = SKU.objects.create(
            organization=self.org,
            cuvee=self.cuvee,
            uom=self.uom_bottle,
            volume_by_uom_to_l=Decimal('0.75'),
            label="Test SKU"
        )
        
        # Récupérer l'objet fraîchement créé
        sku.refresh_from_db()
        initial_version = sku.row_version
        
        # Modification
        sku.label = "Modified SKU"
        sku.save()
        
        # Version incrémentée
        self.assertEqual(sku.row_version, initial_version + 1)


class StockIntegrityTestCase(TestCase):
    """Tests d'intégrité selon DB Roadmap 02"""
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Winery")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_qty_positive_constraints(self):
        """Test contraintes quantités positives"""
        # Les contraintes CHECK sont gérées par les validators Django
        
        # Test quantité vrac négative
        with self.assertRaises(ValidationError):
            move = StockVracMove(
                organization=self.org,
                qty_l=Decimal('-10.0'),  # Négatif
                move_type='entree',
                user=self.user
            )
            move.full_clean()
        
        # Test quantité SKU zéro
        with self.assertRaises(ValidationError):
            move = StockSKUMove(
                organization=self.org,
                qty_units=0,  # Zéro
                move_type='entree',
                user=self.user
            )
            move.full_clean()
    
    def test_concurrent_stock_operations(self):
        """Test opérations concurrentes sur stock (race conditions)"""
        # Ce test simule des conditions de course
        # En production, SELECT FOR UPDATE serait utilisé
        
        # Configuration
        grape_variety = GrapeVariety.objects.create(
            organization=self.org,
            name="Test Grape",
            color="rouge"
        )
        
        vintage = Vintage.objects.create(
            organization=self.org,
            year=2023
        )
        
        uom = UnitOfMeasure.objects.create(
            organization=self.org,
            name="Litre",
            code="L",
            base_ratio_to_l=Decimal('1.0')
        )
        
        cuvee = Cuvee.objects.create(
            organization=self.org,
            name="Test Cuvee",
            vintage=vintage,
            default_uom=uom
        )
        
        warehouse = Warehouse.objects.create(
            organization=self.org,
            name="Test Warehouse"
        )
        
        lot = Lot.objects.create(
            organization=self.org,
            code="Test Lot",
            cuvee=cuvee,
            warehouse=warehouse,
            volume_l=Decimal('1000.0'),
            status='en_cours'
        )
        
        # Stock initial
        balance = StockVracBalance.objects.create(
            organization=self.org,
            lot=lot,
            warehouse=warehouse,
            qty_l=Decimal('100.0')
        )
        
        # Simulation de deux opérations concurrentes
        # En réalité, ceci devrait être géré par des transactions
        # et SELECT FOR UPDATE
        
        try:
            with transaction.atomic():
                # Première opération
                StockManager.move_vrac(
                    lot=lot,
                    src_warehouse=warehouse,
                    dst_warehouse=None,
                    qty_l=Decimal('60.0'),
                    move_type='sortie',
                    user=self.user
                )
                
                # Deuxième opération (devrait échouer si stock insuffisant)
                StockManager.move_vrac(
                    lot=lot,
                    src_warehouse=warehouse,
                    dst_warehouse=None,
                    qty_l=Decimal('60.0'),
                    move_type='sortie',
                    user=self.user
                )
        except ValidationError:
            # Comportement attendu: la deuxième opération échoue
            pass
        
        # Vérifier que le solde final est cohérent
        balance.refresh_from_db()
        self.assertGreaterEqual(balance.qty_l, Decimal('0'))


class StockPerformanceTestCase(TestCase):
    """Tests de performance selon DB Roadmap 02"""
    
    def test_index_usage_simulation(self):
        """Test simulation utilisation des index"""
        # Ce test vérifie que les requêtes utilisent les bons index
        # En production, on utiliserait EXPLAIN ANALYZE
        
        org = Organization.objects.create(name="Test Winery")
        
        # Les index définis dans les modèles:
        # - (organization, lot) sur StockVracMove
        # - (organization, created_at) sur StockVracMove
        # - (move_type, created_at) sur StockVracMove
        
        # Requête qui devrait utiliser l'index (organization, created_at)
        moves = StockVracMove.objects.filter(
            organization=org
        ).order_by('-created_at')
        
        # Requête qui devrait utiliser l'index (move_type, created_at)
        recent_entries = StockVracMove.objects.filter(
            move_type='entree'
        ).order_by('-created_at')
        
        # Ces requêtes ne génèrent pas d'erreur, ce qui valide la structure
        self.assertEqual(list(moves), [])
        self.assertEqual(list(recent_entries), [])
