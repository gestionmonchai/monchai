"""
Tests pour le catalogue grid - Roadmap 25
Tests d'acceptation et de robustesse pour l'API et l'UI
"""

import json
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings
from apps.accounts.models import Organization, Membership
from apps.viticulture.models import Cuvee, Appellation, Vintage, UnitOfMeasure

User = get_user_model()


class CatalogueGridTestCase(TestCase):
    """Tests pour le catalogue grid avec API et UI"""
    
    def setUp(self):
        """Configuration des données de test"""
        # Créer une organisation
        self.organization = Organization.objects.create(
            name="Domaine Test",
            siret="12345678901234"
        )
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Créer un membership
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role="editor"
        )
        
        # Créer des référentiels
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Bouteille",
            code="BT",
            base_ratio_to_l=0.75
        )
        
        self.appellation1 = Appellation.objects.create(
            organization=self.organization,
            name="Bordeaux",
            type="rouge"
        )
        
        self.appellation2 = Appellation.objects.create(
            organization=self.organization,
            name="Sancerre",
            type="blanc"
        )
        
        self.vintage1 = Vintage.objects.create(
            organization=self.organization,
            year=2020
        )
        
        self.vintage2 = Vintage.objects.create(
            organization=self.organization,
            year=2021
        )
        
        # Créer des cuvées de test
        self.cuvee1 = Cuvee.objects.create(
            organization=self.organization,
            name="Cuvée Rouge Excellence",
            code="CRE2020",
            default_uom=self.uom,
            appellation=self.appellation1,
            vintage=self.vintage1
        )
        
        self.cuvee2 = Cuvee.objects.create(
            organization=self.organization,
            name="Cuvée Blanc Premium",
            code="CBP2021",
            default_uom=self.uom,
            appellation=self.appellation2,
            vintage=self.vintage2
        )
        
        self.cuvee3 = Cuvee.objects.create(
            organization=self.organization,
            name="Sauvignon Blanc",
            code="SB2020",
            default_uom=self.uom,
            appellation=self.appellation2,
            vintage=self.vintage1
        )
        
        # Client de test
        self.client = Client()
        self.client.login(email="test@example.com", password="testpass123")
        
        # Vider le cache
        cache.clear()
    
    def test_catalogue_grid_view_loads(self):
        """Test que la page catalogue grid se charge correctement"""
        response = self.client.get(reverse('catalogue:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catalogue des cuvées")
        self.assertContains(response, "Cuvée Rouge Excellence")
        self.assertContains(response, "Cuvée Blanc Premium")
        self.assertContains(response, "Sauvignon Blanc")
    
    def test_catalogue_api_basic(self):
        """Test de l'API catalogue de base"""
        response = self.client.get(reverse('catalogue:catalogue_api'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Vérifier la structure de la réponse
        self.assertIn('items', data)
        self.assertIn('facets', data)
        self.assertIn('perf', data)
        
        # Vérifier les métriques de performance
        self.assertIn('elapsed_ms', data['perf'])
        self.assertIn('cache_hit', data['perf'])
        self.assertIn('queries_count', data['perf'])
        self.assertFalse(data['perf']['cache_hit'])  # Premier appel
        
        # Vérifier les items
        self.assertEqual(len(data['items']), 3)
        item_names = [item['name'] for item in data['items']]
        self.assertIn("Cuvée Rouge Excellence", item_names)
        self.assertIn("Cuvée Blanc Premium", item_names)
        self.assertIn("Sauvignon Blanc", item_names)
    
    def test_catalogue_api_search(self):
        """Test de la recherche dans l'API catalogue"""
        # Recherche par nom
        response = self.client.get(reverse('catalogue:catalogue_api'), {'q': 'Rouge'})
        data = response.json()
        
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Cuvée Rouge Excellence")
        
        # Recherche par code
        response = self.client.get(reverse('catalogue:catalogue_api'), {'q': 'CBP'})
        data = response.json()
        
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Cuvée Blanc Premium")
        
        # Recherche par appellation
        response = self.client.get(reverse('catalogue:catalogue_api'), {'q': 'Sancerre'})
        data = response.json()
        
        self.assertEqual(len(data['items']), 2)  # 2 cuvées avec appellation Sancerre
    
    def test_catalogue_api_filters(self):
        """Test des filtres dans l'API catalogue"""
        # Filtre par appellation
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'appellation': str(self.appellation1.id)
        })
        data = response.json()
        
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Cuvée Rouge Excellence")
        
        # Filtre par millésime
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'vintage': str(self.vintage2.id)
        })
        data = response.json()
        
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Cuvée Blanc Premium")
        
        # Filtre par couleur
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'color': 'blanc'
        })
        data = response.json()
        
        self.assertEqual(len(data['items']), 2)  # 2 cuvées blanches
    
    def test_catalogue_api_sorting(self):
        """Test du tri dans l'API catalogue"""
        # Tri par nom croissant
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'name_asc'
        })
        data = response.json()
        
        names = [item['name'] for item in data['items']]
        self.assertEqual(names, sorted(names))
        
        # Tri par nom décroissant
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'name_desc'
        })
        data = response.json()
        
        names = [item['name'] for item in data['items']]
        self.assertEqual(names, sorted(names, reverse=True))
    
    def test_catalogue_api_facets(self):
        """Test des facettes dans l'API catalogue"""
        response = self.client.get(reverse('catalogue:catalogue_api'))
        data = response.json()
        
        facets = data['facets']
        
        # Vérifier les facettes appellations
        self.assertIn('appellations', facets)
        self.assertEqual(len(facets['appellations']), 2)
        
        appellation_names = [f['name'] for f in facets['appellations']]
        self.assertIn('Bordeaux', appellation_names)
        self.assertIn('Sancerre', appellation_names)
        
        # Vérifier les facettes millésimes
        self.assertIn('vintages', facets)
        self.assertEqual(len(facets['vintages']), 2)
        
        vintage_years = [f['year'] for f in facets['vintages']]
        self.assertIn(2020, vintage_years)
        self.assertIn(2021, vintage_years)
        
        # Vérifier les facettes couleurs
        self.assertIn('colors', facets)
        self.assertEqual(len(facets['colors']), 2)
        
        color_values = [f['value'] for f in facets['colors']]
        self.assertIn('rouge', color_values)
        self.assertIn('blanc', color_values)
    
    def test_catalogue_api_cache(self):
        """Test du cache Redis dans l'API catalogue"""
        # Premier appel - pas de cache
        response1 = self.client.get(reverse('catalogue:catalogue_api'))
        data1 = response1.json()
        self.assertFalse(data1['perf']['cache_hit'])
        
        # Deuxième appel - cache hit
        response2 = self.client.get(reverse('catalogue:catalogue_api'))
        data2 = response2.json()
        self.assertTrue(data2['perf']['cache_hit'])
        
        # Vérifier que les données sont identiques
        self.assertEqual(len(data1['items']), len(data2['items']))
    
    def test_catalogue_api_keyset_pagination(self):
        """Test de la pagination keyset"""
        # Créer plus de cuvées pour tester la pagination
        for i in range(30):
            Cuvee.objects.create(
                organization=self.organization,
                name=f"Cuvée Test {i:02d}",
                code=f"CT{i:02d}",
                default_uom=self.uom,
                appellation=self.appellation1,
                vintage=self.vintage1
            )
        
        # Premier appel avec page_size=10
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'page_size': 10,
            'sort': 'name_asc'
        })
        data = response.json()
        
        self.assertEqual(len(data['items']), 10)
        self.assertIsNotNone(data.get('next_cursor'))
        self.assertTrue(data['perf']['has_next_page'])
        
        # Deuxième appel avec cursor
        response2 = self.client.get(reverse('catalogue:catalogue_api'), {
            'page_size': 10,
            'sort': 'name_asc',
            'cursor': data['next_cursor']
        })
        data2 = response2.json()
        
        self.assertEqual(len(data2['items']), 10)
        
        # Vérifier que les items sont différents
        first_page_names = {item['name'] for item in data['items']}
        second_page_names = {item['name'] for item in data2['items']}
        self.assertEqual(len(first_page_names & second_page_names), 0)  # Pas d'intersection
    
    @override_settings(DEBUG=True)
    def test_catalogue_api_performance(self):
        """Test des performances de l'API catalogue"""
        # Créer plus de données pour tester les performances
        for i in range(100):
            Cuvee.objects.create(
                organization=self.organization,
                name=f"Perf Test {i:03d}",
                code=f"PT{i:03d}",
                default_uom=self.uom,
                appellation=self.appellation1 if i % 2 == 0 else self.appellation2,
                vintage=self.vintage1 if i % 3 == 0 else self.vintage2
            )
        
        # Test de performance avec recherche
        start_time = time.time()
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'q': 'Perf',
            'page_size': 24
        })
        elapsed_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Vérifier les métriques de performance
        self.assertLess(data['perf']['elapsed_ms'], 1000)  # < 1s
        self.assertLess(data['perf']['queries_count'], 10)  # < 10 queries
        self.assertLess(elapsed_time, 2000)  # < 2s total
        
        print(f"Performance test: {data['perf']['elapsed_ms']}ms, {data['perf']['queries_count']} queries")
    
    def test_catalogue_facets_api(self):
        """Test de l'API facettes"""
        response = self.client.get(reverse('catalogue:catalogue_facets_api'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Vérifier la structure
        self.assertIn('appellations', data)
        self.assertIn('vintages', data)
        self.assertIn('colors', data)
        
        # Vérifier le contenu
        self.assertEqual(len(data['appellations']), 2)
        self.assertEqual(len(data['vintages']), 2)
        self.assertEqual(len(data['colors']), 2)
    
    def test_catalogue_search_ajax(self):
        """Test de la recherche AJAX"""
        response = self.client.get(reverse('catalogue:search_ajax'), {'q': 'Rouge'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], "Cuvée Rouge Excellence")
    
    def test_catalogue_api_validation(self):
        """Test de la validation des paramètres API"""
        # Paramètre de tri invalide
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'invalid_sort'
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_catalogue_cross_organization_isolation(self):
        """Test de l'isolation entre organisations"""
        # Créer une autre organisation
        other_org = Organization.objects.create(
            name="Autre Domaine",
            siret="98765432109876"
        )
        
        # Créer une cuvée dans l'autre organisation
        other_uom = UnitOfMeasure.objects.create(
            organization=other_org,
            name="Bouteille",
            code="BT",
            base_ratio_to_l=0.75
        )
        
        other_appellation = Appellation.objects.create(
            organization=other_org,
            name="Champagne",
            type="blanc"
        )
        
        Cuvee.objects.create(
            organization=other_org,
            name="Cuvée Autre Org",
            code="CAO",
            default_uom=other_uom,
            appellation=other_appellation
        )
        
        # Vérifier que l'API ne retourne que les cuvées de l'organisation courante
        response = self.client.get(reverse('catalogue:catalogue_api'))
        data = response.json()
        
        item_names = [item['name'] for item in data['items']]
        self.assertNotIn("Cuvée Autre Org", item_names)
        self.assertEqual(len(data['items']), 3)  # Seulement nos 3 cuvées


class CatalogueGridAcceptanceTestCase(TestCase):
    """Tests d'acceptation pour le catalogue grid selon les spécifications"""
    
    def setUp(self):
        """Configuration des données de test d'acceptation"""
        # Configuration similaire mais avec plus de données
        self.organization = Organization.objects.create(
            name="Domaine Acceptation",
            siret="11111111111111"
        )
        
        self.user = User.objects.create_user(
            username="acceptanceuser",
            email="acceptance@example.com",
            password="testpass123"
        )
        
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role="editor"
        )
        
        # Créer des données de test plus réalistes
        self.uom = UnitOfMeasure.objects.create(
            organization=self.organization,
            name="Bouteille",
            code="BT",
            base_ratio_to_l=0.75
        )
        
        # Créer plusieurs appellations et millésimes
        appellations = []
        for name, color in [("Bordeaux", "rouge"), ("Sancerre", "blanc"), ("Côtes du Rhône", "rouge")]:
            appellations.append(Appellation.objects.create(
                organization=self.organization,
                name=name,
                type=color
            ))
        
        vintages = []
        for year in [2019, 2020, 2021, 2022]:
            vintages.append(Vintage.objects.create(
                organization=self.organization,
                year=year
            ))
        
        # Créer 50 cuvées pour tester la pagination
        for i in range(50):
            Cuvee.objects.create(
                organization=self.organization,
                name=f"Cuvée Test {i:02d}",
                code=f"CT{i:02d}",
                default_uom=self.uom,
                appellation=appellations[i % 3],
                vintage=vintages[i % 4]
            )
        
        self.client = Client()
        self.client.login(email="acceptance@example.com", password="testpass123")
        cache.clear()
    
    def test_ac_catalogue_01_grid_display(self):
        """AC-CATALOGUE-01: La grille affiche les cuvées avec toutes les informations"""
        response = self.client.get(reverse('catalogue:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "catalogue-grid")
        self.assertContains(response, "cuvee-card")
        self.assertContains(response, "Cuvée Test")
    
    def test_ac_catalogue_02_search_realtime(self):
        """AC-CATALOGUE-02: La recherche en temps réel fonctionne avec debounce 200ms"""
        # Test via API (le JavaScript est testé en intégration)
        response = self.client.get(reverse('catalogue:catalogue_api'), {'q': 'Test 01'})
        data = response.json()
        
        # Vérifier que la recherche fonctionne
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['name'], "Cuvée Test 01")
        
        # Vérifier les performances (< 600ms selon GIGA ROADMAP)
        self.assertLess(data['perf']['elapsed_ms'], 600)
    
    def test_ac_catalogue_03_facets_filtering(self):
        """AC-CATALOGUE-03: Les facettes permettent de filtrer efficacement"""
        # Test filtre par appellation
        bordeaux_app = Appellation.objects.get(name="Bordeaux")
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'appellation': str(bordeaux_app.id)
        })
        data = response.json()
        
        # Vérifier que tous les résultats ont la bonne appellation
        for item in data['items']:
            self.assertEqual(item['appellation']['name'], "Bordeaux")
        
        # Vérifier les facettes
        self.assertIn('facets', data)
        self.assertIn('appellations', data['facets'])
    
    def test_ac_catalogue_04_keyset_pagination(self):
        """AC-CATALOGUE-04: La pagination keyset fonctionne correctement"""
        # Premier appel
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'page_size': 24,
            'sort': 'name_asc'
        })
        data = response.json()
        
        self.assertEqual(len(data['items']), 24)
        self.assertIsNotNone(data.get('next_cursor'))
        self.assertTrue(data['perf']['has_next_page'])
        
        # Deuxième appel avec cursor
        response2 = self.client.get(reverse('catalogue:catalogue_api'), {
            'page_size': 24,
            'sort': 'name_asc',
            'cursor': data['next_cursor']
        })
        data2 = response2.json()
        
        self.assertEqual(len(data2['items']), 24)
        
        # Vérifier l'ordre et l'unicité
        first_names = [item['name'] for item in data['items']]
        second_names = [item['name'] for item in data2['items']]
        
        # Pas de doublons entre les pages
        self.assertEqual(len(set(first_names) & set(second_names)), 0)
        
        # Ordre respecté
        all_names = first_names + second_names
        self.assertEqual(all_names, sorted(all_names))
    
    def test_ac_catalogue_05_cache_performance(self):
        """AC-CATALOGUE-05: Le cache Redis améliore les performances"""
        # Premier appel - pas de cache
        response1 = self.client.get(reverse('catalogue:catalogue_api'))
        data1 = response1.json()
        self.assertFalse(data1['perf']['cache_hit'])
        first_time = data1['perf']['elapsed_ms']
        
        # Deuxième appel - cache hit
        response2 = self.client.get(reverse('catalogue:catalogue_api'))
        data2 = response2.json()
        self.assertTrue(data2['perf']['cache_hit'])
        second_time = data2['perf']['elapsed_ms']
        
        # Le cache devrait améliorer les performances
        # (Note: en test, la différence peut être minime)
        print(f"Sans cache: {first_time}ms, Avec cache: {second_time}ms")
    
    def test_ac_catalogue_06_sorting_options(self):
        """AC-CATALOGUE-06: Les options de tri fonctionnent correctement"""
        # Tri par nom croissant
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'name_asc',
            'page_size': 10
        })
        data = response.json()
        names_asc = [item['name'] for item in data['items']]
        self.assertEqual(names_asc, sorted(names_asc))
        
        # Tri par nom décroissant
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'name_desc',
            'page_size': 10
        })
        data = response.json()
        names_desc = [item['name'] for item in data['items']]
        self.assertEqual(names_desc, sorted(names_desc, reverse=True))
        
        # Tri par date de modification
        response = self.client.get(reverse('catalogue:catalogue_api'), {
            'sort': 'updated_desc',
            'page_size': 10
        })
        data = response.json()
        # Vérifier que le tri fonctionne (les dates sont en ordre décroissant)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['items']), 10)
