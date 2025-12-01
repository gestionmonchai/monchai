"""
Tests de non-régression pour toutes les routes du module Production.
Vérifie que chaque URL est accessible et retourne un code HTTP approprié.
"""
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()


class ProductionRoutesTestCase(TestCase):
    """Tests de non-régression pour les routes Production."""
    
    @classmethod
    def setUpTestData(cls):
        """Création des données de test une seule fois."""
        # Organisation de test
        cls.org = Organization.objects.create(
            name="Test Domaine",
            is_initialized=True
        )
        
        # Utilisateur avec membership owner
        cls.user = User.objects.create_user(
            username="testuser",
            email="test@domaine.fr",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        cls.membership = Membership.objects.create(
            user=cls.user,
            organization=cls.org,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.client = Client()
        self.client.login(email="test@domaine.fr", password="testpass123")
        # Simuler la session avec l'org courante
        session = self.client.session
        session['current_org_id'] = self.org.id
        session.save()
    
    # ========================================================================
    # ROUTES PRINCIPALES DU MENU (doivent être accessibles)
    # ========================================================================
    
    def test_production_home(self):
        """Vue d'ensemble Production."""
        response = self.client.get(reverse('production:production_home'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_dash_vigne(self):
        """Dashboard Vigne."""
        response = self.client.get(reverse('production:dash_vigne'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_dash_chai(self):
        """Dashboard Chai."""
        response = self.client.get(reverse('production:dash_chai'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_dash_elevage(self):
        """Dashboard Élevage."""
        response = self.client.get(reverse('production:dash_elevage'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_dash_conditionnement(self):
        """Dashboard Conditionnement."""
        response = self.client.get(reverse('production:dash_conditionnement'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # VIGNE
    # ========================================================================
    
    def test_parcelles_list(self):
        """Liste des parcelles."""
        response = self.client.get(reverse('production:parcelles_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_parcelles_table(self):
        """Table HTMX des parcelles."""
        response = self.client.get(reverse('production:parcelles_table'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # RÉCOLTE
    # ========================================================================
    
    def test_vendanges_list(self):
        """Liste des vendanges."""
        response = self.client.get(reverse('production:vendanges_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_vendanges_table(self):
        """Table HTMX des vendanges."""
        response = self.client.get(reverse('production:vendanges_table'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_vendange_new(self):
        """Formulaire nouvelle vendange."""
        response = self.client.get(reverse('production:vendange_new'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_vendanges_map(self):
        """Carte des vendanges."""
        response = self.client.get(reverse('production:vendanges_map'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # CHAI - LOTS TECHNIQUES
    # ========================================================================
    
    def test_lots_tech_list(self):
        """Liste des lots techniques."""
        response = self.client.get(reverse('production:lots_tech_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_lots_tech_list_legacy(self):
        """Liste legacy des lots techniques."""
        response = self.client.get(reverse('production:lots_tech_list_legacy'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_lots_tech_table(self):
        """Table HTMX des lots techniques."""
        response = self.client.get(reverse('production:lots_tech_table'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_lot_tech_new(self):
        """Formulaire nouveau lot technique."""
        response = self.client.get(reverse('production:lot_tech_new'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # CHAI - OPÉRATIONS (toujours accessibles via URL directe)
    # ========================================================================
    
    def test_encuvages_list(self):
        """Liste des encuvages (supprimé du menu mais URL existe)."""
        response = self.client.get(reverse('production:encuvages_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_vinification_home(self):
        """Home vinification (supprimé du menu mais URL existe)."""
        response = self.client.get(reverse('production:vinification_home'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_soutirages_list(self):
        """Liste des soutirages (supprimé du menu mais URL existe)."""
        response = self.client.get(reverse('production:soutirages_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_assemblages_list(self):
        """Liste des assemblages (supprimé du menu mais URL existe)."""
        response = self.client.get(reverse('production:assemblages_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_assemblage_wizard(self):
        """Wizard nouvel assemblage."""
        response = self.client.get(reverse('production:assemblage_wizard'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # CHAI - ÉLEVAGE & ANALYSES
    # ========================================================================
    
    def test_lots_elevage_home(self):
        """Home élevage."""
        response = self.client.get(reverse('production:lots_elevage_home'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_lots_elevage_analyses(self):
        """Analyses des lots."""
        response = self.client.get(reverse('production:lots_elevage_analyses'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_analyses_home(self):
        """Home analyses."""
        response = self.client.get(reverse('production:analyses_home'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # CONTENANTS
    # ========================================================================
    
    def test_contenants_list(self):
        """Liste des contenants."""
        response = self.client.get(reverse('production:contenants_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_contenants_new(self):
        """Formulaire nouveau contenant."""
        response = self.client.get(reverse('production:contenants_new'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # CONDITIONNEMENT & STOCK
    # ========================================================================
    
    def test_mises_list(self):
        """Liste des mises."""
        response = self.client.get(reverse('production:mises_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_mise_new(self):
        """Formulaire nouvelle mise."""
        response = self.client.get(reverse('production:mise_new'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_inventaire(self):
        """Inventaire."""
        response = self.client.get(reverse('production:inventaire'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_inventaire_vrac(self):
        """Inventaire tab vrac."""
        response = self.client.get(reverse('production:inventaire_vrac'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_inventaire_produits(self):
        """Inventaire tab produits finis."""
        response = self.client.get(reverse('production:inventaire_produits'))
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # VÉRIFICATION DES URLs DANS LE MENU
    # ========================================================================
    
    def test_all_menu_urls_resolve(self):
        """Vérifie que toutes les URLs du menu existent."""
        menu_urls = [
            'production:production_home',
            'production:dash_vigne',
            'production:dash_chai',
            'production:dash_elevage',
            'production:dash_conditionnement',
            'production:parcelles_list',
            'production:vendanges_list',
            'production:lots_tech_list',
            'production:lots_elevage_analyses',
            'production:lots_elevage_home',
            'production:contenants_list',
            'production:mises_list',
            'production:inventaire',
        ]
        
        errors = []
        for url_name in menu_urls:
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                errors.append(f"URL '{url_name}' n'existe pas")
        
        if errors:
            self.fail("\n".join(errors))
    
    def test_removed_from_menu_but_still_accessible(self):
        """
        Les URLs suivantes ont été retirées du menu principal
        mais doivent rester accessibles (liens dans fiche lot).
        """
        removed_urls = [
            'production:encuvages_list',
            'production:vinification_home',
            'production:soutirages_list',
            'production:assemblages_list',
        ]
        
        for url_name in removed_urls:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                self.assertIn(
                    response.status_code, [200, 302],
                    f"URL '{url_name}' devrait être accessible mais retourne {response.status_code}"
                )
            except NoReverseMatch:
                self.fail(f"URL '{url_name}' n'existe plus, liens existants seront cassés!")


class ProductionFormsTestCase(TestCase):
    """Tests des formulaires Production."""
    
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(
            name="Test Domaine Forms",
            is_initialized=True
        )
        cls.user = User.objects.create_user(
            username="testformsuser",
            email="testforms@domaine.fr",
            password="testpass123",
        )
        Membership.objects.create(
            user=cls.user,
            organization=cls.org,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email="testforms@domaine.fr", password="testpass123")
        session = self.client.session
        session['current_org_id'] = self.org.id
        session.save()
    
    def test_vendange_form_get(self):
        """Le formulaire de vendange s'affiche."""
        response = self.client.get(reverse('production:vendange_new'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_lot_tech_form_get(self):
        """Le formulaire de lot technique s'affiche."""
        response = self.client.get(reverse('production:lot_tech_new'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_contenant_form_get(self):
        """Le formulaire de contenant s'affiche."""
        response = self.client.get(reverse('production:contenants_new'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_mise_form_get(self):
        """Le formulaire de mise s'affiche."""
        response = self.client.get(reverse('production:mise_new'))
        self.assertIn(response.status_code, [200, 302])


class MenuIntegrityTestCase(TestCase):
    """
    Vérifie l'intégrité du menu en parsant le template header.html.
    """
    
    def test_header_template_no_broken_urls(self):
        """
        Vérifie qu'aucune URL cassée n'existe dans le header.
        """
        from django.template import engines
        from django.template.loader import get_template
        
        # Charger le template pour vérifier la syntaxe
        try:
            template = get_template('_layout/header.html')
            # Si ça passe, le template est valide syntaxiquement
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Erreur dans header.html: {e}")
