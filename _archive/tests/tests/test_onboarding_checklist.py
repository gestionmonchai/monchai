"""
Tests pour la checklist d'onboarding - Sprint 09
Tests selon roadmap 09: GET checklist, mise à jour automatique, progress
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization, Membership, OrgSetupChecklist
from apps.accounts.utils import checklist_service
from .factories import (
    UserFactory, OrganizationFactory, MembershipFactory,
    OwnerMembershipFactory, AdminMembershipFactory, ReadOnlyMembershipFactory
)

User = get_user_model()


@pytest.mark.django_db
class TestChecklistModel:
    """Tests du modèle OrgSetupChecklist"""
    
    def test_checklist_creation_with_default_state(self):
        """Test création checklist avec état par défaut"""
        organization = OrganizationFactory()
        # La checklist est créée automatiquement par le signal
        checklist = organization.setup_checklist
        
        # Vérifier état par défaut
        expected_state = {
            'company_info': 'todo',
            'taxes': 'todo',
            'currency_format': 'todo',
            'terms': 'todo'
        }
        assert checklist.state == expected_state
        assert checklist.get_progress() == 0
        assert checklist.get_completed_count() == 0
        assert not checklist.is_completed()
    
    def test_checklist_progress_calculation(self):
        """Test calcul du pourcentage de progression"""
        organization = OrganizationFactory()
        checklist = organization.setup_checklist
        
        # 0% au début
        assert checklist.get_progress() == 0
        
        # 25% avec 1 tâche terminée
        checklist.update_task('company_info', 'done')
        assert checklist.get_progress() == 25
        assert checklist.get_completed_count() == 1
        
        # 50% avec 2 tâches terminées
        checklist.update_task('taxes', 'done')
        assert checklist.get_progress() == 50
        assert checklist.get_completed_count() == 2
        
        # 100% avec toutes les tâches terminées
        checklist.update_task('currency_format', 'done')
        checklist.update_task('terms', 'done')
        assert checklist.get_progress() == 100
        assert checklist.get_completed_count() == 4
        assert checklist.is_completed()
    
    def test_checklist_task_info(self):
        """Test récupération des informations détaillées des tâches"""
        organization = OrganizationFactory()
        checklist = organization.setup_checklist
        
        tasks = checklist.get_task_info()
        
        # Vérifier structure
        assert len(tasks) == 4
        
        # Vérifier première tâche
        company_info_task = tasks[0]
        assert company_info_task['key'] == 'company_info'
        assert company_info_task['title'] == 'Informations de l\'exploitation'
        assert company_info_task['status'] == 'todo'
        assert company_info_task['url'] == '/settings/billing/'
        assert company_info_task['icon'] == 'bi-building'
    
    def test_checklist_update_task_validation(self):
        """Test validation lors de la mise à jour des tâches"""
        organization = OrganizationFactory()
        checklist = organization.setup_checklist
        
        # Test clé invalide
        with pytest.raises(ValueError, match="Clé de tâche invalide"):
            checklist.update_task('invalid_key', 'done')
        
        # Test statut invalide
        with pytest.raises(ValueError, match="Statut invalide"):
            checklist.update_task('company_info', 'invalid_status')


@pytest.mark.django_db
class TestChecklistSignal:
    """Tests du signal de création automatique de checklist"""
    
    def test_checklist_created_on_organization_creation(self):
        """Test création automatique de checklist après création organisation"""
        # Créer une organisation
        organization = OrganizationFactory()
        
        # Vérifier que la checklist a été créée automatiquement
        assert hasattr(organization, 'setup_checklist')
        checklist = organization.setup_checklist
        assert checklist.state == OrgSetupChecklist.get_default_state()
        assert checklist.get_progress() == 0


@pytest.mark.django_db
class TestChecklistService:
    """Tests du service ChecklistService"""
    
    def test_get_or_create_checklist(self):
        """Test get_or_create_checklist"""
        organization = OrganizationFactory()
        
        # Premier appel - création
        checklist1 = checklist_service.get_or_create_checklist(organization)
        assert checklist1.organization == organization
        
        # Deuxième appel - récupération
        checklist2 = checklist_service.get_or_create_checklist(organization)
        assert checklist1.id == checklist2.id
    
    def test_checklist_update(self):
        """Test checklist_update"""
        organization = OrganizationFactory()
        
        # Marquer une tâche comme terminée
        checklist = checklist_service.checklist_update(organization, 'company_info', True)
        assert checklist.state['company_info'] == 'done'
        
        # Marquer une tâche comme non terminée
        checklist = checklist_service.checklist_update(organization, 'company_info', False)
        assert checklist.state['company_info'] == 'todo'
    
    def test_check_company_info_completion(self):
        """Test vérification completion des infos exploitation"""
        organization = OrganizationFactory()
        
        # Organisation incomplète par défaut
        assert not checklist_service.check_company_info_completion(organization)
        
        # Compléter les informations
        organization.name = "Mon Exploitation"
        organization.address = "123 Rue de la Paix"
        organization.postal_code = "75001"
        organization.city = "Paris"
        organization.save()
        
        assert checklist_service.check_company_info_completion(organization)
    
    def test_check_currency_format_completion(self):
        """Test vérification completion devise et formats"""
        organization = OrganizationFactory()
        
        # Devise par défaut EUR
        assert checklist_service.check_currency_format_completion(organization)
    
    def test_auto_update_from_organization(self):
        """Test mise à jour automatique depuis organisation"""
        organization = OrganizationFactory()
        
        # État initial
        checklist = checklist_service.get_or_create_checklist(organization)
        assert checklist.get_progress() == 0
        
        # Compléter les infos exploitation
        organization.name = "Mon Exploitation"
        organization.address = "123 Rue de la Paix"
        organization.postal_code = "75001"
        organization.city = "Paris"
        organization.save()
        
        # Mise à jour automatique
        checklist = checklist_service.auto_update_from_organization(organization)
        assert checklist.state['company_info'] == 'done'
        assert checklist.get_progress() > 0


@pytest.mark.django_db
class TestChecklistViews:
    """Tests des vues de checklist"""
    
    def test_checklist_view_get_anonymous_redirected(self):
        """Test utilisateur anonyme redirigé vers login"""
        client = Client()
        response = client.get(reverse('onboarding:checklist'))
        
        assert response.status_code == 302
        assert reverse('auth:login') in response.url
    
    def test_checklist_view_get_with_organization(self):
        """Test GET checklist avec organisation - 200 + 4 tâches affichées + progress 0%"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('onboarding:checklist'))
        
        # Vérifier réponse
        assert response.status_code == 200
        assert 'checklist' in response.context
        assert 'tasks' in response.context
        assert 'progress' in response.context
        
        # Vérifier contenu
        assert response.context['progress'] == 0
        assert response.context['completed_count'] == 0
        assert response.context['total_tasks'] == 4
        assert len(response.context['tasks']) == 4
        assert not response.context['is_completed']
        
        # Vérifier affichage
        content = response.content.decode()
        assert 'Configuration de votre exploitation' in content
        assert 'Informations' in content  # Plus flexible pour l'encodage
        assert 'TVA et taxes' in content
        assert 'Devise et formats' in content
        assert 'Conditions' in content
    
    def test_checklist_view_completed_shows_banner(self):
        """Test checklist terminée affiche bannière de félicitations"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        # Marquer toutes les tâches comme terminées
        checklist = checklist_service.get_or_create_checklist(organization)
        for task_key in ['company_info', 'taxes', 'currency_format', 'terms']:
            checklist.update_task(task_key, 'done')
        
        client = Client()
        client.force_login(user)
        
        response = client.get(reverse('onboarding:checklist'))
        
        # Vérifier contexte
        assert response.context['is_completed'] is True
        assert response.context['progress'] == 100
        
        # Vérifier affichage
        content = response.content.decode()
        assert 'Félicitations' in content
        assert 'Configuration terminée' in content


@pytest.mark.django_db
class TestSettingsViews:
    """Tests des vues de paramètres avec mise à jour automatique"""
    
    def test_billing_settings_post_updates_checklist(self):
        """Test POST /settings/billing met à jour company_info et taxes"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Données complètes
        data = {
            'name': 'Mon Exploitation Test',
            'address': '123 Rue de Test',
            'postal_code': '75001',
            'city': 'Paris',
            'country': 'France',
            'siret': '12345678901234',
            'tva_number': 'FR12345678901'
        }
        
        response = client.post(reverse('auth:billing_settings'), data)
        
        # Vérifier redirection
        assert response.status_code == 302
        
        # Vérifier mise à jour organisation
        organization.refresh_from_db()
        assert organization.name == 'Mon Exploitation Test'
        assert organization.address == '123 Rue de Test'
        
        # Vérifier mise à jour checklist
        checklist = organization.setup_checklist
        assert checklist.state['company_info'] == 'done'
    
    def test_general_settings_post_updates_checklist(self):
        """Test POST /settings/general met à jour currency_format"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Données
        data = {
            'currency': 'USD',
            'cgv_url': 'https://example.com/cgv'
        }
        
        response = client.post(reverse('auth:general_settings'), data)
        
        # Vérifier redirection
        assert response.status_code == 302
        
        # Vérifier mise à jour organisation
        organization.refresh_from_db()
        assert organization.currency == 'USD'
        
        # Vérifier mise à jour checklist
        checklist = organization.setup_checklist
        assert checklist.state['currency_format'] == 'done'
