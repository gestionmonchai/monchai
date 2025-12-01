"""
Tests des permissions et rôles - Sprint 08
Tests selon roadmap 08: read_only interdit /settings/roles, editor accès CRUD, empêcher retrait dernier owner
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization, Membership
from .factories import (
    UserFactory, OrganizationFactory, MembershipFactory,
    OwnerMembershipFactory, AdminMembershipFactory, ReadOnlyMembershipFactory
)

User = get_user_model()


@pytest.mark.django_db
class TestRoleBasedAccess:
    """Tests d'accès basés sur les rôles"""
    
    def test_read_only_cannot_access_roles_management(self):
        """Test read_only interdit d'accès à /settings/roles (403/redirect)"""
        user = UserFactory()
        membership = ReadOnlyMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier accès refusé
        assert response.status_code == 403
    
    def test_editor_cannot_access_roles_management(self):
        """Test editor ne peut pas accéder à /settings/roles"""
        user = UserFactory()
        membership = MembershipFactory(user=user, role=Membership.Role.EDITOR)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier accès refusé
        assert response.status_code == 403
    
    def test_admin_can_access_roles_management(self):
        """Test admin peut accéder à /settings/roles"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier accès autorisé
        assert response.status_code == 200
        assert 'Gestion des rôles' in response.content.decode()
    
    def test_owner_can_access_roles_management(self):
        """Test owner peut accéder à /settings/roles"""
        user = UserFactory()
        membership = OwnerMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier accès autorisé
        assert response.status_code == 200
        assert 'Gestion des rôles' in response.content.decode()
    
    def test_read_only_cannot_send_invitations(self):
        """Test read_only ne peut pas envoyer d'invitations"""
        user = UserFactory()
        membership = ReadOnlyMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:send_invitation'))
        
        # Vérifier accès refusé
        assert response.status_code == 403
    
    def test_editor_cannot_send_invitations(self):
        """Test editor ne peut pas envoyer d'invitations"""
        user = UserFactory()
        membership = MembershipFactory(user=user, role=Membership.Role.EDITOR)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:send_invitation'))
        
        # Vérifier accès refusé
        assert response.status_code == 403
    
    def test_admin_can_send_invitations(self):
        """Test admin peut envoyer des invitations"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:send_invitation'))
        
        # Vérifier accès autorisé
        assert response.status_code == 200
        assert 'Inviter un utilisateur' in response.content.decode()


@pytest.mark.django_db
class TestOwnerProtection:
    """Tests de protection du dernier owner"""
    
    def test_cannot_remove_last_owner(self):
        """Test empêcher retrait du dernier owner"""
        organization = OrganizationFactory()
        owner_user = UserFactory()
        owner_membership = OwnerMembershipFactory(user=owner_user, organization=organization)
        
        admin_user = UserFactory()
        admin_membership = AdminMembershipFactory(user=admin_user, organization=organization)
        
        client = Client()
        client.force_login(admin_user)
        
        # Tenter de désactiver le dernier owner
        response = client.post(reverse('auth:deactivate_member', args=[owner_membership.id]))
        
        # Vérifier que l'action est refusée
        owner_membership.refresh_from_db()
        assert owner_membership.is_active is True
    
    def test_can_remove_owner_when_multiple_owners_exist(self):
        """Test peut retirer un owner quand plusieurs owners existent"""
        organization = OrganizationFactory()
        
        # Créer deux owners
        owner1_user = UserFactory()
        owner1_membership = OwnerMembershipFactory(user=owner1_user, organization=organization)
        
        owner2_user = UserFactory()
        owner2_membership = OwnerMembershipFactory(user=owner2_user, organization=organization)
        
        client = Client()
        client.force_login(owner1_user)
        
        # Retirer le deuxième owner
        response = client.post(reverse('auth:deactivate_member', args=[owner2_membership.id]))
        
        # Vérifier que l'action est autorisée
        assert response.status_code == 302
        owner2_membership.refresh_from_db()
        assert owner2_membership.is_active is False
    
    def test_cannot_change_last_owner_role(self):
        """Test ne peut pas changer le rôle du dernier owner"""
        organization = OrganizationFactory()
        owner_user = UserFactory()
        owner_membership = OwnerMembershipFactory(user=owner_user, organization=organization)
        
        client = Client()
        client.force_login(owner_user)
        
        # Tenter de changer son propre rôle (dernier owner)
        data = {'role': Membership.Role.ADMIN}
        response = client.post(reverse('auth:change_role', args=[owner_membership.id]), data)
        
        # Vérifier que le rôle n'a pas changé
        owner_membership.refresh_from_db()
        assert owner_membership.role == Membership.Role.OWNER


@pytest.mark.django_db
class TestOrganizationIsolation:
    """Tests d'isolation entre organisations"""
    
    def test_user_cannot_access_other_organization_data(self):
        """Test utilisateur ne peut pas accéder aux données d'une autre organisation"""
        # Organisation A
        org_a = OrganizationFactory(name="Organisation A")
        user_a = UserFactory()
        membership_a = MembershipFactory(user=user_a, organization=org_a, role=Membership.Role.ADMIN)
        
        # Organisation B
        org_b = OrganizationFactory(name="Organisation B")
        user_b = UserFactory()
        membership_b = MembershipFactory(user=user_b, organization=org_b, role=Membership.Role.ADMIN)
        
        client = Client()
        client.force_login(user_a)
        
        # Tenter d'accéder aux rôles de l'organisation B
        # (ceci nécessiterait une URL avec org_id ou un middleware qui filtre)
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier que seules les données de l'organisation A sont visibles
        assert response.status_code == 200
        content = response.content.decode()
        assert "Organisation A" in content
        assert "Organisation B" not in content
    
    def test_user_cannot_invite_to_other_organization(self):
        """Test utilisateur ne peut pas inviter dans une autre organisation"""
        # Organisation A
        org_a = OrganizationFactory()
        user_a = UserFactory()
        membership_a = AdminMembershipFactory(user=user_a, organization=org_a)
        
        # Organisation B
        org_b = OrganizationFactory()
        
        client = Client()
        client.force_login(user_a)
        
        # Tenter d'envoyer une invitation
        data = {
            'email': 'newuser@test.com',
            'role': Membership.Role.EDITOR
        }
        response = client.post(reverse('auth:send_invitation'), data)
        
        # Vérifier que l'invitation est créée pour l'organisation A seulement
        from apps.accounts.models import Invitation
        invitation = Invitation.objects.filter(email='newuser@test.com').first()
        if invitation:
            assert invitation.organization == org_a
            assert invitation.organization != org_b


