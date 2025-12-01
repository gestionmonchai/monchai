"""
Tests pour les paramètres de facturation - Roadmap 11
Tests du modèle OrgBilling, formulaire, vues et intégration checklist
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from apps.accounts.models import OrgBilling
from apps.accounts.forms import OrgBillingForm
from apps.accounts.utils import checklist_service
from tests.factories import UserFactory, OrganizationFactory, AdminMembershipFactory

User = get_user_model()


@pytest.mark.django_db
class TestOrgBillingModel:
    """Tests du modèle OrgBilling"""
    
    def test_billing_creation_with_migration(self):
        """Test création automatique OrgBilling via migration"""
        organization = OrganizationFactory()
        
        # Vérifier que l'enregistrement de facturation a été créé automatiquement
        assert hasattr(organization, 'billing')
        billing = organization.billing
        assert billing.legal_name == ''
        assert billing.vat_status == 'not_subject_to_vat'
        assert billing.billing_country == 'France'
    
    def test_billing_str_representation(self):
        """Test représentation string du modèle"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        assert str(billing) == f'Facturation {organization.name}'
    
    def test_get_full_billing_address(self):
        """Test formatage adresse complète"""
        organization = OrganizationFactory()
        billing = organization.billing
        billing.billing_address_line1 = '123 Rue de la Paix'
        billing.billing_address_line2 = 'Bâtiment A'
        billing.billing_postal_code = '75001'
        billing.billing_city = 'Paris'
        billing.billing_country = 'France'
        billing.save()
        
        expected_address = "123 Rue de la Paix\nBâtiment A\n75001 Paris\nFrance"
        assert billing.get_full_billing_address() == expected_address
    
    def test_get_full_billing_address_without_line2(self):
        """Test formatage adresse sans ligne 2"""
        organization = OrganizationFactory()
        billing = organization.billing
        billing.billing_address_line1 = '123 Rue de la Paix'
        billing.billing_postal_code = '75001'
        billing.billing_city = 'Paris'
        billing.billing_country = 'France'
        billing.save()
        
        expected_address = "123 Rue de la Paix\n75001 Paris\nFrance"
        assert billing.get_full_billing_address() == expected_address
    
    def test_is_vat_subject(self):
        """Test vérification assujettissement TVA"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        # Non assujetti par défaut
        assert not billing.is_vat_subject()
        
        # Assujetti
        billing.vat_status = 'subject_to_vat'
        billing.save()
        assert billing.is_vat_subject()
    
    def test_has_complete_company_info(self):
        """Test vérification informations société complètes"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        # Incomplet par défaut
        assert not billing.has_complete_company_info()
        
        # Complet
        billing.legal_name = 'Mon Entreprise SARL'
        billing.billing_address_line1 = '123 Rue de la Paix'
        billing.billing_postal_code = '75001'
        billing.billing_city = 'Paris'
        billing.save()
        
        assert billing.has_complete_company_info()
    
    def test_has_complete_tax_info_not_subject(self):
        """Test informations fiscales complètes - non assujetti"""
        organization = OrganizationFactory()
        billing = organization.billing
        billing.vat_status = 'not_subject_to_vat'
        billing.save()
        
        assert billing.has_complete_tax_info()
    
    def test_has_complete_tax_info_subject_with_number(self):
        """Test informations fiscales complètes - assujetti avec numéro"""
        organization = OrganizationFactory()
        billing = organization.billing
        billing.vat_status = 'subject_to_vat'
        billing.vat_number = 'FR12345678901'
        billing.save()
        
        assert billing.has_complete_tax_info()
    
    def test_has_complete_tax_info_subject_without_number(self):
        """Test informations fiscales incomplètes - assujetti sans numéro"""
        organization = OrganizationFactory()
        billing = organization.billing
        billing.vat_status = 'subject_to_vat'
        billing.vat_number = ''
        billing.save()
        
        assert not billing.has_complete_tax_info()


@pytest.mark.django_db
class TestOrgBillingForm:
    """Tests du formulaire OrgBillingForm"""
    
    def test_form_required_fields(self):
        """Test champs requis du formulaire"""
        form = OrgBillingForm()
        
        required_fields = ['legal_name', 'billing_address_line1', 'billing_postal_code', 'billing_city', 'vat_status']
        for field_name in required_fields:
            assert form.fields[field_name].required is True
    
    def test_form_valid_data_not_subject_to_vat(self):
        """Test formulaire valide - non assujetti TVA"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
            'siret': '12345678901234',
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert form.is_valid()
        
        saved_billing = form.save()
        assert saved_billing.legal_name == 'Mon Entreprise SARL'
        assert saved_billing.siret == '12345678901234'
        assert saved_billing.vat_status == 'not_subject_to_vat'
        assert saved_billing.vat_number == ''
    
    def test_form_valid_data_subject_to_vat(self):
        """Test formulaire valide - assujetti TVA"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'subject_to_vat',
            'vat_number': 'FR12345678901',
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert form.is_valid()
        
        saved_billing = form.save()
        assert saved_billing.vat_status == 'subject_to_vat'
        assert saved_billing.vat_number == 'FR12345678901'
    
    def test_form_invalid_siret_too_short(self):
        """Test validation SIRET trop court"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
            'siret': '123456789',  # Trop court
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert not form.is_valid()
        assert 'siret' in form.errors
        assert '14 chiffres' in str(form.errors['siret'])
    
    def test_form_invalid_siret_non_numeric(self):
        """Test validation SIRET non numérique"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
            'siret': '1234567890123A',  # Contient une lettre
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert not form.is_valid()
        assert 'siret' in form.errors
    
    def test_form_invalid_vat_number_missing_when_subject(self):
        """Test validation TVA manquante quand assujetti"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'subject_to_vat',
            'vat_number': '',  # Manquant
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert not form.is_valid()
        assert 'vat_number' in form.errors
    
    def test_form_invalid_vat_number_wrong_format(self):
        """Test validation format TVA incorrect"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'subject_to_vat',
            'vat_number': 'DE123456789',  # Format allemand
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert not form.is_valid()
        assert 'vat_number' in form.errors
        assert 'FR' in str(form.errors['vat_number'])
    
    def test_form_clears_vat_number_when_not_subject(self):
        """Test nettoyage numéro TVA quand non assujetti"""
        organization = OrganizationFactory()
        billing = organization.billing
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
            'vat_number': 'FR12345678901',  # Sera vidé
        }
        
        form = OrgBillingForm(data, instance=billing)
        assert form.is_valid()
        
        saved_billing = form.save()
        assert saved_billing.vat_number == ''


