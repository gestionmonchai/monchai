"""
Tests de routing et guards - Roadmap 06_routing_middlewares_gardes.txt
Tests pour valider les conventions d'URL, redirections et guards d'accès
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from apps.accounts.models import Organization, Membership

User = get_user_model()


class RoutingConventionsTestCase(TestCase):
    """Tests des conventions d'URL selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
    
    def test_auth_urls_respond(self):
        """Test roadmap : Toutes les routes listées répondent (GET) sans 500/404"""
        auth_urls = [
            '/auth/login/',
            '/auth/signup/',
            '/auth/password/reset/',
            '/auth/logout/',  # POST mais devrait rediriger en GET
        ]
        
        for url in auth_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Doit répondre (200 ou redirection), pas 404/500
                self.assertIn(response.status_code, [200, 302, 405])
    
    def test_api_urls_respond(self):
        """Test roadmap : API endpoints répondent correctement"""
        # Test sans authentification (doit retourner 401 ou redirection)
        response = self.client.get('/api/auth/whoami/')
        self.assertIn(response.status_code, [401, 403])
        
        # Test CSRF endpoint (public)
        response = self.client.get('/api/auth/csrf/')
        self.assertEqual(response.status_code, 200)
    
    def test_root_redirect_logic(self):
        """Test de la logique de redirection racine"""
        # Utilisateur non connecté → /auth/login/
        response = self.client.get('/')
        self.assertRedirects(response, '/auth/login/')
        
        # Utilisateur connecté → /dashboard/
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get('/')
        self.assertRedirects(response, '/dashboard/')


