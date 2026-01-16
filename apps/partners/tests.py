"""
Tests pour l'app Partners (Tiers unifiés)
"""

from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import Organization, User, Membership
from .models import (
    Partner, PartnerRole, Address, ContactPerson,
    ClientProfile, SupplierProfile, PartnerTag
)


class PartnerModelTest(TestCase):
    """Tests pour le modèle Partner"""
    
    @classmethod
    def setUpTestData(cls):
        # Créer une organisation de test
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        
        # Créer les rôles par défaut
        PartnerRole.ensure_defaults()
    
    def test_partner_creation(self):
        """Test création d'un partenaire simple"""
        partner = Partner.objects.create(
            organization=self.organization,
            name="Test Partner",
            partner_type="company"
        )
        
        self.assertIsNotNone(partner.id)
        self.assertIsNotNone(partner.code)
        self.assertTrue(partner.code.startswith("PAR-"))
        self.assertEqual(partner.name_normalized, "test partner")
    
    def test_partner_with_roles(self):
        """Test création avec rôles multiples"""
        partner = Partner.objects.create(
            organization=self.organization,
            name="Multi Role Partner",
            partner_type="company"
        )
        
        # Ajouter rôles client et fournisseur
        partner.add_role('client')
        partner.add_role('supplier')
        
        self.assertTrue(partner.is_client)
        self.assertTrue(partner.is_supplier)
        self.assertFalse(partner.is_prospect)
        self.assertEqual(len(partner.role_codes), 2)
    
    def test_partner_code_generation(self):
        """Test génération codes uniques"""
        p1 = Partner.objects.create(
            organization=self.organization,
            name="Partner 1"
        )
        p2 = Partner.objects.create(
            organization=self.organization,
            name="Partner 2"
        )
        
        self.assertNotEqual(p1.code, p2.code)
        self.assertNotEqual(p1.display_id, p2.display_id)
    
    def test_partner_name_normalization(self):
        """Test normalisation du nom"""
        partner = Partner.objects.create(
            organization=self.organization,
            name="CHÂTEAU DU VIN"
        )
        
        self.assertEqual(partner.name_normalized, "chateau du vin")


class AddressModelTest(TestCase):
    """Tests pour le modèle Address"""
    
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        cls.partner = Partner.objects.create(
            organization=cls.organization,
            name="Test Partner"
        )
    
    def test_address_creation(self):
        """Test création d'une adresse"""
        address = Address.objects.create(
            organization=self.organization,
            partner=self.partner,
            street="123 Rue du Vin",
            postal_code="33000",
            city="Bordeaux",
            country="FR",
            address_type="billing",
            is_default=True
        )
        
        self.assertEqual(address.partner, self.partner)
        self.assertTrue(address.is_default)
        self.assertIn("Bordeaux", address.full_address)
    
    def test_default_address_uniqueness(self):
        """Test qu'une seule adresse peut être par défaut"""
        addr1 = Address.objects.create(
            organization=self.organization,
            partner=self.partner,
            street="Adresse 1",
            postal_code="33000",
            city="Bordeaux",
            is_default=True
        )
        
        addr2 = Address.objects.create(
            organization=self.organization,
            partner=self.partner,
            street="Adresse 2",
            postal_code="75000",
            city="Paris",
            is_default=True
        )
        
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)


class ContactPersonModelTest(TestCase):
    """Tests pour le modèle ContactPerson"""
    
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        cls.partner = Partner.objects.create(
            organization=cls.organization,
            name="Test Partner"
        )
    
    def test_contact_creation(self):
        """Test création d'un interlocuteur"""
        contact = ContactPerson.objects.create(
            organization=self.organization,
            partner=self.partner,
            first_name="Jean",
            last_name="Dupont",
            email="jean@example.com",
            role="buyer"
        )
        
        self.assertEqual(contact.full_name, "Jean Dupont")
        self.assertEqual(contact.partner, self.partner)


class ClientProfileModelTest(TestCase):
    """Tests pour le modèle ClientProfile"""
    
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        cls.partner = Partner.objects.create(
            organization=cls.organization,
            name="Test Client"
        )
    
    def test_client_profile_creation(self):
        """Test création d'un profil client"""
        profile = ClientProfile.objects.create(
            organization=self.organization,
            partner=self.partner,
            payment_terms="30d",
            credit_limit=10000
        )
        
        self.assertEqual(profile.partner, self.partner)
        self.assertEqual(profile.available_credit, 10000)
    
    def test_over_limit_detection(self):
        """Test détection dépassement encours"""
        profile = ClientProfile.objects.create(
            organization=self.organization,
            partner=self.partner,
            credit_limit=5000,
            current_balance=6000
        )
        
        self.assertTrue(profile.is_over_limit)


class PartnerViewsTest(TestCase):
    """Tests pour les vues Partners"""
    
    @classmethod
    def setUpTestData(cls):
        # Créer utilisateur et organisation
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        cls.membership = Membership.objects.create(
            user=cls.user,
            organization=cls.organization,
            status="active"
        )
        
        # Créer les rôles
        PartnerRole.ensure_defaults()
        
        # Créer quelques partenaires
        cls.partner = Partner.objects.create(
            organization=cls.organization,
            name="Test Partner",
            email="partner@test.com"
        )
        cls.partner.add_role('client')
    
    def setUp(self):
        self.client = Client()
        self.client.login(email="test@example.com", password="testpass123")
        # Simuler la session avec organisation active
        session = self.client.session
        session['active_organization_id'] = str(self.organization.id)
        session.save()
    
    def test_partners_list_view(self):
        """Test vue liste des partenaires"""
        response = self.client.get(reverse('partners:partners_list'))
        # Devrait rediriger si pas d'org ou retourner 200
        self.assertIn(response.status_code, [200, 302])
    
    def test_clients_list_view(self):
        """Test vue liste des clients"""
        response = self.client.get(reverse('partners:clients_list'))
        self.assertIn(response.status_code, [200, 302])
    
    def test_suppliers_list_view(self):
        """Test vue liste des fournisseurs"""
        response = self.client.get(reverse('partners:suppliers_list'))
        self.assertIn(response.status_code, [200, 302])


class PartnerAPITest(TestCase):
    """Tests pour les APIs Partners"""
    
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            name="Test Domaine"
        )
        
        cls.user = User.objects.create_user(
            email="api@example.com",
            password="testpass123"
        )
        
        cls.membership = Membership.objects.create(
            user=cls.user,
            organization=cls.organization,
            status="active"
        )
        
        PartnerRole.ensure_defaults()
        
        # Créer partenaires de test
        for i in range(5):
            p = Partner.objects.create(
                organization=cls.organization,
                name=f"Partner {i}",
                email=f"partner{i}@test.com"
            )
            p.add_role('client')
    
    def setUp(self):
        self.client = Client()
        self.client.login(email="api@example.com", password="testpass123")
        session = self.client.session
        session['active_organization_id'] = str(self.organization.id)
        session.save()
    
    def test_suggestions_api(self):
        """Test API suggestions"""
        response = self.client.get(
            reverse('partners:partners_suggestions_api'),
            {'q': 'Partner'}
        )
        self.assertIn(response.status_code, [200, 302])
