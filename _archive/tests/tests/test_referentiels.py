"""
Tests pour les référentiels viticoles
Roadmap Cut #3 : Référentiels (starter pack)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.referentiels.models import Cepage, Parcelle, Unite, Cuvee, Entrepot
from apps.referentiels.forms import CepageForm, ParcelleForm
from tests.factories import UserFactory, OrganizationFactory, MembershipFactory

User = get_user_model()


class CepageModelTest(TestCase):
    """Tests du modèle Cepage"""
    
    def setUp(self):
        self.organization = OrganizationFactory()
    
    def test_create_cepage_with_defaults(self):
        """Test création cépage avec valeurs par défaut"""
        cepage = Cepage.objects.create(
            organization=self.organization,
            nom="Cabernet Sauvignon"
        )
        
        self.assertEqual(cepage.nom, "Cabernet Sauvignon")
        self.assertEqual(cepage.couleur, "rouge")  # Valeur par défaut
        self.assertEqual(cepage.code, "")
        self.assertEqual(str(cepage), "Cabernet Sauvignon (Rouge)")
    
    def test_create_cepage_complete(self):
        """Test création cépage avec tous les champs"""
        cepage = Cepage.objects.create(
            organization=self.organization,
            nom="Chardonnay",
            code="CH",
            couleur="blanc",
            notes="Cépage blanc noble"
        )
        
        self.assertEqual(cepage.nom, "Chardonnay")
        self.assertEqual(cepage.code, "CH")
        self.assertEqual(cepage.couleur, "blanc")
        self.assertEqual(cepage.notes, "Cépage blanc noble")
    
    def test_unique_together_constraint(self):
        """Test contrainte d'unicité organization + nom"""
        Cepage.objects.create(
            organization=self.organization,
            nom="Merlot"
        )
        
        # Même nom dans organisation différente → OK
        other_org = OrganizationFactory()
        cepage2 = Cepage.objects.create(
            organization=other_org,
            nom="Merlot"
        )
        self.assertEqual(cepage2.nom, "Merlot")
        
        # Vérifier qu'on a bien 2 cépages avec le même nom mais dans des orgs différentes
        merlot_count = Cepage.objects.filter(nom="Merlot").count()
        self.assertEqual(merlot_count, 2)
    
    def test_get_absolute_url(self):
        """Test URL absolue du cépage"""
        cepage = Cepage.objects.create(
            organization=self.organization,
            nom="Syrah"
        )
        
        expected_url = reverse('referentiels:cepage_detail', kwargs={'pk': cepage.pk})
        self.assertEqual(cepage.get_absolute_url(), expected_url)


class ParcelleModelTest(TestCase):
    """Tests du modèle Parcelle"""
    
    def setUp(self):
        self.organization = OrganizationFactory()
    
    def test_create_parcelle_minimal(self):
        """Test création parcelle avec champs minimaux"""
        parcelle = Parcelle.objects.create(
            organization=self.organization,
            nom="Les Vignes du Haut",
            surface=2.5
        )
        
        self.assertEqual(parcelle.nom, "Les Vignes du Haut")
        self.assertEqual(parcelle.surface, 2.5)
        self.assertEqual(str(parcelle), "Les Vignes du Haut (2.5 ha)")
    
    def test_create_parcelle_complete(self):
        """Test création parcelle avec tous les champs"""
        parcelle = Parcelle.objects.create(
            organization=self.organization,
            nom="Clos Saint-Pierre",
            surface=1.25,
            lieu_dit="Les Coteaux",
            commune="Châteauneuf-du-Pape",
            appellation="Châteauneuf-du-Pape AOC",
            notes="Exposition sud, sol argilo-calcaire"
        )
        
        self.assertEqual(parcelle.lieu_dit, "Les Coteaux")
        self.assertEqual(parcelle.commune, "Châteauneuf-du-Pape")
        self.assertEqual(parcelle.appellation, "Châteauneuf-du-Pape AOC")


class CepageFormTest(TestCase):
    """Tests du formulaire CepageForm"""
    
    def setUp(self):
        self.organization = OrganizationFactory()
    
    def test_form_valid_minimal(self):
        """Test formulaire valide avec champs minimaux"""
        data = {
            'nom': 'Pinot Noir',
            'couleur': 'rouge'
        }
        
        form = CepageForm(data=data, organization=self.organization)
        self.assertTrue(form.is_valid())
    
    def test_form_valid_complete(self):
        """Test formulaire valide avec tous les champs"""
        data = {
            'nom': 'Sauvignon Blanc',
            'code': 'SB',
            'couleur': 'blanc',
            'notes': 'Cépage aromatique'
        }
        
        form = CepageForm(data=data, organization=self.organization)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_empty_nom(self):
        """Test formulaire invalide sans nom"""
        data = {
            'couleur': 'rouge'
        }
        
        form = CepageForm(data=data, organization=self.organization)
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)
    
    def test_form_clean_nom_duplicate(self):
        """Test validation nom en double"""
        # Créer un cépage existant
        Cepage.objects.create(
            organization=self.organization,
            nom="Grenache"
        )
        
        # Tenter de créer un autre avec même nom
        data = {
            'nom': 'Grenache',
            'couleur': 'rouge'
        }
        
        form = CepageForm(data=data, organization=self.organization)
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)


