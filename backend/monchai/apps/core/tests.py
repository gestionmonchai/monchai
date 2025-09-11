import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from monchai.apps.accounts.models import Domaine, User, Profile
from monchai.apps.core.models import Parcelle, Cuve, Lot, Mouvement, Vendange, BouteilleLot


class TestParcelleModel(TestCase):
    def setUp(self):
        self.domaine = Domaine.objects.create(nom="Domaine Test")
    
    def test_create_parcelle_valid(self):
        parcelle = Parcelle.objects.create(
            domaine=self.domaine,
            nom="Les Carrières",
            cepage="Melon B.",
            surface_ha=Decimal("1.2")
        )
        self.assertEqual(parcelle.nom, "Les Carrières")
        self.assertEqual(parcelle.surface_ha, Decimal("1.2"))
    
    def test_surface_ha_positive_required(self):
        with self.assertRaises(ValidationError):
            parcelle = Parcelle(
                domaine=self.domaine,
                nom="Test",
                cepage="Test",
                surface_ha=Decimal("0")
            )
            parcelle.full_clean()


class TestMouvementModel(TestCase):
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
            volume_disponible_hl=Decimal("50")
        )
    
    def test_create_mouvement_inter_cuves(self):
        cuve_dest = Cuve.objects.create(
            domaine=self.domaine,
            nom="Cuve 2",
            capacite_hl=Decimal("80")
        )
        
        mouvement = Mouvement.objects.create(
            domaine=self.domaine,
            type="inter_cuves",
            source_lot=self.lot,
            destination_cuve=cuve_dest,
            volume_hl=Decimal("10"),
            date="2025-09-15"
        )
        
        self.assertEqual(mouvement.type, "inter_cuves")
        self.assertEqual(mouvement.volume_hl, Decimal("10"))
        self.assertEqual(mouvement.status, "draft")
    
    def test_volume_positive_required(self):
        with self.assertRaises(ValidationError):
            mouvement = Mouvement(
                domaine=self.domaine,
                type="perte",
                source_lot=self.lot,
                volume_hl=Decimal("0"),
                date="2025-09-15"
            )
            mouvement.full_clean()


class TestBouteilleLotModel(TestCase):
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
            volume_disponible_hl=Decimal("50")
        )
    
    def test_create_bouteille_lot(self):
        bouteille_lot = BouteilleLot.objects.create(
            domaine=self.domaine,
            source_lot=self.lot,
            nb_bouteilles=2500,
            contenance_ml=750,
            date="2025-09-20"
        )
        
        self.assertEqual(bouteille_lot.nb_bouteilles, 2500)
        self.assertEqual(bouteille_lot.contenance_ml, 750)
