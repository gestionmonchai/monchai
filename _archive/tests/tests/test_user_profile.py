"""
Tests pour le profil utilisateur - Roadmap 10
Tests du modèle UserProfile, signal, vues et formulaires
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages

from apps.accounts.models import UserProfile
from apps.accounts.utils import get_display_name
from tests.factories import UserFactory, AdminMembershipFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileModel:
    """Tests du modèle UserProfile"""
    
    def test_profile_creation_with_signal(self):
        """Test création automatique du profil via signal"""
        user = UserFactory()
        
        # Vérifier que le profil a été créé automatiquement
        assert hasattr(user, 'profile')
        profile = user.profile
        assert profile.locale == 'fr'
        assert profile.timezone == 'Europe/Paris'
        assert profile.display_name == ''
    
    def test_get_display_name_with_display_name(self):
        """Test get_display_name avec display_name défini"""
        user = UserFactory()
        profile = user.profile
        profile.display_name = 'Jean Dupont'
        profile.save()
        
        assert profile.get_display_name() == 'Jean Dupont'
    
    def test_get_display_name_with_first_last_name(self):
        """Test get_display_name avec first_name et last_name"""
        user = UserFactory(first_name='Marie', last_name='Martin')
        profile = user.profile
        
        assert profile.get_display_name() == 'Marie Martin'
    
    def test_get_display_name_with_first_name_only(self):
        """Test get_display_name avec first_name seulement"""
        user = UserFactory(first_name='Pierre', last_name='')
        profile = user.profile
        
        assert profile.get_display_name() == 'Pierre'
    
    def test_get_display_name_fallback_to_email(self):
        """Test get_display_name fallback vers email"""
        user = UserFactory(first_name='', last_name='')
        profile = user.profile
        
        assert profile.get_display_name() == user.email
    
    def test_get_avatar_url_without_avatar(self):
        """Test get_avatar_url sans avatar"""
        user = UserFactory()
        profile = user.profile
        
        assert profile.get_avatar_url() is None
    
    def test_timezone_choices(self):
        """Test liste des fuseaux horaires"""
        choices = UserProfile.get_timezone_choices()
        
        assert len(choices) == 10
        assert ('Europe/Paris', 'Paris (Europe/Paris)') in choices
        assert ('America/New_York', 'New York (America/New_York)') in choices


@pytest.mark.django_db
class TestGetDisplayNameUtility:
    """Tests de l'utilitaire get_display_name"""
    
    def test_get_display_name_with_profile(self):
        """Test get_display_name avec profil"""
        user = UserFactory()
        user.profile.display_name = 'Test User'
        user.profile.save()
        
        assert get_display_name(user) == 'Test User'
    
    def test_get_display_name_fallback_without_profile(self):
        """Test get_display_name fallback sans profil (ne devrait pas arriver)"""
        user = UserFactory(first_name='', last_name='')
        # Supprimer le profil pour tester le fallback
        user.profile.delete()
        
        # Devrait utiliser le fallback
        result = get_display_name(user)
        assert result == user.email  # Car first_name et last_name sont vides


