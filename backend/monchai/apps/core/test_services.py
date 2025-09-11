import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction
from monchai.apps.accounts.models import Domaine
from monchai.apps.core.models import Parcelle, Cuve, Lot, Mouvement, Vendange, BouteilleLot
from monchai.apps.core.services import MouvementService, MiseEnBouteilleService


class TestMouvementService(TestCase):
    def setUp(self):
        self.domaine = Domaine.objects.create(nom="Domaine Test")
        self.cuve1 = Cuve.objects.create(
            domaine=self.domaine,
            nom="Cuve 1",
            capacite_hl=Decimal("100")
        )
        self.cuve2 = Cuve.objects.create(
            domaine=self.domaine,
            nom="Cuve 2", 
            capacite_hl=Decimal("80")
        )
        self.lot = Lot.objects.create(
            domaine=self.domaine,
            cuve=self.cuve1,
            volume_disponible_hl=Decimal("50"),
            ref_interne="LOT-TEST-001"
        )
    
    def test_create_inter_cuves_valid(self):
        """Test création mouvement inter-cuves valide"""
        mouvement = MouvementService.create_inter_cuves(
            source_lot_id=self.lot.id,
            destination_cuve_id=self.cuve2.id,
            volume_hl=Decimal("10"),
            date="2025-09-15",
            commentaire="Test soutirage"
        )
        
        self.assertEqual(mouvement.type, "inter_cuves")
        self.assertEqual(mouvement.volume_hl, Decimal("10"))
        self.assertEqual(mouvement.status, "draft")
        self.assertEqual(mouvement.source_lot, self.lot)
        self.assertEqual(mouvement.destination_cuve, self.cuve2)
    
    def test_create_inter_cuves_volume_insuffisant(self):
        """Test volume insuffisant dans lot source"""
        with self.assertRaises(ValidationError) as cm:
            MouvementService.create_inter_cuves(
                source_lot_id=self.lot.id,
                destination_cuve_id=self.cuve2.id,
                volume_hl=Decimal("60"),  # Plus que les 50 hl disponibles
                date="2025-09-15"
            )
        
        self.assertIn("Volume insuffisant", str(cm.exception))
    
    def test_create_inter_cuves_volume_negatif(self):
        """Test volume négatif"""
        with self.assertRaises(ValidationError) as cm:
            MouvementService.create_inter_cuves(
                source_lot_id=self.lot.id,
                destination_cuve_id=self.cuve2.id,
                volume_hl=Decimal("-5"),
                date="2025-09-15"
            )
        
        self.assertIn("doit être positif", str(cm.exception))
    
    def test_create_perte_valid(self):
        """Test création mouvement de perte valide"""
        mouvement = MouvementService.create_perte(
            source_lot_id=self.lot.id,
            volume_hl=Decimal("2"),
            date="2025-09-15",
            commentaire="Perte évaporation"
        )
        
        self.assertEqual(mouvement.type, "perte")
        self.assertEqual(mouvement.volume_hl, Decimal("2"))
        self.assertEqual(mouvement.commentaire, "Perte évaporation")
    
    def test_create_perte_sans_commentaire(self):
        """Test perte sans commentaire (doit échouer)"""
        with self.assertRaises(ValidationError) as cm:
            MouvementService.create_perte(
                source_lot_id=self.lot.id,
                volume_hl=Decimal("2"),
                date="2025-09-15",
                commentaire=""
            )
        
        self.assertIn("commentaire est obligatoire", str(cm.exception))
    
    def test_valider_mouvement_inter_cuves(self):
        """Test validation d'un mouvement inter-cuves"""
        # Créer le mouvement
        mouvement = MouvementService.create_inter_cuves(
            source_lot_id=self.lot.id,
            destination_cuve_id=self.cuve2.id,
            volume_hl=Decimal("10"),
            date="2025-09-15"
        )
        
        # Volume initial du lot source
        volume_initial = self.lot.volume_disponible_hl
        
        # Valider le mouvement
        mouvement_valide = MouvementService.valider_mouvement(mouvement.id)
        
        # Vérifications
        self.assertEqual(mouvement_valide.status, "valide")
        
        # Recharger le lot source
        self.lot.refresh_from_db()
        self.assertEqual(
            self.lot.volume_disponible_hl,
            volume_initial - Decimal("10")
        )
        
        # Vérifier qu'un lot a été créé dans la cuve destination
        lot_destination = Lot.objects.filter(cuve=self.cuve2).first()
        self.assertIsNotNone(lot_destination)
        self.assertEqual(lot_destination.volume_disponible_hl, Decimal("10"))
    
    def test_valider_mouvement_perte(self):
        """Test validation d'un mouvement de perte"""
        mouvement = MouvementService.create_perte(
            source_lot_id=self.lot.id,
            volume_hl=Decimal("3"),
            date="2025-09-15",
            commentaire="Évaporation"
        )
        
        volume_initial = self.lot.volume_disponible_hl
        
        # Valider
        MouvementService.valider_mouvement(mouvement.id)
        
        # Vérifier la diminution du volume
        self.lot.refresh_from_db()
        self.assertEqual(
            self.lot.volume_disponible_hl,
            volume_initial - Decimal("3")
        )
    
    def test_valider_mouvement_deja_valide(self):
        """Test validation d'un mouvement déjà validé"""
        mouvement = MouvementService.create_perte(
            source_lot_id=self.lot.id,
            volume_hl=Decimal("2"),
            date="2025-09-15",
            commentaire="Test"
        )
        
        # Première validation
        MouvementService.valider_mouvement(mouvement.id)
        
        # Tentative de re-validation
        with self.assertRaises(ValidationError) as cm:
            MouvementService.valider_mouvement(mouvement.id)
        
        self.assertIn("brouillon", str(cm.exception))