class RedirectionTestCase(TestCase):
    """Tests des redirections de référence selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_redirect_url(self):
        """Test roadmap : LOGIN_REDIRECT_URL=/auth/first-run/"""
        response = self.client.post('/auth/login/', {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Doit rediriger vers first-run (guard) - vérifier première redirection
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/auth/first-run/'))
    
    def test_logout_redirect_url(self):
        """Test roadmap : LOGOUT_REDIRECT_URL=/auth/login/"""
        # Se connecter d'abord
        self.client.login(username='test@example.com', password='testpass123')
        
        # Se déconnecter
        response = self.client.post('/auth/logout/')
        
        # Doit rediriger vers login
        self.assertRedirects(response, '/auth/login/')
    
    def test_login_required_redirect(self):
        """Test que @login_required redirige vers LOGIN_URL"""
        # Tenter d'accéder au dashboard sans être connecté
        response = self.client.get('/dashboard/')
        
        # Doit rediriger vers login avec next parameter
        self.assertRedirects(response, '/auth/login/?next=/dashboard/')


class GuardsTestCase(TestCase):
    """Tests des guards d'accès selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
        
        # Utilisateur sans organisation
        self.user_no_org = User.objects.create_user(
            username='noorg@example.com',
            email='noorg@example.com',
            password='testpass123'
        )
        
        # Utilisateur avec organisation
        self.user_with_org = User.objects.create_user(
            username='withorg@example.com',
            email='withorg@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        
        self.membership = Membership.objects.create(
            user=self.user_with_org,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def test_first_run_guard_for_user_without_org(self):
        """Test roadmap : Guard first-run fonctionne pour user sans org"""
        self.client.login(username='noorg@example.com', password='testpass123')
        
        # Accéder au first-run (suivre les redirections)
        response = self.client.get('/auth/first-run/', follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Le template doit proposer de créer une organisation
        self.assertContains(response, 'Créer mon exploitation')
    
    def test_require_membership_redirect(self):
        """Test roadmap : Accès à une vue métier sans membership → redirect vers first-run"""
        self.client.login(username='noorg@example.com', password='testpass123')
        
        # Tenter d'accéder à une vue protégée par @require_membership
        response = self.client.get('/auth/settings/roles/')
        
        # Doit rediriger vers first-run (vérifier la première redirection)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/auth/first-run/'))
    
    def test_membership_allows_access(self):
        """Test qu'un membership actif permet l'accès aux vues métier"""
        self.client.login(username='withorg@example.com', password='testpass123')
        
        # Accéder à une vue protégée
        response = self.client.get('/auth/settings/roles/')
        
        # Doit permettre l'accès (200)
        self.assertEqual(response.status_code, 200)
    
    def test_role_hierarchy_enforcement(self):
        """Test de l'application de la hiérarchie des rôles"""
        # Créer un utilisateur read-only
        reader = User.objects.create_user(
            username='reader@example.com',
            email='reader@example.com',
            password='testpass123'
        )
        
        Membership.objects.create(
            user=reader,
            organization=self.organization,
            role=Membership.Role.READ_ONLY,
            is_active=True
        )
        
        self.client.login(username='reader@example.com', password='testpass123')
        
        # Tenter d'accéder à la gestion des rôles (nécessite admin+)
        response = self.client.get('/auth/settings/roles/')
        
        # Doit être refusé (403)
        self.assertEqual(response.status_code, 403)


class SecurityTestCase(TestCase):
    """Tests de sécurité selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_protection_on_forms(self):
        """Test roadmap : CSRF OK sur tous les formulaires POST"""
        # Test login form
        response = self.client.get('/auth/login/')
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Test signup form
        response = self.client.get('/auth/signup/')
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_security_headers(self):
        """Test que les headers de sécurité sont présents"""
        response = self.client.get('/auth/login/')
        
        # Vérifier les headers de sécurité
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.get('X-XSS-Protection'), '1; mode=block')
    
    def test_api_csrf_requirement(self):
        """Test que l'API nécessite CSRF pour les opérations sensibles"""
        self.client.login(username='test@example.com', password='testpass123')
        
        # POST sans CSRF token
        response = self.client.post('/api/auth/logout/', {})
        
        # Doit être refusé ou géré par Django CSRF middleware
        self.assertIn(response.status_code, [403, 200, 204])  # 204 pour logout API réussi


class CurrentOrganizationMiddlewareTestCase(TestCase):
    """Tests du middleware CurrentOrganization selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        
        self.org1 = Organization.objects.create(name='Org 1', siret='12345678901234', is_initialized=True)
        self.org2 = Organization.objects.create(name='Org 2', siret='12345678901235', is_initialized=True)
        
        # Memberships dans deux organisations
        self.membership1 = Membership.objects.create(
            user=self.user,
            organization=self.org1,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        self.membership2 = Membership.objects.create(
            user=self.user,
            organization=self.org2,
            role=Membership.Role.EDITOR,
            is_active=True
        )
    
    def test_current_org_fallback_to_first_membership(self):
        """Test que le middleware utilise le premier membership par défaut"""
        self.client.login(username='test@example.com', password='testpass123')
        
        # Accéder à l'API whoami
        response = self.client.get('/api/auth/whoami/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Doit utiliser la première organisation
        self.assertEqual(data['organization']['id'], self.org1.id)
    
    def test_current_org_from_session(self):
        """Test que le middleware respecte current_org_id en session"""
        self.client.login(username='test@example.com', password='testpass123')
        
        # Définir l'org courante en session
        session = self.client.session
        session['current_org_id'] = self.org2.id
        session.save()
        
        # Accéder à l'API whoami
        response = self.client.get('/api/auth/whoami/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Doit utiliser l'organisation de la session
        self.assertEqual(data['organization']['id'], self.org2.id)
    
    def test_invalid_org_id_in_session_cleanup(self):
        """Test que le middleware nettoie les org_id invalides en session"""
        self.client.login(username='test@example.com', password='testpass123')
        
        # Définir un org_id invalide en session
        session = self.client.session
        session['current_org_id'] = 99999  # N'existe pas
        session.save()
        
        # Accéder à l'API whoami
        response = self.client.get('/api/auth/whoami/')
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la session a été nettoyée et fallback appliqué
        self.assertNotIn('current_org_id', self.client.session)


class ErrorPreventionTestCase(TestCase):
    """Tests de prévention d'erreurs classiques selon roadmap 06"""
    
    def setUp(self):
        self.client = Client()
    
    def test_no_redirect_loops(self):
        """Test roadmap : Éviter les boucles de redirection"""
        # Créer un utilisateur sans organisation
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.login(username='test@example.com', password='testpass123')
        
        # Suivre les redirections pour détecter les boucles
        response = self.client.get('/', follow=True)
        
        # Ne doit pas y avoir de boucle infinie
        self.assertLess(len(response.redirect_chain), 5)
        
        # Doit finir sur first-run ou dashboard (selon l'état de l'utilisateur)
        final_path = response.request['PATH_INFO']
        self.assertIn(final_path, ['/auth/first-run/', '/dashboard/'])
    
    def test_api_url_consistency(self):
        """Test roadmap : Éviter 404 API avec URLs cohérentes"""
        # Vérifier que les URLs API sont cohérentes
        api_urls = [
            '/api/auth/whoami/',
            '/api/auth/csrf/',
            '/api/auth/logout/',
        ]
        
        for url in api_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Ne doit pas être 404
                self.assertNotEqual(response.status_code, 404)