class CepageViewTest(TestCase):
    """Tests des vues Cepage"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.organization = OrganizationFactory()
        self.membership = MembershipFactory(
            user=self.user,
            organization=self.organization,
            role='admin'
        )
        
        # Créer quelques cépages de test
        self.cepage1 = Cepage.objects.create(
            organization=self.organization,
            nom="Cabernet Sauvignon",
            code="CS",
            couleur="rouge"
        )
        self.cepage2 = Cepage.objects.create(
            organization=self.organization,
            nom="Chardonnay",
            couleur="blanc"
        )
    
    def test_referentiels_home_access(self):
        """Test accès page d'accueil référentiels"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get(reverse('referentiels:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Référentiels')
        self.assertContains(response, '2 cépage')  # Pluriel avec 2 cépages
    
    def test_cepage_list_access(self):
        """Test accès liste des cépages"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get(reverse('referentiels:cepage_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cabernet Sauvignon')
        self.assertContains(response, 'Chardonnay')
    
    def test_cepage_detail_access(self):
        """Test accès détail cépage"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get(reverse('referentiels:cepage_detail', kwargs={'pk': self.cepage1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cabernet Sauvignon')
        self.assertContains(response, 'CS')  # Code
    
    def test_cepage_create_get(self):
        """Test affichage formulaire création cépage"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get(reverse('referentiels:cepage_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouveau cépage')
    
    def test_cepage_create_post_valid(self):
        """Test création cépage via POST"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        data = {
            'nom': 'Merlot',
            'code': 'ME',
            'couleur': 'rouge',
            'notes': 'Cépage souple'
        }
        
        response = self.client.post(reverse('referentiels:cepage_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect après création
        
        # Vérifier que le cépage a été créé
        cepage = Cepage.objects.get(nom='Merlot', organization=self.organization)
        self.assertEqual(cepage.code, 'ME')
        self.assertEqual(cepage.couleur, 'rouge')
    
    def test_cepage_update_get(self):
        """Test affichage formulaire modification cépage"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        response = self.client.get(reverse('referentiels:cepage_update', kwargs={'pk': self.cepage1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier')
        self.assertContains(response, 'Cabernet Sauvignon')
    
    def test_cepage_update_post_valid(self):
        """Test modification cépage via POST"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        data = {
            'nom': 'Cabernet Sauvignon',
            'code': 'CAB',  # Changement du code
            'couleur': 'rouge',
            'notes': 'Cépage noble de Bordeaux'
        }
        
        response = self.client.post(reverse('referentiels:cepage_update', kwargs={'pk': self.cepage1.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Vérifier la modification
        self.cepage1.refresh_from_db()
        self.assertEqual(self.cepage1.code, 'CAB')
        self.assertEqual(self.cepage1.notes, 'Cépage noble de Bordeaux')
    
    def test_cepage_delete_post(self):
        """Test suppression cépage"""
        self.client.force_login(self.user)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        # Compter avant suppression
        count_before = Cepage.objects.filter(organization=self.organization).count()
        
        response = self.client.post(reverse('referentiels:cepage_delete', kwargs={'pk': self.cepage1.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Vérifier la suppression
        count_after = Cepage.objects.filter(organization=self.organization).count()
        self.assertEqual(count_after, count_before - 1)
        
        # Vérifier que le cépage n'existe plus
        with self.assertRaises(Cepage.DoesNotExist):
            Cepage.objects.get(pk=self.cepage1.pk)


class PermissionsTest(TestCase):
    """Tests des permissions sur les référentiels"""
    
    def setUp(self):
        self.client = Client()
        self.organization = OrganizationFactory()
        
        # Utilisateur read_only
        self.user_readonly = UserFactory()
        self.membership_readonly = MembershipFactory(
            user=self.user_readonly,
            organization=self.organization,
            role='read_only'
        )
        
        # Utilisateur editor
        self.user_editor = UserFactory()
        self.membership_editor = MembershipFactory(
            user=self.user_editor,
            organization=self.organization,
            role='editor'
        )
        
        self.cepage = Cepage.objects.create(
            organization=self.organization,
            nom="Test Cépage"
        )
    
    def test_readonly_can_view_but_not_edit(self):
        """Test que read_only peut voir mais pas modifier"""
        self.client.force_login(self.user_readonly)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        # Peut voir la liste
        response = self.client.get(reverse('referentiels:cepage_list'))
        self.assertEqual(response.status_code, 200)
        
        # Peut voir le détail
        response = self.client.get(reverse('referentiels:cepage_detail', kwargs={'pk': self.cepage.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Ne peut pas créer
        response = self.client.get(reverse('referentiels:cepage_create'))
        self.assertEqual(response.status_code, 403)
        
        # Ne peut pas modifier
        response = self.client.get(reverse('referentiels:cepage_update', kwargs={'pk': self.cepage.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_editor_can_edit_but_not_delete(self):
        """Test que editor peut modifier mais pas supprimer"""
        self.client.force_login(self.user_editor)
        
        session = self.client.session
        session['current_org_id'] = self.organization.id
        session.save()
        
        # Peut créer
        response = self.client.get(reverse('referentiels:cepage_create'))
        self.assertEqual(response.status_code, 200)
        
        # Peut modifier
        response = self.client.get(reverse('referentiels:cepage_update', kwargs={'pk': self.cepage.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Ne peut pas supprimer (admin requis)
        response = self.client.post(reverse('referentiels:cepage_delete', kwargs={'pk': self.cepage.pk}))
        self.assertEqual(response.status_code, 403)