@pytest.mark.django_db
class TestMembershipRequiredDecorator:
    """Tests du décorateur require_membership"""
    
    def test_anonymous_user_redirected_to_login(self):
        """Test utilisateur anonyme redirigé vers login"""
        client = Client()
        
        response = client.get(reverse('auth:roles_management'))
        
        assert response.status_code == 302
        assert reverse('auth:login') in response.url
    
    def test_user_without_membership_redirected_to_first_run(self):
        """Test utilisateur sans membership redirigé vers first-run"""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        assert response.status_code == 302
        assert reverse('auth:first_run') in response.url
    
    def test_inactive_membership_denied_access(self):
        """Test membership inactif refuse l'accès"""
        user = UserFactory()
        membership = MembershipFactory(user=user, is_active=False, role=Membership.Role.ADMIN)
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('auth:roles_management'))
        
        # Vérifier redirection first-run (pas de membership actif)
        assert response.status_code == 302
        assert reverse('auth:first_run') in response.url


@pytest.mark.django_db
class TestRoleHierarchy:
    """Tests de la hiérarchie des rôles"""
    
    def test_admin_cannot_create_owner_invitation(self):
        """Test admin ne peut pas créer d'invitation owner"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        data = {
            'email': 'newowner@test.com',
            'role': Membership.Role.OWNER
        }
        response = client.post(reverse('auth:send_invitation'), data)
        
        # Vérifier que le formulaire rejette le rôle owner
        assert response.status_code == 200
        assert 'form' in response.context
        # Le formulaire devrait avoir une erreur ou ne pas permettre owner
    
    def test_owner_can_create_any_role_invitation(self):
        """Test owner peut créer des invitations pour tous les rôles"""
        user = UserFactory()
        membership = OwnerMembershipFactory(user=user)
        client = Client()
        client.force_login(user)
        
        # Tester création invitation owner
        data = {
            'email': 'newowner@test.com',
            'role': Membership.Role.OWNER
        }
        response = client.post(reverse('auth:send_invitation'), data)
        
        # Vérifier succès (redirection)
        assert response.status_code == 302
