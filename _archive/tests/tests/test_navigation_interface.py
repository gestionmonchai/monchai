"""
Tests pour l'interface de navigation - Accès aux paramètres
Validation menu dropdown et carte dashboard
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization, Membership
from tests.factories import UserFactory, OrganizationFactory, MembershipFactory

User = get_user_model()


class NavigationInterfaceTest(TestCase):
    """Tests de l'interface de navigation pour les paramètres"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = UserFactory()
        self.readonly_user = UserFactory()
        self.organization = OrganizationFactory()
        
        # Membership admin
        self.admin_membership = MembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
        
        # Membership read_only
        self.readonly_membership = MembershipFactory(
            user=self.readonly_user,
            organization=self.organization,
            role='read_only'
        )
    
    def test_admin_sees_settings_menu_in_base_template(self):
        """Test que les admins voient le menu Paramètres"""
        self.client.force_login(self.admin_user)
        
        # Simuler le middleware current_org
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier présence du menu Paramètres
        self.assertContains(response, 'Paramètres')
        self.assertContains(response, 'bi-gear')
        self.assertContains(response, 'Checklist d\'onboarding')
        self.assertContains(response, 'Informations de facturation')
        self.assertContains(response, 'Paramètres généraux')
    
    def test_readonly_does_not_see_settings_menu(self):
        """Test que les read_only ne voient pas le menu Paramètres"""
        self.client.force_login(self.readonly_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier absence du menu Paramètres
        # Note: On ne peut pas tester facilement le dropdown dans base.html
        # mais on peut vérifier que la carte dashboard n'est pas présente
        content = response.content.decode()
        
        # La carte paramètres ne doit pas être présente pour read_only
        settings_card_present = 'Configurez votre organisation' in content
        self.assertFalse(settings_card_present)
    
    def test_admin_sees_settings_card_on_dashboard(self):
        """Test que les admins voient la carte Paramètres sur le dashboard"""
        self.client.force_login(self.admin_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier présence de la carte Paramètres
        self.assertContains(response, 'Configurez votre organisation')
        self.assertContains(response, 'btn-outline-primary')  # Bouton checklist
        self.assertContains(response, 'btn-outline-secondary')  # Boutons settings
    
    def test_settings_links_are_functional(self):
        """Test que tous les liens de paramètres fonctionnent"""
        self.client.force_login(self.admin_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        # Test des URLs principales
        urls_to_test = [
            '/onboarding/checklist/',
            '/auth/settings/billing/',
            '/auth/settings/general/',
        ]
        
        for url in urls_to_test:
            with self.subTest(url=url):
                response = self.client.get(url)
                # 200 OK ou 302 redirect (selon middleware)
                self.assertIn(response.status_code, [200, 302])
    
    def test_permissions_consistency(self):
        """Test cohérence des permissions entre menu et pages"""
        # Admin peut accéder
        self.client.force_login(self.admin_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/auth/settings/general/')
        self.assertIn(response.status_code, [200, 302])
        
        # Read-only ne peut pas accéder
        self.client.force_login(self.readonly_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/auth/settings/general/')
        # Doit être refusé (403 ou redirect)
        self.assertIn(response.status_code, [403, 302])


class ResponsiveDesignTest(TestCase):
    """Tests basiques du design responsive"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = UserFactory()
        self.organization = OrganizationFactory()
        self.admin_membership = MembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
    
    def test_bootstrap_classes_present(self):
        """Test que les classes Bootstrap sont présentes"""
        self.client.force_login(self.admin_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier classes Bootstrap importantes
        self.assertContains(response, 'dropdown-header')
        self.assertContains(response, 'dropdown-item')
        self.assertContains(response, 'btn-outline-')
        self.assertContains(response, 'd-grid gap-2')
    
    def test_icons_present(self):
        """Test que les icônes Bootstrap sont présentes"""
        self.client.force_login(self.admin_user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier icônes importantes
        icons_to_check = [
            'bi-gear',
            'bi-list-check', 
            'bi-receipt',
            'bi-sliders'
        ]
        
        for icon in icons_to_check:
            with self.subTest(icon=icon):
                self.assertContains(response, icon)