@pytest.mark.django_db
class TestProfileViews:
    """Tests des vues de profil"""
    
    def test_profile_view_get_anonymous_redirected(self):
        """Test redirection utilisateur anonyme"""
        client = Client()
        response = client.get(reverse('auth:profile'))
        
        assert response.status_code == 302
        assert '/auth/login/' in response.url
    
    def test_profile_view_get_authenticated(self):
        """Test accès page profil utilisateur connecté"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        
        client = Client()
        client.force_login(user)
        response = client.get(reverse('auth:profile'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'profile' in response.context
        assert response.context['profile'] == user.profile
    
    def test_profile_view_form_fields_populated(self):
        """Test champs formulaire pré-remplis"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        profile = user.profile
        profile.display_name = 'Test User'
        profile.locale = 'en'
        profile.timezone = 'America/New_York'
        profile.save()
        
        client = Client()
        client.force_login(user)
        response = client.get(reverse('auth:profile'))
        
        form = response.context['form']
        assert form.initial['display_name'] == 'Test User'
        assert form.initial['locale'] == 'en'
        assert form.initial['timezone'] == 'America/New_York'
    
    def test_profile_view_post_valid_data(self):
        """Test POST avec données valides"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        
        client = Client()
        client.force_login(user)
        
        data = {
            'display_name': 'Nouveau Nom',
            'locale': 'en',
            'timezone': 'America/Los_Angeles'
        }
        
        response = client.post(reverse('auth:profile'), data)
        
        # Vérifier redirection
        assert response.status_code == 302
        assert response.url == reverse('auth:profile')
        
        # Vérifier sauvegarde
        user.profile.refresh_from_db()
        assert user.profile.display_name == 'Nouveau Nom'
        assert user.profile.locale == 'en'
        assert user.profile.timezone == 'America/Los_Angeles'
        
        # Vérifier message de succès
        response = client.get(reverse('auth:profile'))
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Profil mis à jour avec succès' in str(messages[0])
    
    def test_profile_view_post_invalid_avatar_size(self):
        """Test POST avec avatar trop volumineux"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        
        client = Client()
        client.force_login(user)
        
        # Créer une image JPEG valide mais trop volumineuse (simulée)
        # En-tête JPEG minimal + données
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
        large_content = jpeg_header + b"x" * (3 * 1024 * 1024 - len(jpeg_header))  # 3 Mo total
        
        large_file = SimpleUploadedFile(
            "large_avatar.jpg",
            large_content,
            content_type="image/jpeg"
        )
        
        data = {
            'display_name': 'Test',
            'locale': 'fr',
            'timezone': 'Europe/Paris',
            'avatar': large_file
        }
        
        response = client.post(reverse('auth:profile'), data)
        
        # Vérifier erreur de validation
        assert response.status_code == 200
        form = response.context['form']
        assert 'avatar' in form.errors
        # Vérifier qu'il y a une erreur (peu importe le message exact)
        assert len(form.errors['avatar']) > 0
    
    def test_profile_view_post_invalid_avatar_format(self):
        """Test POST avec format d'avatar invalide"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        
        client = Client()
        client.force_login(user)
        
        # Créer un fichier avec mauvais format
        invalid_file = SimpleUploadedFile(
            "avatar.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        data = {
            'display_name': 'Test',
            'locale': 'fr',
            'timezone': 'Europe/Paris',
            'avatar': invalid_file
        }
        
        response = client.post(reverse('auth:profile'), data)
        
        # Vérifier erreur de validation
        assert response.status_code == 200
        form = response.context['form']
        assert 'avatar' in form.errors
        # Vérifier qu'il y a une erreur (peu importe le message exact)
        assert len(form.errors['avatar']) > 0
    
    def test_profile_view_post_empty_display_name(self):
        """Test POST avec display_name vide (valide)"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        
        client = Client()
        client.force_login(user)
        
        data = {
            'display_name': '',
            'locale': 'fr',
            'timezone': 'Europe/Paris'
        }
        
        response = client.post(reverse('auth:profile'), data)
        
        # Vérifier succès
        assert response.status_code == 302
        
        # Vérifier sauvegarde
        user.profile.refresh_from_db()
        assert user.profile.display_name == ''
        # Le fallback dépend de si l'utilisateur a des first_name/last_name
        display_name = user.profile.get_display_name()
        assert display_name in [user.email, f"{user.first_name} {user.last_name}".strip()]


@pytest.mark.django_db
class TestProfileForm:
    """Tests du formulaire UserProfileForm"""
    
    def test_form_required_fields(self):
        """Test champs requis du formulaire"""
        from apps.accounts.forms import UserProfileForm
        
        form = UserProfileForm()
        
        # locale et timezone sont requis selon roadmap 10
        assert form.fields['locale'].required is True
        assert form.fields['timezone'].required is True
        assert form.fields['display_name'].required is False
        assert form.fields['avatar'].required is False
    
    def test_form_timezone_choices(self):
        """Test choix de fuseaux horaires"""
        from apps.accounts.forms import UserProfileForm
        
        form = UserProfileForm()
        choices = form.fields['timezone'].choices
        
        assert len(choices) == 10
        assert ('Europe/Paris', 'Paris (Europe/Paris)') in choices
    
    def test_form_clean_display_name_too_long(self):
        """Test validation display_name trop long"""
        from apps.accounts.forms import UserProfileForm
        
        user = UserFactory()
        profile = user.profile
        
        data = {
            'display_name': 'x' * 101,  # Plus de 100 caractères
            'locale': 'fr',
            'timezone': 'Europe/Paris'
        }
        
        form = UserProfileForm(data, instance=profile)
        assert not form.is_valid()
        assert 'display_name' in form.errors
        assert '100 caractères' in str(form.errors['display_name'])
    
    def test_form_valid_data(self):
        """Test formulaire avec données valides"""
        from apps.accounts.forms import UserProfileForm
        
        user = UserFactory()
        profile = user.profile
        
        data = {
            'display_name': 'Test User',
            'locale': 'en',
            'timezone': 'America/New_York'
        }
        
        form = UserProfileForm(data, instance=profile)
        assert form.is_valid()
        
        saved_profile = form.save()
        assert saved_profile.display_name == 'Test User'
        assert saved_profile.locale == 'en'
        assert saved_profile.timezone == 'America/New_York'
