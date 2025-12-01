"""
Tests pour le système d'invitations - Roadmap 07
Tests selon checklist QA : modèle, tokens, vues, emails, sécurité
"""

from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from django.contrib.messages import get_messages

from .models import Organization, Membership, Invitation
from .utils import invitation_manager

User = get_user_model()


class InvitationModelTest(TestCase):
    """Tests du modèle Invitation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def test_create_invitation(self):
        """Test création d'invitation"""
        invitation = Invitation.objects.create(
            email='invite@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            token='test-token',
            expires_at=timezone.now() + timedelta(hours=72),
            invited_by=self.user
        )
        
        self.assertEqual(invitation.email, 'invite@test.com')
        self.assertEqual(invitation.organization, self.organization)
        self.assertEqual(invitation.role, Membership.Role.EDITOR)
        self.assertEqual(invitation.status, Invitation.Status.SENT)
        self.assertFalse(invitation.is_expired())
    
    def test_invitation_expiry(self):
        """Test expiration d'invitation"""
        # Invitation expirée
        expired_invitation = Invitation.objects.create(
            email='expired@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            token='expired-token',
            expires_at=timezone.now() - timedelta(hours=1),
            invited_by=self.user
        )
        
        self.assertTrue(expired_invitation.is_expired())
        self.assertFalse(expired_invitation.can_be_accepted())
    
    def test_invitation_methods(self):
        """Test méthodes du modèle Invitation"""
        invitation = Invitation.objects.create(
            email='methods@test.com',
            organization=self.organization,
            role=Membership.Role.ADMIN,
            token='methods-token',
            expires_at=timezone.now() + timedelta(hours=72),
            invited_by=self.user
        )
        
        # Test can_be_accepted
        self.assertTrue(invitation.can_be_accepted())
        
        # Test mark_as_accepted
        accepted_user = User.objects.create_user(
            username='accepted@test.com',
            email='accepted@test.com',
            password='testpass123'
        )
        invitation.mark_as_accepted(accepted_user)
        
        self.assertEqual(invitation.status, Invitation.Status.ACCEPTED)
        self.assertEqual(invitation.accepted_by, accepted_user)
        self.assertIsNotNone(invitation.accepted_at)
        self.assertFalse(invitation.can_be_accepted())


class InvitationManagerTest(TestCase):
    """Tests du gestionnaire d'invitations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def test_create_invitation_token(self):
        """Test génération de token d'invitation"""
        token = invitation_manager.create_invitation_token(
            email='test@example.com',
            organization_id=self.organization.id,
            role=Membership.Role.EDITOR
        )
        
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)  # Token signé doit être assez long
    
    def test_verify_invitation_token(self):
        """Test vérification de token d'invitation"""
        # Token valide
        token = invitation_manager.create_invitation_token(
            email='test@example.com',
            organization_id=self.organization.id,
            role=Membership.Role.EDITOR
        )
        
        payload = invitation_manager.verify_invitation_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['email'], 'test@example.com')
        self.assertEqual(payload['org_id'], self.organization.id)
        self.assertEqual(payload['role'], Membership.Role.EDITOR)
        
        # Token invalide
        invalid_payload = invitation_manager.verify_invitation_token('invalid-token')
        self.assertIsNone(invalid_payload)
    
    def test_create_invitation_complete(self):
        """Test création d'invitation complète"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        invitation = invitation_manager.create_invitation(
            email='complete@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            invited_by=self.user,
            request=request
        )
        
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.email, 'complete@test.com')
        self.assertEqual(invitation.organization, self.organization)
        self.assertEqual(invitation.role, Membership.Role.EDITOR)
        self.assertEqual(invitation.invited_by, self.user)
        
        # Vérifier qu'un email a été envoyé (en mode test)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('complete@test.com', mail.outbox[0].to)
    
    def test_prevent_duplicate_invitations(self):
        """Test prévention des invitations en double"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        # Première invitation
        invitation1 = invitation_manager.create_invitation(
            email='duplicate@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            invited_by=self.user,
            request=request
        )
        
        # Tentative de deuxième invitation
        invitation2 = invitation_manager.create_invitation(
            email='duplicate@test.com',
            organization=self.organization,
            role=Membership.Role.ADMIN,
            invited_by=self.user,
            request=request
        )
        
        self.assertIsNotNone(invitation1)
        self.assertIsNone(invitation2)  # Doit être rejetée


