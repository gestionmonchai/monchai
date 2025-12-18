"""
Tests de régression pour l'éditeur de templates de documents
"""
import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User, Organization, Membership
from apps.sales.models_documents import DocumentTemplate


@pytest.fixture
def org_and_user(db):
    """Crée une organisation et un utilisateur admin pour les tests"""
    org = Organization.objects.create(
        name="Test Domaine",
    )
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User"
    )
    Membership.objects.create(
        user=user,
        organization=org,
        role="owner"
    )
    return org, user


@pytest.fixture
def authenticated_client(org_and_user):
    """Client authentifié avec organisation"""
    org, user = org_and_user
    client = Client()
    client.login(email="test@example.com", password="testpass123")
    # Simuler la sélection d'organisation
    session = client.session
    session['current_org_id'] = str(org.id)
    session.save()
    return client, org, user


@pytest.mark.django_db
class TestDocumentTemplateViews:
    """Tests pour les vues de templates de documents"""
    
    def test_template_list_loads(self, authenticated_client):
        """La liste des templates se charge sans erreur"""
        client, org, user = authenticated_client
        response = client.get('/clients/templates/')
        assert response.status_code == 200
    
    def test_template_create_page_loads(self, authenticated_client):
        """La page de création de template se charge sans erreur (test de régression)"""
        client, org, user = authenticated_client
        response = client.get('/clients/templates/creer/')
        assert response.status_code == 200
        assert 'CodeMirror' in response.content.decode()
    
    def test_template_create_form_submission(self, authenticated_client):
        """Création d'un template via le formulaire"""
        client, org, user = authenticated_client
        
        response = client.post('/clients/templates/creer/', {
            'name': 'Test Template',
            'document_type': 'quote',
            'description': 'Template de test',
            'paper_size': 'A4',
            'orientation': 'portrait',
            'html_header': '<h1>Test Header</h1>',
            'html_body': '<p>Test Body</p>',
            'html_footer': '<p>Test Footer</p>',
            'custom_css': 'body { color: red; }',
        })
        
        # Devrait rediriger vers le détail
        assert response.status_code == 302
        
        # Vérifier que le template a été créé
        template = DocumentTemplate.objects.filter(
            organization=org,
            name='Test Template'
        ).first()
        assert template is not None
        assert template.document_type == 'quote'
    
    def test_template_edit_page_loads(self, authenticated_client):
        """La page de modification de template se charge"""
        client, org, user = authenticated_client
        
        # Créer un template
        template = DocumentTemplate.objects.create(
            organization=org,
            name='Edit Test',
            document_type='invoice',
            html_header='<h1>Invoice</h1>',
            html_body='<p>Body</p>',
            html_footer='<p>Footer</p>',
        )
        
        response = client.get(f'/clients/templates/{template.id}/modifier/')
        assert response.status_code == 200
        assert 'Edit Test' in response.content.decode()
    
    def test_template_detail_page_loads(self, authenticated_client):
        """La page de détail de template se charge"""
        client, org, user = authenticated_client
        
        template = DocumentTemplate.objects.create(
            organization=org,
            name='Detail Test',
            document_type='order',
        )
        
        response = client.get(f'/clients/templates/{template.id}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestDocumentTemplateModel:
    """Tests pour le modèle DocumentTemplate"""
    
    def test_create_default_template(self, org_and_user):
        """Création d'un template par défaut"""
        org, user = org_and_user
        
        template = DocumentTemplate.objects.create(
            organization=org,
            name='Facture Standard',
            document_type='invoice',
            is_default=True,
        )
        
        assert template.is_default is True
        assert str(template) == "Facture - Facture Standard [Défaut]"
    
    def test_only_one_default_per_type(self, org_and_user):
        """Un seul template par défaut par type de document"""
        org, user = org_and_user
        
        template1 = DocumentTemplate.objects.create(
            organization=org,
            name='Facture 1',
            document_type='invoice',
            is_default=True,
        )
        
        template2 = DocumentTemplate.objects.create(
            organization=org,
            name='Facture 2',
            document_type='invoice',
            is_default=True,
        )
        
        # Recharger template1
        template1.refresh_from_db()
        
        # Template1 ne devrait plus être le défaut
        assert template1.is_default is False
        assert template2.is_default is True
