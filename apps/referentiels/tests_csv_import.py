"""
Tests pour l'import CSV des référentiels
Roadmap 18 - Import CSV des référentiels
"""

import io
import csv
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Organization, Membership
from apps.viticulture.models import GrapeVariety, Appellation, Vintage, UnitOfMeasure, VineyardPlot, Cuvee, Warehouse
from .csv_import import CSVImportService, CSVImportError

User = get_user_model()


class CSVImportServiceTestCase(TestCase):
    """Tests du service d'import CSV"""
    
    def setUp(self):
        # Créer une organisation et un utilisateur
        self.organization = Organization.objects.create(
            name="Test Domaine"
        )
        
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        # Créer le membership admin
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role='admin'
        )
        
        self.service = CSVImportService(self.organization)
    
    def test_detect_encoding_utf8(self):
        """Test détection encodage UTF-8"""
        content = "nom,couleur\nCabernet Sauvignon,rouge\n".encode('utf-8')
        encoding = self.service.detect_encoding(content)
        self.assertEqual(encoding, 'utf-8')
    
    def test_detect_encoding_latin1(self):
        """Test détection encodage Latin-1"""
        content = "nom,couleur\nCabernet Sauvignon,rouge\nPinot Noir,rouge\n".encode('latin-1')
        encoding = self.service.detect_encoding(content)
        self.assertIn(encoding, ['latin-1', 'ISO-8859-1'])
    
    def test_detect_delimiter_semicolon(self):
        """Test détection délimiteur point-virgule"""
        content = "nom;couleur\nCabernet Sauvignon;rouge\nChardonnay;blanc"
        delimiter = self.service.detect_delimiter(content)
        self.assertEqual(delimiter, ';')
    
    def test_detect_delimiter_comma(self):
        """Test détection délimiteur virgule"""
        content = "nom,couleur\nCabernet Sauvignon,rouge\nChardonnay,blanc"
        delimiter = self.service.detect_delimiter(content)
        self.assertEqual(delimiter, ',')
    
    def test_parse_csv_simple(self):
        """Test parsing CSV simple"""
        csv_content = "nom,couleur\nCabernet Sauvignon,rouge\nChardonnay,blanc"
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        
        headers, rows, encoding = self.service.parse_csv_file(file_obj)
        
        self.assertEqual(headers, ['nom', 'couleur'])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['Cabernet Sauvignon', 'rouge'])
        self.assertEqual(rows[1], ['Chardonnay', 'blanc'])
        self.assertEqual(encoding, 'utf-8')
    
    def test_validate_mapping_grape_valid(self):
        """Test validation mapping cépages valide"""
        mapping = {'nom': 'name', 'couleur': 'color'}
        errors = self.service.validate_mapping('grape', mapping)
        self.assertEqual(errors, [])
    
    def test_validate_mapping_grape_missing_required(self):
        """Test validation mapping cépages avec champ requis manquant"""
        mapping = {'couleur': 'color'}  # Manque 'name'
        errors = self.service.validate_mapping('grape', mapping)
        self.assertIn('Champ requis manquant: name', errors)
    
    def test_preview_import_grape_valid(self):
        """Test prévisualisation import cépages valide"""
        headers = ['nom', 'couleur']
        rows = [
            ['Cabernet Sauvignon', 'rouge'],
            ['Chardonnay', 'blanc']
        ]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result = self.service.preview_import('grape', headers, rows, mapping, limit=10)
        
        self.assertEqual(len(result['preview']), 2)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['total_rows'], 2)
    
    def test_preview_import_grape_with_errors(self):
        """Test prévisualisation import cépages avec erreurs"""
        headers = ['nom', 'couleur']
        rows = [
            ['', 'rouge'],  # Nom manquant
            ['Chardonnay', 'violet']  # Couleur invalide
        ]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result = self.service.preview_import('grape', headers, rows, mapping, limit=10)
        
        self.assertEqual(len(result['preview']), 2)
        self.assertTrue(len(result['errors']) > 0)
    
    def test_execute_import_grape_create(self):
        """Test exécution import cépages - création"""
        headers = ['nom', 'couleur']
        rows = [
            ['Cabernet Sauvignon', 'rouge'],
            ['Chardonnay', 'blanc']
        ]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result = self.service.execute_import('grape', headers, rows, mapping)
        
        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], 0)
        
        # Vérifier que les cépages ont été créés
        grapes = GrapeVariety.objects.filter(organization=self.organization)
        self.assertEqual(grapes.count(), 2)
        
        cabernet = grapes.get(name='Cabernet Sauvignon')
        self.assertEqual(cabernet.color, 'rouge')
    
    def test_execute_import_grape_update(self):
        """Test exécution import cépages - mise à jour"""
        # Créer un cépage existant
        existing_grape = GrapeVariety.objects.create(
            organization=self.organization,
            name='Cabernet Sauvignon',
            name_norm='cabernet sauvignon',
            color='rouge'
        )
        
        headers = ['nom', 'couleur']
        rows = [
            ['Cabernet Sauvignon', 'blanc']  # Changer la couleur
        ]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result = self.service.execute_import('grape', headers, rows, mapping)
        
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 1)
        self.assertEqual(result['errors'], 0)
        
        # Vérifier que le cépage a été mis à jour
        existing_grape.refresh_from_db()
        self.assertEqual(existing_grape.color, 'blanc')
    
    def test_execute_import_vintage_valid(self):
        """Test exécution import millésimes valide"""
        headers = ['annee']
        rows = [
            ['2020'],
            ['2021'],
            ['2022']
        ]
        mapping = {'annee': 'year'}
        
        result = self.service.execute_import('vintage', headers, rows, mapping)
        
        self.assertEqual(result['created'], 3)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], 0)
        
        # Vérifier que les millésimes ont été créés
        vintages = Vintage.objects.filter(organization=self.organization)
        self.assertEqual(vintages.count(), 3)
        self.assertTrue(vintages.filter(year=2020).exists())
        self.assertTrue(vintages.filter(year=2021).exists())
        self.assertTrue(vintages.filter(year=2022).exists())
    
    def test_execute_import_uom_valid(self):
        """Test exécution import unités de mesure valide"""
        headers = ['code', 'nom', 'ratio']
        rows = [
            ['BT', 'Bouteille', '0.75'],
            ['MAG', 'Magnum', '1.5']
        ]
        mapping = {'code': 'code', 'nom': 'name', 'ratio': 'base_ratio_to_l'}
        
        result = self.service.execute_import('uom', headers, rows, mapping)
        
        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], 0)
        
        # Vérifier que les UoM ont été créées
        uoms = UnitOfMeasure.objects.filter(organization=self.organization)
        self.assertEqual(uoms.count(), 2)
        
        bt = uoms.get(code='BT')
        self.assertEqual(bt.name, 'Bouteille')
        self.assertEqual(bt.base_ratio_to_l, Decimal('0.75'))
    
    def test_generate_error_report(self):
        """Test génération rapport d'erreurs"""
        errors = [
            'Ligne 1: name: requis',
            'Ligne 2: color: valeur invalide'
        ]
        
        report = self.service.generate_error_report(errors)
        
        # Vérifier le format CSV
        lines = report.strip().split('\n')
        self.assertEqual(len(lines), 3)  # Header + 2 erreurs
        self.assertEqual(lines[0], 'Ligne;Erreur')