@pytest.mark.django_db
class TestBillingSettingsViews:
    """Tests des vues de paramètres de facturation"""
    
    def test_billing_settings_get_anonymous_redirected(self):
        """Test redirection utilisateur anonyme"""
        client = Client()
        response = client.get(reverse('auth:billing_settings'))
        
        assert response.status_code == 302
        assert '/auth/login/' in response.url
    
    def test_billing_settings_get_non_admin_forbidden(self):
        """Test accès refusé pour non-admin selon roadmap 11"""
        user = UserFactory()
        organization = OrganizationFactory()
        # Créer un membership non-admin (read_only par défaut)
        from tests.factories import MembershipFactory
        membership = MembershipFactory(user=user, organization=organization, role='read_only')
        
        client = Client()
        client.force_login(user)
        
        # Simuler la session avec l'organisation courante
        session = client.session
        session['current_org_id'] = organization.id
        session.save()
        
        response = client.get(reverse('auth:billing_settings'))
        
        # Devrait être redirigé ou recevoir 403
        assert response.status_code in [302, 403]
    
    def test_billing_settings_get_admin_success(self):
        """Test accès autorisé pour admin"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Simuler la session avec l'organisation courante
        session = client.session
        session['current_org_id'] = organization.id
        session.save()
        
        response = client.get(reverse('auth:billing_settings'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'billing' in response.context
        assert response.context['billing'] == organization.billing
    
    def test_billing_settings_post_valid_data_updates_checklist(self):
        """Test POST valide met à jour la checklist selon roadmap 11"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Simuler la session avec l'organisation courante
        session = client.session
        session['current_org_id'] = organization.id
        session.save()
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'subject_to_vat',
            'vat_number': 'FR12345678901',
            'siret': '12345678901234',
        }
        
        response = client.post(reverse('auth:billing_settings'), data)
        
        # Vérifier redirection
        assert response.status_code == 302
        assert response.url == reverse('auth:billing_settings')
        
        # Vérifier sauvegarde
        organization.billing.refresh_from_db()
        billing = organization.billing
        assert billing.legal_name == 'Mon Entreprise SARL'
        assert billing.vat_number == 'FR12345678901'
        
        # Vérifier mise à jour checklist
        organization.setup_checklist.refresh_from_db()
        checklist = organization.setup_checklist
        assert checklist.state.get('company_info') == 'done'
        assert checklist.state.get('taxes') == 'done'
        
        # Vérifier message de succès
        response = client.get(reverse('auth:billing_settings'))
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'Informations de facturation mises à jour' in str(messages[0])
    
    def test_billing_settings_post_minimal_valid_updates_partial_checklist(self):
        """Test POST minimal valide (non assujetti) met à jour partiellement la checklist"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Simuler la session avec l'organisation courante
        session = client.session
        session['current_org_id'] = organization.id
        session.save()
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
        }
        
        response = client.post(reverse('auth:billing_settings'), data)
        
        # Vérifier redirection
        assert response.status_code == 302
        
        # Vérifier mise à jour checklist
        organization.setup_checklist.refresh_from_db()
        checklist = organization.setup_checklist
        assert checklist.state.get('company_info') == 'done'
        assert checklist.state.get('taxes') == 'done'  # Non assujetti = complet
    
    def test_billing_settings_post_invalid_siret_shows_error(self):
        """Test POST avec SIRET invalide affiche erreur inline selon roadmap 11"""
        user = UserFactory()
        membership = AdminMembershipFactory(user=user)
        organization = membership.organization
        
        client = Client()
        client.force_login(user)
        
        # Simuler la session avec l'organisation courante
        session = client.session
        session['current_org_id'] = organization.id
        session.save()
        
        data = {
            'legal_name': 'Mon Entreprise SARL',
            'billing_address_line1': '123 Rue de la Paix',
            'billing_postal_code': '75001',
            'billing_city': 'Paris',
            'billing_country': 'France',
            'vat_status': 'not_subject_to_vat',
            'siret': '123',  # SIRET invalide
        }
        
        response = client.post(reverse('auth:billing_settings'), data)
        
        # Vérifier erreur affichée
        assert response.status_code == 200
        form = response.context['form']
        assert 'siret' in form.errors
        assert '14 chiffres' in str(form.errors['siret'])
        
        # Vérifier pas de crash
        assert 'form' in response.context
