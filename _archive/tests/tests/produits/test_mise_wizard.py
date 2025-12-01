from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.production.models import LotTechnique
from apps.produits.models import Mise, LotCommercial
from apps.drm.models import DRMLine
from datetime import date


class MiseWizardFlowTest(TestCase):
    def setUp(self):
        self.c = Client()
        User = get_user_model()
        self.user = User.objects.create_user(email='user@example.com', password='pass1234')
        self.c.login(email='user@example.com', password='pass1234')
        self.lot = LotTechnique.objects.create(code='LT-2025-010', campagne='2025-2026', volume_l=100)

    def test_wizard_creates_mise_and_lots_and_drm(self):
        # Step 1: select source
        url = reverse('production:mise_new')
        resp = self.c.post(url + '?step=1', data={
            'step': '1',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-lot_tech_source': str(self.lot.id),
            'form-0-volume_l': '50',
        })
        self.assertEqual(resp.status_code, 302)
        # Step 2: define format and meta
        resp = self.c.post(reverse('production:mise_new') + '?step=2', data={
            'step': '2',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-format_ml': '750',
            'form-0-quantite_unites': '40',
            'form-0-pertes_pct': '2',
            'notes': 'Test mise',
        })
        self.assertEqual(resp.status_code, 302)
        # Step 3: confirm
        resp = self.c.post(reverse('production:mise_new') + '?step=3', data={
            'step': '3',
            'confirmer': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        mise = Mise.objects.first()
        self.assertIsNotNone(mise)
        self.assertTrue(LotCommercial.objects.filter(mise=mise).exists())
        self.assertTrue(DRMLine.objects.filter(ref_kind='mise', ref_id=mise.id).exists())
        self.lot.refresh_from_db()
        self.assertLess(float(self.lot.volume_l), 100.0)