class CSVImportViewsTestCase(TestCase):
    """Tests des vues d'import CSV"""
    
    def setUp(self):
        # Créer une organisation et un utilisateur admin
        self.organization = Organization.objects.create(
            name="Test Domaine",
            slug="test-domaine"
        )
        
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123"
        )
        
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role='admin'
        )
        
        self.client = Client()
        self.client.login(email="admin@example.com", password="testpass123")
        
        # Simuler le middleware d'organisation
        session = self.client.session
        session['current_org_id'] = str(self.organization.id)
        session.save()
    
    def test_import_csv_page_access_admin(self):
        """Test accès page import CSV pour admin"""
        url = reverse('referentiels:import_csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Import CSV des référentiels')
        self.assertContains(response, 'Cépages')
        self.assertContains(response, 'Appellations')
    
    def test_import_csv_preview_valid_file(self):
        """Test prévisualisation avec fichier valide"""
        # Créer un fichier CSV de test
        csv_content = "nom,couleur\nCabernet Sauvignon,rouge\nChardonnay,blanc"
        csv_file = SimpleUploadedFile(
            "cepages.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        url = reverse('referentiels:import_csv_preview')
        response = self.client.post(url, {
            'import_type': 'grape',
            'csv_file': csv_file
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['headers']), 2)
        self.assertEqual(len(data['preview']), 2)
        self.assertEqual(data['total_rows'], 2)
    
    def test_import_csv_preview_invalid_file_size(self):
        """Test prévisualisation avec fichier trop volumineux"""
        # Créer un fichier trop volumineux (simulé)
        large_content = "nom,couleur\n" + "Cépage,rouge\n" * 100000
        csv_file = SimpleUploadedFile(
            "large.csv",
            large_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        url = reverse('referentiels:import_csv_preview')
        response = self.client.post(url, {
            'import_type': 'grape',
            'csv_file': csv_file
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Fichier trop volumineux', data['error'])
    
    def test_import_csv_execute_valid(self):
        """Test exécution import valide"""
        # D'abord faire une prévisualisation pour mettre en session
        csv_content = "nom,couleur\nCabernet Sauvignon,rouge\nChardonnay,blanc"
        csv_file = SimpleUploadedFile(
            "cepages.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        preview_url = reverse('referentiels:import_csv_preview')
        self.client.post(preview_url, {
            'import_type': 'grape',
            'csv_file': csv_file
        })
        
        # Maintenant exécuter l'import
        execute_url = reverse('referentiels:import_csv_execute')
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        response = self.client.post(execute_url, {
            'mapping': json.dumps(mapping)
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['created'], 2)
        self.assertEqual(data['updated'], 0)
        self.assertEqual(data['errors'], 0)
        
        # Vérifier que les cépages ont été créés
        grapes = GrapeVariety.objects.filter(organization=self.organization)
        self.assertEqual(grapes.count(), 2)


class CSVImportRobustnessTestCase(TestCase):
    """Tests de robustesse pour l'import CSV"""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Domaine",
            slug="test-domaine"
        )
        self.service = CSVImportService(self.organization)
    
    def test_parse_csv_with_bom(self):
        """Test parsing CSV avec BOM UTF-8"""
        csv_content = "\ufeffnom,couleur\nCabernet Sauvignon,rouge"
        file_obj = io.BytesIO(csv_content.encode('utf-8-sig'))
        
        headers, rows, encoding = self.service.parse_csv_file(file_obj)
        
        self.assertEqual(headers, ['nom', 'couleur'])
        self.assertEqual(len(rows), 1)
        self.assertEqual(encoding, 'utf-8-sig')
    
    def test_parse_csv_empty_lines(self):
        """Test parsing CSV avec lignes vides"""
        csv_content = "nom,couleur\n\nCabernet Sauvignon,rouge\n\n\nChardonnay,blanc\n"
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        
        headers, rows, encoding = self.service.parse_csv_file(file_obj)
        
        self.assertEqual(headers, ['nom', 'couleur'])
        self.assertEqual(len(rows), 2)  # Lignes vides ignorées
    
    def test_parse_csv_malformed(self):
        """Test parsing CSV malformé"""
        csv_content = "nom,couleur\nCabernet Sauvignon,rouge,extra\nChardonnay"  # Colonnes incohérentes
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        
        # Ne doit pas planter
        headers, rows, encoding = self.service.parse_csv_file(file_obj)
        
        self.assertEqual(headers, ['nom', 'couleur'])
        self.assertEqual(len(rows), 2)
    
    def test_import_with_special_characters(self):
        """Test import avec caractères spéciaux"""
        headers = ['nom', 'couleur']
        rows = [
            ['Gewürztraminer', 'blanc'],  # Caractères allemands
            ['Côtes-du-Rhône', 'rouge'],  # Accents et tirets
            ["Château d'Yquem", 'blanc']  # Apostrophe
        ]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result = self.service.execute_import('grape', headers, rows, mapping)
        
        self.assertEqual(result['created'], 3)
        self.assertEqual(result['errors'], 0)
        
        # Vérifier que les noms sont correctement stockés
        grapes = GrapeVariety.objects.filter(organization=self.organization)
        names = [g.name for g in grapes]
        self.assertIn('Gewürztraminer', names)
        self.assertIn('Côtes-du-Rhône', names)
        self.assertIn("Château d'Yquem", names)
    
    def test_import_duplicate_handling(self):
        """Test gestion des doublons lors de l'import"""
        # Premier import
        headers = ['nom', 'couleur']
        rows = [['Cabernet Sauvignon', 'rouge']]
        mapping = {'nom': 'name', 'couleur': 'color'}
        
        result1 = self.service.execute_import('grape', headers, rows, mapping)
        self.assertEqual(result1['created'], 1)
        
        # Deuxième import avec même nom mais couleur différente
        rows = [['Cabernet Sauvignon', 'blanc']]
        result2 = self.service.execute_import('grape', headers, rows, mapping)
        
        self.assertEqual(result2['created'], 0)
        self.assertEqual(result2['updated'], 1)
        
        # Vérifier que la couleur a été mise à jour
        grape = GrapeVariety.objects.get(
            organization=self.organization,
            name='Cabernet Sauvignon'
        )
        self.assertEqual(grape.color, 'blanc')
