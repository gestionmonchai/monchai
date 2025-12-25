"""
Tests pour le système TimelineEvent et MetaDetailView
======================================================
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from apps.accounts.models import Organization
from apps.core.models import TimelineEvent, Document
from apps.referentiels.models import Parcelle

User = get_user_model()


class TimelineEventTests(TestCase):
    """Tests pour le modèle TimelineEvent"""
    
    def setUp(self):
        """Configuration des fixtures de test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Org')
        self.parcelle = Parcelle.objects.create(
            organization=self.org,
            nom='Parcelle Test',
            surface=1.5
        )
    
    def test_create_timeline_event(self):
        """Test création d'un événement timeline"""
        event = TimelineEvent.create_for_object(
            self.parcelle,
            event_type='operation',
            title='Test opération',
            summary='Description de test',
            user=self.user
        )
        
        self.assertIsNotNone(event.pk)
        self.assertEqual(event.organization, self.org)
        self.assertEqual(event.event_type, 'operation')
        self.assertEqual(event.title, 'Test opération')
        self.assertEqual(event.created_by, self.user)
    
    def test_timeline_event_with_source(self):
        """Test création d'un événement avec objet source"""
        # Créer un autre objet comme source
        parcelle2 = Parcelle.objects.create(
            organization=self.org,
            nom='Parcelle Source',
            surface=2.0
        )
        
        event = TimelineEvent.create_for_object(
            self.parcelle,
            event_type='link',
            title='Liaison créée',
            source=parcelle2,
            user=self.user
        )
        
        self.assertIsNotNone(event.source_content_type)
        self.assertEqual(event.source_object_id, str(parcelle2.pk))
    
    def test_timeline_tenant_filtering(self):
        """Test filtrage par tenant"""
        # Créer une autre organisation
        org2 = Organization.objects.create(name='Autre Org')
        parcelle2 = Parcelle.objects.create(
            organization=org2,
            nom='Parcelle Autre',
            surface=1.0
        )
        
        # Créer des événements pour chaque org
        event1 = TimelineEvent.create_for_object(
            self.parcelle,
            event_type='note',
            title='Note org 1'
        )
        event2 = TimelineEvent.create_for_object(
            parcelle2,
            event_type='note',
            title='Note org 2'
        )
        
        # Vérifier le filtrage
        events_org1 = TimelineEvent.objects.filter(organization=self.org)
        events_org2 = TimelineEvent.objects.filter(organization=org2)
        
        self.assertEqual(events_org1.count(), 1)
        self.assertEqual(events_org2.count(), 1)
        self.assertEqual(events_org1.first().title, 'Note org 1')
    
    def test_timeline_event_types(self):
        """Test tous les types d'événements"""
        for event_type, label in TimelineEvent.EVENT_TYPES:
            event = TimelineEvent.create_for_object(
                self.parcelle,
                event_type=event_type,
                title=f'Test {label}'
            )
            self.assertEqual(event.event_type, event_type)
            self.assertEqual(event.get_event_type_display(), label)
    
    def test_timeline_ordering(self):
        """Test que les événements sont triés par date décroissante"""
        import time
        
        event1 = TimelineEvent.create_for_object(
            self.parcelle,
            event_type='note',
            title='Premier'
        )
        time.sleep(0.1)  # Petit délai pour avoir des dates différentes
        event2 = TimelineEvent.create_for_object(
            self.parcelle,
            event_type='note',
            title='Deuxième'
        )
        
        events = TimelineEvent.objects.filter(organization=self.org)
        self.assertEqual(events.first().title, 'Deuxième')  # Le plus récent en premier


class DocumentTests(TestCase):
    """Tests pour le modèle Document"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Org')
        self.parcelle = Parcelle.objects.create(
            organization=self.org,
            nom='Parcelle Test',
            surface=1.5
        )
    
    def test_create_document(self):
        """Test création d'un document"""
        ct = ContentType.objects.get_for_model(self.parcelle)
        
        doc = Document.objects.create(
            organization=self.org,
            content_type=ct,
            object_id=str(self.parcelle.pk),
            title='Document test',
            filename='test.pdf',
            file_type='pdf',
            category='other',
            created_by=self.user
        )
        
        self.assertIsNotNone(doc.pk)
        self.assertEqual(doc.organization, self.org)
        self.assertEqual(doc.title, 'Document test')


class MetaDetailViewTests(TestCase):
    """Tests pour le MetaDetailView"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Org')
        self.parcelle = Parcelle.objects.create(
            organization=self.org,
            nom='Parcelle Test',
            surface=1.5
        )
    
    def test_meta_modes_available(self):
        """Test que les modes sont disponibles"""
        from apps.referentiels.views_meta import ParcelleMetaDetailView
        
        view = ParcelleMetaDetailView()
        self.assertIn('fiche', view.meta_modes)
        self.assertIn('timeline', view.meta_modes)
        self.assertIn('relations', view.meta_modes)
    
    def test_default_mode_is_fiche(self):
        """Test que le mode par défaut est fiche"""
        from apps.referentiels.views_meta import ParcelleMetaDetailView
        
        view = ParcelleMetaDetailView()
        self.assertEqual(view.default_mode, 'fiche')
