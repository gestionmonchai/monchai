"""
Tests d'authentification pour Mon Chai.
Implémentation selon roadmap 02_auth_flow.txt
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.messages import get_messages

from .models import User, Organization, Membership

User = get_user_model()


class AuthFlowTestCase(TestCase):
    """Tests du flux d'authentification selon roadmap 02_auth_flow.txt"""
    
    def setUp(self):
        self.client = Client()
        self.test_email = 'test@example.com'
        self.test_password = 'testpass123'
        
    def test_signup_success_redirect_first_run(self):
        """
        Test roadmap : Signup → redirection vers first-run guard
        """
        response = self.client.post(reverse('auth:signup'), {
            'email': self.test_email,
            'first_name': 'Test',
            'last_name': 'User',
            'password1': self.test_password,
            'password2': self.test_password,
        })
        
        # Vérifier que l'utilisateur est créé
        self.assertTrue(User.objects.filter(email=self.test_email).exists())
        
        # Vérifier la redirection vers first-run (qui redirige maintenant vers org creation)
        self.assertRedirects(response, '/auth/first-run/', fetch_redirect_response=False)
        
        # Vérifier que l'utilisateur est connecté
        user = User.objects.get(email=self.test_email)
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_failure_shows_error_message(self):
        """
        Test roadmap : Login échec → message "identifiants invalides" affiché
        """
        response = self.client.post(reverse('auth:login'), {
            'username': 'nonexistent@example.com',
            'password': 'wrongpassword',
        })
        
        # Vérifier que la page de login est affichée avec erreur
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email ou mot de passe incorrect')
    
    def test_login_success_redirect_first_run(self):
        """
        Test login réussi avec redirection vers first-run
        """
        # Créer un utilisateur
        user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password,
            first_name='Test'
        )
        
        response = self.client.post(reverse('auth:login'), {
            'username': self.test_email,
            'password': self.test_password,
        })
        
        # Vérifier la redirection vers first-run (qui redirige maintenant vers org creation)
        self.assertRedirects(response, '/auth/first-run/', fetch_redirect_response=False)
    
    def test_password_reset_sends_email_console(self):
        """
        Test roadmap : Reset POST request → email console
        """
        # Créer un utilisateur
        user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password
        )
        
        response = self.client.post(reverse('auth:password_reset'), {
            'email': self.test_email,
        })
        
        # Vérifier la redirection vers done
        self.assertRedirects(response, reverse('auth:password_reset_done'))
        
        # Vérifier qu'un email a été envoyé (console backend)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Réinitialisation', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.test_email])
    
    def test_logout_destroys_session_shows_message(self):
        """
        Test roadmap : Logout session détruite → plus de badge de session
        """
        # Créer et connecter un utilisateur
        user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password
        )
        self.client.login(username=self.test_email, password=self.test_password)
        
        # Vérifier que l'utilisateur est connecté
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Se déconnecter
        response = self.client.post(reverse('auth:logout'))
        
        # Vérifier la redirection vers login
        self.assertRedirects(response, '/auth/login/')
        
        # Vérifier que la session est détruite
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_first_run_guard_no_membership(self):
        """
        Test du first-run guard sans membership
        """
        user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password
        )
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.get(reverse('auth:first_run'))
        
        # Vérifier la redirection vers création d'organisation
        self.assertRedirects(response, '/auth/first-run/org/')
    
    def test_first_run_guard_with_membership_redirects_dashboard(self):
        """
        Test du first-run guard avec membership actif
        """
        # Créer utilisateur, organisation et membership
        user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password
        )
        org = Organization.objects.create(
            name='Test Exploitation',
            siret='12345678901234'
        )
        Membership.objects.create(
            user=user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.get(reverse('auth:first_run'))
        
        # Vérifier la redirection vers dashboard
        self.assertRedirects(response, '/dashboard/')


class APIAuthTestCase(TestCase):
    """Tests de l'API d'authentification"""
    
    def setUp(self):
        self.client = Client()
        self.test_email = 'api@example.com'
        self.test_password = 'apipass123'
        self.user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password,
            first_name='API',
            last_name='User'
        )
    
    def test_api_login_success(self):
        """Test API login avec succès"""
        response = self.client.post('/api/auth/session/', {
            'email': self.test_email,
            'password': self.test_password,
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], self.test_email)
    
    def test_api_login_failure(self):
        """Test API login avec échec"""
        response = self.client.post('/api/auth/session/', {
            'email': self.test_email,
            'password': 'wrongpassword',
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
    
    def test_api_whoami_authenticated(self):
        """Test API whoami avec utilisateur connecté"""
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.get('/api/auth/whoami/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['email'], self.test_email)
        self.assertEqual(data['full_name'], 'API User')
        self.assertFalse(data['has_active_membership'])
    
    def test_api_logout(self):
        """Test API logout"""
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(response.status_code, 204)
        
        # Vérifier que la session est détruite
        response = self.client.get('/api/auth/whoami/')
        self.assertEqual(response.status_code, 403)  # Non authentifié


class OnboardingTestCase(TestCase):
    """Tests de l'onboarding rapide selon roadmap 03_onboarding_rapide.txt"""
    
    def setUp(self):
        self.client = Client()
        self.test_email = 'onboarding@example.com'
        self.test_password = 'onboardpass123'
        self.user = User.objects.create_user(
            username=self.test_email,
            email=self.test_email,
            password=self.test_password,
            first_name='Onboarding',
            last_name='User'
        )
    
    def test_first_run_no_membership_redirects_to_org_creation(self):
        """
        Test roadmap : Après signup → GET /auth/first-run/ renvoie redirect vers 
        /auth/first-run/org/ si aucun Membership
        """
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.get(reverse('auth:first_run'))
        
        # Vérifier la redirection vers création d'organisation
        self.assertRedirects(response, '/auth/first-run/org/')
    
    def test_create_organization_success(self):
        """
        Test roadmap : POST /auth/first-run/org/ avec name valide → crée Organization + 
        Membership owner → redirect /dashboard/
        """
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.post(reverse('auth:create_organization'), {
            'name': 'Test Exploitation Onboarding',
            'siret': '12345678901234',
            'tva_number': 'FR12345678901',
            'currency': 'EUR',
        })
        
        # Vérifier que l'organisation est créée
        self.assertTrue(Organization.objects.filter(name='Test Exploitation Onboarding').exists())
        org = Organization.objects.get(name='Test Exploitation Onboarding')
        
        # Vérifier que l'organisation est initialisée
        self.assertTrue(org.is_initialized)
        
        # Vérifier que le Membership owner est créé
        self.assertTrue(Membership.objects.filter(
            user=self.user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        ).exists())
        
        # Vérifier la redirection vers dashboard
        self.assertRedirects(response, '/dashboard/')
    
    def test_create_organization_minimal_data(self):
        """
        Test création d'organisation avec données minimales (nom seulement)
        """
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.post(reverse('auth:create_organization'), {
            'name': 'Exploitation Minimale',
            'currency': 'EUR',  # Valeur par défaut
        })
        
        # Vérifier que l'organisation est créée même sans SIRET/TVA
        self.assertTrue(Organization.objects.filter(name='Exploitation Minimale').exists())
        org = Organization.objects.get(name='Exploitation Minimale')
        
        # Vérifier les valeurs par défaut
        self.assertEqual(org.currency, 'EUR')
        self.assertEqual(org.siret, '')
        self.assertEqual(org.tva_number, '')
        self.assertTrue(org.is_initialized)
        
        # Vérifier la redirection
        self.assertRedirects(response, '/dashboard/')
    
    def test_create_organization_invalid_siret(self):
        """
        Test validation du SIRET
        """
        self.client.login(username=self.test_email, password=self.test_password)
        
        response = self.client.post(reverse('auth:create_organization'), {
            'name': 'Test Exploitation',
            'siret': '123456789',  # SIRET invalide (trop court)
            'currency': 'EUR',
        })
        
        # Vérifier que l'organisation n'est pas créée
        self.assertFalse(Organization.objects.filter(name='Test Exploitation').exists())
        
        # Vérifier que le formulaire contient des erreurs
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Le SIRET doit contenir exactement 14 chiffres')
    
    def test_first_run_with_existing_membership_redirects_dashboard(self):
        """
        Test que si l'utilisateur a déjà un Membership, il est redirigé vers dashboard
        """
        # Créer une organisation et un membership
        org = Organization.objects.create(
            name='Exploitation Existante',
            siret='98765432109876',
            is_initialized=True
        )
        Membership.objects.create(
            user=self.user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        self.client.login(username=self.test_email, password=self.test_password)
        
        # Tester first-run
        response = self.client.get(reverse('auth:first_run'))
        self.assertRedirects(response, '/dashboard/')
        
        # Tester accès direct à création d'organisation
        response = self.client.get(reverse('auth:create_organization'))
        self.assertRedirects(response, '/dashboard/')
    
    def test_require_membership_decorator(self):
        """
        Test roadmap : Accès à une vue « métier » sans Membership → redirect vers first-run guard
        """
        from .decorators import require_membership
        
        # Créer une vue protégée pour le test
        @require_membership
        def protected_view(request):
            return HttpResponse('Protected content')
        
        self.client.login(username=self.test_email, password=self.test_password)
        
        # Simuler l'accès à une vue protégée sans membership
        from django.http import HttpResponse
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/protected/')
        request.user = self.user
        
        response = protected_view(request)
        
        # Vérifier la redirection vers first-run
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/auth/first-run/')


class RolesAndPermissionsTestCase(TestCase):
    """Tests des rôles et permissions selon roadmap 04_roles_acces.txt"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Exploitation Rôles',
            siret='12345678901234',
            is_initialized=True
        )
        
        # Créer des utilisateurs avec différents rôles
        self.owner = User.objects.create_user(
            username='owner@test.fr',
            email='owner@test.fr',
            password='owner123',
            first_name='Owner',
            last_name='Test'
        )
        self.owner_membership = Membership.objects.create(
            user=self.owner,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        self.admin = User.objects.create_user(
            username='admin@test.fr',
            email='admin@test.fr',
            password='admin123',
            first_name='Admin',
            last_name='Test'
        )
        self.admin_membership = Membership.objects.create(
            user=self.admin,
            organization=self.organization,
            role=Membership.Role.ADMIN,
            is_active=True
        )
        
        self.editor = User.objects.create_user(
            username='editor@test.fr',
            email='editor@test.fr',
            password='editor123',
            first_name='Editor',
            last_name='Test'
        )
        self.editor_membership = Membership.objects.create(
            user=self.editor,
            organization=self.organization,
            role=Membership.Role.EDITOR,
            is_active=True
        )
        
        self.reader = User.objects.create_user(
            username='reader@test.fr',
            email='reader@test.fr',
            password='reader123',
            first_name='Reader',
            last_name='Test'
        )
        self.reader_membership = Membership.objects.create(
            user=self.reader,
            organization=self.organization,
            role=Membership.Role.READ_ONLY,
            is_active=True
        )
    
    def test_read_only_cannot_access_roles_management(self):
        """
        Test roadmap : Un read_only ne peut pas accéder à /settings/roles (403 ou redirect)
        """
        self.client.login(username='reader@test.fr', password='reader123')
        
        response = self.client.get(reverse('auth:roles_management'))
        
        # Vérifier que l'accès est refusé
        self.assertEqual(response.status_code, 403)
    
    def test_editor_cannot_access_roles_management(self):
        """
        Test qu'un editor ne peut pas accéder à la gestion des rôles
        """
        self.client.login(username='editor@test.fr', password='editor123')
        
        response = self.client.get(reverse('auth:roles_management'))
        
        # Vérifier que l'accès est refusé
        self.assertEqual(response.status_code, 403)
    
    def test_admin_can_access_roles_management(self):
        """
        Test qu'un admin peut accéder à la gestion des rôles
        """
        self.client.login(username='admin@test.fr', password='admin123')
        
        response = self.client.get(reverse('auth:roles_management'))
        
        # Vérifier que l'accès est autorisé
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestion des rôles')
        self.assertContains(response, self.organization.name)
    
    def test_owner_can_access_roles_management(self):
        """
        Test qu'un owner peut accéder à la gestion des rôles
        """
        self.client.login(username='owner@test.fr', password='owner123')
        
        response = self.client.get(reverse('auth:roles_management'))
        
        # Vérifier que l'accès est autorisé
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestion des rôles')
    
    def test_admin_can_invite_user(self):
        """
        Test roadmap : Un admin peut inviter; l'invité rejoint avec le rôle demandé
        """
        self.client.login(username='admin@test.fr', password='admin123')
        
        response = self.client.post(reverse('auth:invite_user'), {
            'email': 'newuser@test.fr',
            'role': Membership.Role.EDITOR,
        })
        
        # Vérifier la redirection vers la gestion des rôles
        self.assertRedirects(response, reverse('auth:roles_management'))
        
        # Vérifier le message de succès
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invitation envoyée' in str(m) for m in messages))
    
    def test_admin_cannot_create_owner(self):
        """
        Test qu'un admin ne peut pas créer un owner
        """
        self.client.login(username='admin@test.fr', password='admin123')
        
        # Vérifier que le formulaire ne propose pas le rôle owner
        response = self.client.get(reverse('auth:invite_user'))
        self.assertEqual(response.status_code, 200)
        
        # Le formulaire ne devrait pas contenir l'option owner
        form_html = response.content.decode()
        self.assertNotIn('Propriétaire', form_html)
    
    def test_owner_can_create_any_role(self):
        """
        Test qu'un owner peut créer tous les rôles
        """
        self.client.login(username='owner@test.fr', password='owner123')
        
        response = self.client.get(reverse('auth:invite_user'))
        self.assertEqual(response.status_code, 200)
        
        # Le formulaire devrait contenir toutes les options
        form_html = response.content.decode()
        self.assertIn('Propriétaire', form_html)
        self.assertIn('Administrateur', form_html)
        self.assertIn('Éditeur', form_html)
    
    def test_cannot_remove_last_owner(self):
        """
        Test roadmap : Impossible de se retrouver sans owner dans une org
        """
        self.client.login(username='owner@test.fr', password='owner123')
        
        # Essayer de changer le rôle du seul owner
        response = self.client.post(
            reverse('auth:change_role', kwargs={'membership_id': self.owner_membership.id}),
            {'role': Membership.Role.ADMIN}
        )
        
        # Vérifier que le changement est refusé
        self.assertEqual(response.status_code, 200)  # Reste sur la page avec erreur
        
        # Vérifier que le rôle n'a pas changé
        self.owner_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.role, Membership.Role.OWNER)
    
    def test_can_remove_owner_when_multiple_owners(self):
        """
        Test qu'on peut retirer un owner s'il y en a plusieurs
        """
        # Créer un second owner
        second_owner = User.objects.create_user(
            username='owner2@test.fr',
            email='owner2@test.fr',
            password='owner123'
        )
        second_owner_membership = Membership.objects.create(
            user=second_owner,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        self.client.login(username='owner@test.fr', password='owner123')
        
        # Changer le rôle du second owner
        response = self.client.post(
            reverse('auth:change_role', kwargs={'membership_id': second_owner_membership.id}),
            {'role': Membership.Role.ADMIN}
        )
        
        # Vérifier la redirection (succès)
        self.assertRedirects(response, reverse('auth:roles_management'))
        
        # Vérifier que le rôle a changé
        second_owner_membership.refresh_from_db()
        self.assertEqual(second_owner_membership.role, Membership.Role.ADMIN)
    
    def test_deactivate_member_success(self):
        """
        Test de désactivation d'un membre
        """
        self.client.login(username='owner@test.fr', password='owner123')
        
        # Désactiver l'éditeur
        response = self.client.post(
            reverse('auth:deactivate_member', kwargs={'membership_id': self.editor_membership.id})
        )
        
        # Vérifier la redirection
        self.assertRedirects(response, reverse('auth:roles_management'))
        
        # Vérifier que le membership est désactivé
        self.editor_membership.refresh_from_db()
        self.assertFalse(self.editor_membership.is_active)
    
    def test_cannot_deactivate_self(self):
        """
        Test qu'on ne peut pas se désactiver soi-même
        """
        self.client.login(username='owner@test.fr', password='owner123')
        
        response = self.client.post(
            reverse('auth:deactivate_member', kwargs={'membership_id': self.owner_membership.id})
        )
        
        # Vérifier la redirection avec message d'erreur
        self.assertRedirects(response, reverse('auth:roles_management'))
        
        # Vérifier que le membership est toujours actif
        self.owner_membership.refresh_from_db()
        self.assertTrue(self.owner_membership.is_active)
    
    def test_require_membership_decorator_hierarchy(self):
        """
        Test de la hiérarchie des rôles avec le décorateur
        """
        from .decorators import require_membership
        from django.http import HttpResponse
        
        @require_membership('editor')
        def test_view(request):
            return HttpResponse('OK')
        
        # Test avec différents rôles
        test_cases = [
            ('reader@test.fr', 403),  # READ_ONLY ne peut pas accéder à une vue editor
            ('editor@test.fr', 200),  # EDITOR peut accéder
            ('admin@test.fr', 200),   # ADMIN peut accéder (hiérarchie)
            ('owner@test.fr', 200),   # OWNER peut accéder (hiérarchie)
        ]
        
        for email, expected_status in test_cases:
            with self.subTest(email=email):
                self.client.login(username=email, password=email.split('@')[0] + '123')
                
                # Simuler l'appel à la vue
                from django.test import RequestFactory
                factory = RequestFactory()
                request = factory.get('/test/')
                request.user = User.objects.get(email=email)
                
                response = test_view(request)
                self.assertEqual(response.status_code, expected_status)
