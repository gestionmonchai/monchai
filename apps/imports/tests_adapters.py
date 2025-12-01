"""
Tests pour les adapters d'import
Validation des configurations et fonctionnalités de base
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership
from apps.referentiels.models import Parcelle, Entrepot, Unite
from apps.viticulture.models import Cuvee, Appellation, Vintage, UnitOfMeasure
from .adapters import get_adapter, IMPORT_ADAPTERS

User = get_user_model()


class ImportAdaptersTestCase(TestCase):
    """Tests des adapters d'import"""
    
    def setUp(self):
        """Configuration des tests"""
        # Organisation de test
        self.organization = Organization.objects.create(
            name="Test Domaine",
            siret="12345678901234"
        )
        
        # Utilisateur de test
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Membership
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role="admin"
        )
        
        # Données de référence pour tests
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Bouteille",
            code="BTL",
            base_ratio_to_l=0.75  # 0.75L par bouteille
        )
        
        self.unite = Unite.objects.create(
            organization=self.organization,
            nom="Bouteille",
            symbole="BTL"
        )
        
        self.appellation = Appellation.objects.create(
            organization=self.organization,
            name="Côtes du Rhône",
            type="rouge"
        )
        
        self.vintage = Vintage.objects.create(
            organization=self.organization,
            year=2023
        )
    
    def test_adapter_registry(self):
        """Test du registry des adapters"""
        # Vérifier que tous les adapters sont enregistrés
        expected_adapters = ['grape_variety', 'parcelle', 'unite', 'cuvee', 'entrepot']
        
        for entity_type in expected_adapters:
            self.assertIn(entity_type, IMPORT_ADAPTERS)
            
            # Vérifier qu'on peut récupérer l'adapter
            adapter = get_adapter(entity_type)
            self.assertIsNotNone(adapter)
            self.assertEqual(adapter.entity_name, entity_type)
    
    def test_parcelle_adapter(self):
        """Test de l'adapter parcelle"""
        adapter = get_adapter('parcelle')
        
        # Test du schéma
        schema = adapter.get_schema()
        self.assertIn('nom', schema['required_fields'])
        self.assertIn('surface_ha', schema['optional_fields'])
        
        # Test de validation
        valid, msg = adapter._validate_nom_length("Test Parcelle")
        self.assertTrue(valid)
        
        invalid, msg = adapter._validate_nom_length("A")
        self.assertFalse(invalid)
        self.assertIn("au moins 2 caractères", msg)
        
        # Test de transformation
        row_data = {'nom': '  test parcelle  ', 'surface_ha': '2,5'}
        transformed = adapter.transform_row(row_data)
        self.assertEqual(transformed['surface_ha'], 2.5)
    
    def test_unite_adapter(self):
        """Test de l'adapter unité"""
        adapter = get_adapter('unite')
        
        # Test du schéma
        schema = adapter.get_schema()
        self.assertIn('nom', schema['required_fields'])
        self.assertIn('symbole', schema['required_fields'])
        
        # Test de validation symbole
        valid, msg = adapter._validate_symbole_format("BTL")
        self.assertTrue(valid)
        
        invalid, msg = adapter._validate_symbole_format("")
        self.assertFalse(invalid)
        self.assertIn("requis", msg)
        
        # Test de transformation
        row_data = {'nom': 'bouteille', 'symbole': 'btl'}
        transformed = adapter.transform_row(row_data)
        self.assertEqual(transformed['symbole'], 'BTL')
    
    def test_cuvee_adapter(self):
        """Test de l'adapter cuvée"""
        adapter = get_adapter('cuvee')
        
        # Test du schéma
        schema = adapter.get_schema()
        self.assertIn('name', schema['required_fields'])
        self.assertIn('default_uom', schema['required_fields'])
        self.assertIn('appellation', schema['optional_fields'])
        
        # Test de validation vintage
        valid, msg = adapter._validate_vintage_year("2023")
        self.assertTrue(valid)
        
        invalid, msg = adapter._validate_vintage_year("1800")
        self.assertFalse(invalid)
        self.assertIn("invalide", msg)
        
        # Test de résolution FK
        row_data = {
            'name': 'Test Cuvée',
            'default_uom': 'BTL',
            'appellation': 'Côtes du Rhône',
            'vintage': 2023
        }
        resolved = adapter.resolve_foreign_keys(self.organization, row_data)
        self.assertEqual(resolved['default_uom'], self.uom)
        self.assertEqual(resolved['appellation'], self.appellation)
        self.assertEqual(resolved['vintage'], self.vintage)
    
    def test_entrepot_adapter(self):
        """Test de l'adapter entrepôt"""
        adapter = get_adapter('entrepot')
        
        # Test du schéma
        schema = adapter.get_schema()
        self.assertIn('nom', schema['required_fields'])
        self.assertIn('notes', schema['optional_fields'])
        
        # Test de validation
        valid, msg = adapter._validate_nom_length("Entrepôt Principal")
        self.assertTrue(valid)
        
        # Test de création d'instance
        validated_data = {'nom': 'Test Entrepôt', 'notes': 'Test notes'}
        instance = adapter.create_instance(self.organization, validated_data)
        
        self.assertIsInstance(instance, Entrepot)
        self.assertEqual(instance.nom, 'Test Entrepôt')
        self.assertEqual(instance.organization, self.organization)
    
    def test_unite_creation(self):
        """Test de création d'unité"""
        adapter = get_adapter('unite')
        
        # Test de création d'instance
        validated_data = {'nom': 'Test Unité', 'symbole': 'TU'}
        instance = adapter.create_instance(self.organization, validated_data)
        
        self.assertIsInstance(instance, Unite)
        self.assertEqual(instance.nom, 'Test Unité')
        self.assertEqual(instance.symbole, 'TU')
        self.assertEqual(instance.organization, self.organization)
    
    def test_adapter_error_handling(self):
        """Test de gestion d'erreurs"""
        # Test adapter inexistant
        with self.assertRaises(ValueError):
            get_adapter('inexistant')
        
        # Test résolution FK inexistante
        adapter = get_adapter('cuvee')
        row_data = {
            'name': 'Test',
            'default_uom': 'INEXISTANT'
        }
        resolved = adapter.resolve_foreign_keys(self.organization, row_data)
        self.assertIn('_errors', resolved)
        self.assertIn('non trouvée', resolved['_errors'][0])
    
    def test_adapter_synonyms(self):
        """Test des synonymes de colonnes"""
        adapter = get_adapter('parcelle')
        schema = adapter.get_schema()
        
        # Vérifier que les synonymes sont configurés
        self.assertIn('nom', schema['synonyms'])
        self.assertIn('name', schema['synonyms']['nom'])
        self.assertIn('libelle', schema['synonyms']['nom'])
    
    def test_adapter_transforms(self):
        """Test des transformations par défaut"""
        adapter = get_adapter('unite')
        schema = adapter.get_schema()
        
        # Vérifier les transformations
        self.assertIn('nom', schema['transforms_defaults'])
        self.assertIn('trim', schema['transforms_defaults']['nom'])
        self.assertIn('title_case', schema['transforms_defaults']['nom'])
        
        self.assertIn('symbole', schema['transforms_defaults'])
        self.assertIn('upper', schema['transforms_defaults']['symbole'])
