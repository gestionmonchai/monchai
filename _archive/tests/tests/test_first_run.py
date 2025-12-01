"""
Tests du first-run guard - Sprint 08
Tests selon roadmap 08: sans membership → guard, POST valide → crée Organization + Membership
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization, Membership
from .factories import UserFactory, OrganizationFactory, MembershipFactory

User = get_user_model()


@pytest.mark.django_db
class TestFirstRunGuard:
    """Tests du garde first-run"""
    
    def test_user_without_membership_redirected_to_first_run(self):
        """Test utilisateur sans membership → redirection first-run"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        # Tenter d'accéder à une page protégée
        response = client.get('/dashboard/')  # URL qui nécessite membership
        
        # Vérifier redirection vers first-run
        assert response.status_code == 302
        assert reverse('auth:first_run') in response.url
    
    def test_user_with_membership_accesses_protected_pages(self):
        """Test utilisateur avec membership → accès aux pages protégées"""
        user = UserFactory()
        membership = MembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        # Accéder à une page protégée
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier accès autorisé (pas de redirection first-run)
        assert response.status_code in [200, 403]  # 403 si pas admin, mais pas redirection first-run
    
    def test_first_run_page_displays_organization_form(self):
        """Test page first-run affiche formulaire organisation"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:first_run'))
        
        assert response.status_code == 200
        assert 'Créer votre exploitation' in response.content.decode()
    
    def test_first_run_redirects_to_create_org_form(self):
        """Test first-run redirige vers formulaire création organisation"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:first_run'))
        
        # Vérifier redirection vers formulaire création
        assert response.status_code == 302
        assert reverse('auth:create_organization') in response.url


@pytest.mark.django_db
class TestOrganizationCreation:
    """Tests de création d'organisation"""
    
    def test_create_organization_get_displays_form(self):
        """Test GET création organisation affiche formulaire"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:create_organization'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'Créer votre exploitation' in response.content.decode()
    
    def test_create_organization_valid_post_creates_org_and_membership(self):
        """Test POST valide → crée Organization + Membership owner"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        data = {
            'name': 'Mon Exploitation Test',
            'siret': '12345678901234',
            'tva_number': 'FR12345678901',
            'currency': 'EUR'
        }
        
        response = client.post(reverse('auth:create_organization'), data)
        
        # Vérifier redirection après création
        assert response.status_code == 302
        
        # Vérifier création organisation
        organization = Organization.objects.get(name='Mon Exploitation Test')
        assert organization.siret == '12345678901234'
        assert organization.tva_number == 'FR12345678901'
        assert organization.currency == 'EUR'
        assert organization.is_initialized is True
        
        # Vérifier création membership owner
        membership = Membership.objects.get(user=user, organization=organization)
        assert membership.role == Membership.Role.OWNER
        assert membership.is_active is True
    
    def test_create_organization_invalid_siret_shows_error(self):
        """Test création organisation avec SIRET invalide → erreur"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        data = {
            'name': 'Mon Exploitation Test',
            'siret': '123',  # SIRET invalide
            'currency': 'EUR'
        }
        
        response = client.post(reverse('auth:create_organization'), data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert 'SIRET' in str(response.context['form'].errors)
    
    def test_create_organization_empty_name_shows_error(self):
        """Test création organisation sans nom → erreur"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        data = {
            'name': '',  # Nom vide
            'currency': 'EUR'
        }
        
        response = client.post(reverse('auth:create_organization'), data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
    
    def test_user_with_existing_membership_cannot_create_organization(self):
        """Test utilisateur avec membership existant ne peut pas créer organisation"""
        user = UserFactory()
        membership = MembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        # Tenter d'accéder à la création d'organisation
        response = client.get(reverse('auth:create_organization'))
        
        # Vérifier redirection (utilisateur a déjà une organisation)
        assert response.status_code == 302
    
    def test_anonymous_user_redirected_to_login(self):
        """Test utilisateur anonyme redirigé vers login"""
        client = Client()
        
        response = client.get(reverse('auth:create_organization'))
        
        assert response.status_code == 302
        assert reverse('auth:login') in response.url


@pytest.mark.django_db
class TestFirstRunIntegration:
    """Tests d'intégration du flux first-run complet"""
    
    def test_complete_first_run_flow(self):
        """Test flux complet: signup → first-run → création org → accès dashboard"""
        client = Client()
        
        # 1. Signup
        signup_data = {
            'email': 'newuser@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        response = client.post(reverse('auth:signup'), signup_data)
        assert response.status_code == 302
        
        # 2. First-run (redirection automatique)
        response = client.get(reverse('auth:first_run'))
        assert response.status_code == 302
        assert reverse('auth:create_organization') in response.url
        
        # 3. Création organisation
        org_data = {
            'name': 'Nouvelle Exploitation',
            'currency': 'EUR'
        }
        response = client.post(reverse('auth:create_organization'), org_data)
        assert response.status_code == 302
        
        # 4. Vérifier que l'utilisateur peut maintenant accéder aux pages protégées
        user = User.objects.get(email='newuser@test.com')
        assert user.memberships.count() == 1
        
        membership = user.memberships.first()
        assert membership.role == Membership.Role.OWNER
        assert membership.organization.name == 'Nouvelle Exploitation'