class InvitationViewsTest(TestCase):
    """Tests des vues d'invitation"""
    
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        self.membership = Membership.objects.create(
            user=self.owner,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
    
    def test_send_invitation_view_get(self):
        """Test affichage du formulaire d'invitation"""
        self.client.login(username='owner@test.com', password='testpass123')
        
        response = self.client.get(reverse('auth:send_invitation'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inviter un utilisateur')
        self.assertContains(response, 'form')
    
    def test_send_invitation_view_post(self):
        """Test envoi d'invitation via formulaire"""
        self.client.login(username='owner@test.com', password='testpass123')
        
        response = self.client.post(reverse('auth:send_invitation'), {
            'email': 'newuser@test.com',
            'role': Membership.Role.EDITOR
        })
        
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        
        # Vérifier qu'une invitation a été créée
        invitation = Invitation.objects.filter(email='newuser@test.com').first()
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.role, Membership.Role.EDITOR)
        
        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
    
    def test_accept_invitation_view_anonymous(self):
        """Test acceptation d'invitation par utilisateur non connecté"""
        # Créer une invitation avec un token valide
        token = invitation_manager.create_invitation_token(
            email='anonymous@test.com',
            organization_id=self.organization.id,
            role=Membership.Role.EDITOR
        )
        
        invitation = Invitation.objects.create(
            email='anonymous@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            token=token,
            expires_at=timezone.now() + timedelta(hours=72),
            invited_by=self.owner
        )
        
        # GET - Afficher la page d'acceptation
        response = self.client.get(
            reverse('auth:accept_invitation', kwargs={'token': token})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invitation à rejoindre')
        self.assertContains(response, self.organization.name)
    
    def test_accept_invitation_view_authenticated(self):
        """Test acceptation d'invitation par utilisateur connecté"""
        # Créer un utilisateur connecté
        user = User.objects.create_user(
            username='connected@test.com',
            email='connected@test.com',
            password='testpass123'
        )
        self.client.login(username='connected@test.com', password='testpass123')
        
        # Créer une invitation avec un token valide
        token = invitation_manager.create_invitation_token(
            email='connected@test.com',
            organization_id=self.organization.id,
            role=Membership.Role.EDITOR
        )
        
        invitation = Invitation.objects.create(
            email='connected@test.com',
            organization=self.organization,
            role=Membership.Role.EDITOR,
            token=token,
            expires_at=timezone.now() + timedelta(hours=72),
            invited_by=self.owner
        )
        
        # POST - Accepter l'invitation
        response = self.client.post(
            reverse('auth:accept_invitation', kwargs={'token': token})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        
        # Vérifier qu'un membership a été créé
        membership = Membership.objects.filter(
            user=user,
            organization=self.organization
        ).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, Membership.Role.EDITOR)
        
        # Vérifier que l'invitation est marquée comme acceptée
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.ACCEPTED)


class InvitationSecurityTest(TestCase):
    """Tests de sécurité du système d'invitations"""
    
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        self.editor = User.objects.create_user(
            username='editor@test.com',
            email='editor@test.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            is_initialized=True
        )
        
        # Owner membership
        Membership.objects.create(
            user=self.owner,
            organization=self.organization,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        # Editor membership
        Membership.objects.create(
            user=self.editor,
            organization=self.organization,
            role=Membership.Role.EDITOR,
            is_active=True
        )
    
    def test_invitation_requires_admin_role(self):
        """Test que seuls les admins+ peuvent inviter"""
        # Editor ne peut pas accéder à la page d'invitation
        self.client.login(username='editor@test.com', password='testpass123')
        
        response = self.client.get(reverse('auth:send_invitation'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        response = self.client.post(reverse('auth:send_invitation'), {
            'email': 'unauthorized@test.com',
            'role': Membership.Role.EDITOR
        })
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_invitation_requires_authentication(self):
        """Test que l'invitation nécessite une authentification"""
        response = self.client.get(reverse('auth:send_invitation'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
        
        response = self.client.post(reverse('auth:send_invitation'), {
            'email': 'anonymous@test.com',
            'role': Membership.Role.EDITOR
        })
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_token_tampering_protection(self):
        """Test protection contre la modification de tokens"""
        # Token valide
        valid_token = invitation_manager.create_invitation_token(
            email='test@example.com',
            organization_id=self.organization.id,
            role=Membership.Role.EDITOR
        )
        
        # Token modifié
        tampered_token = valid_token + 'tampered'
        
        payload = invitation_manager.verify_invitation_token(tampered_token)
        self.assertIsNone(payload)  # Doit être rejeté
    
    def test_expired_token_rejection(self):
        """Test rejet des tokens expirés"""
        # Créer un token avec expiration dans le passé
        past_time = timezone.now() - timedelta(hours=1)
        
        with self.settings(SECRET_KEY='test-secret'):
            # Simuler un token expiré en modifiant l'expiry_hours temporairement
            original_expiry = invitation_manager.expiry_hours
            invitation_manager.expiry_hours = -1  # Expiration dans le passé
            
            expired_token = invitation_manager.create_invitation_token(
                email='expired@example.com',
                organization_id=self.organization.id,
                role=Membership.Role.EDITOR
            )
            
            # Restaurer l'expiration normale
            invitation_manager.expiry_hours = original_expiry
            
            # Le token doit être rejeté
            payload = invitation_manager.verify_invitation_token(expired_token)
            self.assertIsNone(payload)
