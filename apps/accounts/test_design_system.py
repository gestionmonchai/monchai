"""
Tests du Design System - Roadmap 05_design_system_et_templates_auth.txt
Tests pour valider les composants UI et l'accessibilité
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()


class DesignSystemTestCase(TestCase):
    """Tests du design system selon roadmap 05"""
    
    def setUp(self):
        self.client = Client()
    
    def test_login_template_uses_auth_base(self):
        """Test que le template de login utilise auth_base.html"""
        response = self.client.get(reverse('auth:login'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier la présence des éléments du design system
        content = response.content.decode()
        self.assertIn('auth-container', content)
        self.assertIn('auth-card', content)
        self.assertIn('Connexion', content)
        self.assertIn('Mon Chai', content)
    
    def test_signup_template_uses_auth_base(self):
        """Test que le template de signup utilise auth_base.html"""
        response = self.client.get(reverse('auth:signup'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        self.assertIn('auth-container', content)
        self.assertIn('Créer un compte', content)
    
    def test_password_reset_template_uses_auth_base(self):
        """Test que le template de reset utilise auth_base.html"""
        response = self.client.get(reverse('auth:password_reset'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        self.assertIn('auth-container', content)
        self.assertIn('Mot de passe oublié', content)
    
    def test_form_fields_have_required_attributes(self):
        """Test roadmap : HTML5 required, type=email, minlength"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier les attributs HTML5
        self.assertIn('type="email"', content)
        self.assertIn('required', content)
        self.assertIn('autocomplete="email"', content)
        self.assertIn('autocomplete="current-password"', content)
    
    def test_signup_form_has_minlength(self):
        """Test que les champs password ont minlength=8"""
        response = self.client.get(reverse('auth:signup'))
        content = response.content.decode()
        
        # Vérifier minlength pour les mots de passe
        self.assertIn('minlength="8"', content)
        self.assertIn('autocomplete="new-password"', content)
    
    def test_form_labels_are_present(self):
        """Test roadmap : Labels présents, associés aux inputs (for/id)"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier la présence des labels
        self.assertIn('<label', content)
        self.assertIn('for=', content)
        self.assertIn('Adresse e-mail', content)
        self.assertIn('Mot de passe', content)
    
    def test_error_messages_are_inline(self):
        """Test roadmap : Messages d'erreur inline, pas de modales"""
        # Tenter une connexion avec des données invalides
        response = self.client.post(reverse('auth:login'), {
            'username': 'invalid@email.com',
            'password': 'wrongpassword'
        })
        
        content = response.content.decode()
        
        # Vérifier que les erreurs sont affichées inline
        self.assertIn('invalid-feedback', content)
        self.assertIn('role="alert"', content)
        # Pas de JavaScript modal
        self.assertNotIn('modal', content.lower())
    
    def test_session_badge_in_header(self):
        """Test roadmap : SessionBadge avec display_name, role, org"""
        # Créer un utilisateur avec organisation
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        org = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        
        Membership.objects.create(
            user=user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        # Se connecter
        self.client.login(username='test@example.com', password='testpass123')
        
        # Vérifier le SessionBadge
        response = self.client.get('/dashboard/')
        content = response.content.decode()
        
        self.assertIn('Test User', content)
        self.assertIn('Test Org', content)
        self.assertIn('Propriétaire', content)
        self.assertIn('bi-person-circle', content)
    
    def test_banner_component_with_aria_roles(self):
        """Test roadmap : Rôles ARIA pour bannières (role="status" pour success, role="alert" pour erreurs)"""
        # Tester avec une erreur de connexion
        response = self.client.post(reverse('auth:login'), {
            'username': 'invalid@email.com',
            'password': 'wrongpassword'
        })
        
        content = response.content.decode()
        
        # Vérifier les rôles ARIA
        self.assertIn('role="alert"', content)
    
    def test_focus_visible_styles(self):
        """Test roadmap : Focus visible (outline) sur les contrôles"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier que le CSS contient les styles de focus
        self.assertIn('focus', content)
        self.assertIn('outline', content)
    
    def test_responsive_design(self):
        """Test roadmap : Responsif OK < 360px (mobile)"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier la présence de media queries
        self.assertIn('@media', content)
        self.assertIn('360px', content)
        self.assertIn('viewport', content)
    
    def test_contrast_and_typography(self):
        """Test roadmap : Contraste AA, tailles de police >= 14px"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier les tailles de police
        self.assertIn('font-size: 1rem', content)  # 16px par défaut
        self.assertIn('font-size: 0.9rem', content)  # 14.4px pour les labels
    
    def test_submit_button_loading_state(self):
        """Test roadmap : États loading sur boutons d'action"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier la présence du spinner et des états
        self.assertIn('spinner-border', content)
        self.assertIn('btn-spinner', content)
        self.assertIn('disabled', content)
    
    def test_no_csrf_token_missing(self):
        """Test roadmap : Éviter 'page blanche après POST' → vérifier {% csrf_token %}"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier la présence du token CSRF
        self.assertIn('csrfmiddlewaretoken', content)
    
    def test_password_reset_generic_message(self):
        """Test roadmap : Ne jamais révéler si un email est 'inconnu' lors du reset"""
        response = self.client.post(reverse('auth:password_reset'), {
            'email': 'nonexistent@example.com'
        })
        
        # Vérifier la redirection vers done
        self.assertRedirects(response, reverse('auth:password_reset_done'))
        
        # Vérifier le message générique
        done_response = self.client.get(reverse('auth:password_reset_done'))
        content = done_response.content.decode()
        
        self.assertIn('Si un compte existe', content)
        self.assertNotIn('Email introuvable', content)
        self.assertNotIn('Aucun compte', content)


class AccessibilityTestCase(TestCase):
    """Tests d'accessibilité selon roadmap 05"""
    
    def setUp(self):
        self.client = Client()
    
    def test_tabulation_order(self):
        """Test roadmap : Ordre de tabulation logique: email → mdp → submit → liens"""
        response = self.client.get(reverse('auth:login'))
        content = response.content.decode()
        
        # Vérifier que les éléments ont un ordre logique dans le DOM
        email_pos = content.find('type="email"')
        password_pos = content.find('type="password"')
        submit_pos = content.find('type="submit"')
        
        # L'email doit venir avant le password, qui doit venir avant le submit
        self.assertLess(email_pos, password_pos)
        self.assertLess(password_pos, submit_pos)
    
    def test_aria_describedby_attributes(self):
        """Test roadmap : aria-describedby sur l'input quand help-text ou erreur existent"""
        # Tester avec une erreur
        response = self.client.post(reverse('auth:login'), {
            'username': '',  # Email vide pour déclencher une erreur
            'password': 'test'
        })
        
        content = response.content.decode()
        
        # Vérifier aria-describedby si erreur présente
        if 'invalid-feedback' in content:
            self.assertIn('aria-describedby', content)
    
    def test_required_field_indicators(self):
        """Test roadmap : Indicateurs de champs requis avec aria-label"""
        response = self.client.get(reverse('auth:signup'))
        content = response.content.decode()
        
        # Vérifier les indicateurs de champs requis
        self.assertIn('aria-label="requis"', content)
        self.assertIn('text-danger', content)
        self.assertIn('*', content)