class TestMiseEnBouteilleService(TestCase):
    def setUp(self):
        self.domaine = Domaine.objects.create(nom="Domaine Test")
        self.cuve = Cuve.objects.create(
            domaine=self.domaine,
            nom="Cuve 1",
            capacite_hl=Decimal("100")
        )
        self.lot = Lot.objects.create(
            domaine=self.domaine,
            cuve=self.cuve,
            volume_disponible_hl=Decimal("20"),  # 20 hl = 2000 L
            ref_interne="LOT-BOUTEILLE-001"
        )
    
    def test_mise_en_bouteille_valid(self):
        """Test mise en bouteille valide"""
        mouvement, bouteille_lot = MiseEnBouteilleService.executer_mise_en_bouteille(
            source_lot_id=self.lot.id,
            nb_bouteilles=2500,  # 2500 * 0.75L = 1875L = 18.75 hl
            contenance_ml=750,
            taux_perte_hl=Decimal("0.25"),
            date="2025-09-20"
        )
        
        # Vérifications mouvement
        self.assertEqual(mouvement.type, "mise_en_bouteille")
        self.assertEqual(mouvement.status, "valide")
        self.assertEqual(mouvement.volume_hl, Decimal("19"))  # 18.75 + 0.25
        
        # Vérifications bouteille lot
        self.assertEqual(bouteille_lot.nb_bouteilles, 2500)
        self.assertEqual(bouteille_lot.contenance_ml, 750)
        self.assertEqual(bouteille_lot.source_lot, self.lot)
        
        # Vérifier diminution du lot source
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.volume_disponible_hl, Decimal("1"))  # 20 - 19
    
    def test_mise_en_bouteille_volume_insuffisant(self):
        """Test mise en bouteille avec volume insuffisant"""
        with self.assertRaises(ValidationError) as cm:
            MiseEnBouteilleService.executer_mise_en_bouteille(
                source_lot_id=self.lot.id,
                nb_bouteilles=3000,  # 3000 * 0.75L = 2250L = 22.5 hl > 20 hl disponibles
                contenance_ml=750,
                date="2025-09-20"
            )
        
        self.assertIn("Volume insuffisant", str(cm.exception))


class TestVendangeVersCuve(TestCase):
    def setUp(self):
        self.domaine = Domaine.objects.create(nom="Domaine Test")
        self.parcelle = Parcelle.objects.create(
            domaine=self.domaine,
            nom="Les Carrières",
            cepage="Melon B.",
            surface_ha=Decimal("1.2")
        )
        self.cuve = Cuve.objects.create(
            domaine=self.domaine,
            nom="Cuve 1",
            capacite_hl=Decimal("100")
        )
        self.vendange = Vendange.objects.create(
            parcelle=self.parcelle,
            date="2025-09-12",
            volume_hl=Decimal("25.4"),
            dechets_hl=Decimal("0.8")
        )
    
    def test_create_vendange_vers_cuve(self):
        """Test création mouvement vendange vers cuve"""
        mouvement = MouvementService.create_vendange_vers_cuve(
            vendange_id=self.vendange.id,
            destination_cuve_id=self.cuve.id
        )
        
        self.assertEqual(mouvement.type, "vendange_vers_cuve")
        self.assertEqual(mouvement.volume_hl, Decimal("24.6"))  # 25.4 - 0.8
        self.assertEqual(mouvement.pertes_hl, Decimal("0.8"))
        self.assertEqual(mouvement.destination_cuve, self.cuve)
        
        # Valider et vérifier création du lot
        MouvementService.valider_mouvement(mouvement.id)
        
        lot_cree = Lot.objects.filter(cuve=self.cuve).first()
        self.assertIsNotNone(lot_cree)
        self.assertEqual(lot_cree.volume_disponible_hl, Decimal("24.6"))
