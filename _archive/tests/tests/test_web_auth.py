"""
Tests d'authentification web - Sprint 08
Tests selon roadmap 08: signup, login, logout, reset
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.messages import get_messages

from .factories import UserFactory, OrganizationFactory, MembershipFactory

User = get_user_model()


@pytest.mark.django_db
class TestSignupFlow:
    """Tests du flux d'inscription"""
    
    def test_signup_get_displays_form(self):
        """Test affichage du formulaire d'inscription"""
        client = Client()
        response = client.get(reverse('auth:signup'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'Créer un compte' in response.content.decode()
    
    def test_signup_valid_creates_user_and_redirects_first_run(self):
        """Test signup valide → création utilisateur + redirection first-run"""
        client = Client()
        
        data = {
            'email': 'newuser@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = client.post(reverse('auth:signup'), data)
        
        # Vérifier redirection (first-run guard)
        assert response.status_code == 302
        
        # Vérifier création utilisateur
        user = User.objects.get(email='newuser@test.com')
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('complexpass123')
        
        # Vérifier connexion automatique
        assert '_auth_user_id' in client.session
    
    def test_signup_with_invitation_creates_membership(self):
        """Test signup avec invitation en session → membership créé"""
        client = Client()
        organization = OrganizationFactory()
        
        # Simuler invitation en session
        session = client.session
        session['invitation_payload'] = {
            'email': 'invited@test.com',
            'organization_id': organization.id,
            'organization_name': organization.name,
            'role': 'editor',
            'role_display': 'Éditeur',
            'invitation_id': 123
        }
        session.save()
        
        data = {
            'email': 'invited@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = client.post(reverse('auth:signup'), data)
        
        # Vérifier création membership
        user = User.objects.get(email='invited@test.com')
        membership = user.memberships.filter(organization=organization).first()
        assert membership is not None
        assert membership.role == 'editor'
        
        # Vérifier nettoyage session
        assert 'invitation_payload' not in client.session
    
    def test_signup_invalid_email_shows_error(self):
        """Test signup avec email invalide → erreur"""
        client = Client()
        
        data = {
            'email': 'invalid-email',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = client.post(reverse('auth:signup'), data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestLoginFlow:
    """Tests du flux de connexion"""
    
    def test_login_get_displays_form(self):
        """Test affichage du formulaire de connexion"""
        client = Client()
        response = client.get(reverse('auth:login'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'Connexion' in response.content.decode()
    
    def test_login_valid_credentials_redirects(self):
        """Test connexion avec identifiants valides → redirection"""
        user = UserFactory(email='test@example.com')
        client = Client()
        
        data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = client.post(reverse('auth:login'), data)
        
        assert response.status_code == 302
        assert '_auth_user_id' in client.session
    
    def test_login_invalid_credentials_shows_error(self):
        """Test connexion avec identifiants invalides → message d'erreur"""
        UserFactory(email='test@example.com')
        client = Client()
        
        data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post(reverse('auth:login'), data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert 'Email ou mot de passe incorrect' in response.content.decode()
    
    def test_login_inactive_user_shows_error(self):
        """Test connexion avec utilisateur inactif → erreur"""
        user = UserFactory(email='inactive@example.com', is_active=False)
        client = Client()
        
        data = {
            'username': 'inactive@example.com',
            'password': 'testpass123'
        }
        
        response = client.post(reverse('auth:login'), data)
        
        assert response.status_code == 200
        assert 'Ce compte a été désactivé' in response.content.decode()


@pytest.mark.django_db
class TestLogoutFlow:
    """Tests du flux de déconnexion"""
    
    def test_logout_destroys_session(self):
        """Test logout détruit la session"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        # Vérifier connexion
        assert '_auth_user_id' in client.session
        
        response = client.post(reverse('auth:logout'))
        
        # Vérifier redirection
        assert response.status_code == 302
        
        # Vérifier destruction session
        assert '_auth_user_id' not in client.session
    
    def test_logout_redirects_to_login(self):
        """Test logout redirige vers login"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        response = client.post(reverse('auth:logout'))
        
        assert response.status_code == 302
        assert response.url == reverse('auth:login')


@pytest.mark.django_db
class TestPasswordResetFlow:
    """Tests du flux de réinitialisation mot de passe"""
    
    def test_password_reset_request_valid_email_sends_mail(self):
        """Test demande reset avec email valide → email envoyé"""
        user = UserFactory(email='reset@example.com')
        client = Client()
        
        data = {'email': 'reset@example.com'}
        response = client.post(reverse('auth:password_reset'), data)
        
        # Vérifier redirection vers page "done"
        assert response.status_code == 302
        assert reverse('auth:password_reset_done') in response.url
        
        # Vérifier email envoyé
        assert len(mail.outbox) == 1
        assert 'reset@example.com' in mail.outbox[0].to
    
    def test_password_reset_request_invalid_email_still_shows_success(self):
        """Test demande reset avec email inexistant → succès apparent (sécurité)"""
        client = Client()
        
        data = {'email': 'nonexistent@example.com'}
        response = client.post(reverse('auth:password_reset'), data)
        
        # Vérifier redirection vers page "done" (ne pas révéler si email existe)
        assert response.status_code == 302
        assert reverse('auth:password_reset_done') in response.url
        
        # Vérifier aucun email envoyé
        assert len(mail.outbox) == 0
    
    def test_password_reset_done_displays_message(self):
        """Test page reset done affiche message"""
        client = Client()
        response = client.get(reverse('auth:password_reset_done'))
        
        assert response.status_code == 200
        assert 'email' in response.content.decode().lower()


@pytest.mark.django_db
class TestAuthenticationRedirects:
    """Tests des redirections d'authentification"""
    
    def test_authenticated_user_redirected_from_login(self):
        """Test utilisateur connecté redirigé depuis login"""
        user = UserFactory()
        membership = MembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:login'))
        
        assert response.status_code == 302
    
    def test_authenticated_user_redirected_from_signup(self):
        """Test utilisateur connecté redirigé depuis signup"""
        user = UserFactory()
        membership = MembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:signup'))
        
        assert response.status_code == 302
