from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.production.models import LotTechnique
from datetime import date


class AssemblageFlowTest(TestCase):
    def setUp(self):
        self.c = Client()
        User = get_user_model()
        self.user = User.objects.create_user(email='user@example.com', password='pass1234')
        self.c.login(email='user@example.com', password='pass1234')

    def test_create_assemblage_decrements_sources_and_creates_result(self):
        lot1 = LotTechnique.objects.create(code='LT-2025-001', campagne='2025-2026', volume_l=100)
        lot2 = LotTechnique.objects.create(code='LT-2025-002', campagne='2025-2026', volume_l=100)
        url = reverse('production:assemblage_new')
        data = {
            'code': '',
            'date': date.today().isoformat(),
            'campagne': '2025-2026',
            'notes': 'Test',
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-lot_source': str(lot1.id),
            'form-0-volume_l': '50',
            'form-1-lot_source': str(lot2.id),
            'form-1-volume_l': '30',
        }
        resp = self.c.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        lot1.refresh_from_db(); lot2.refresh_from_db()
        self.assertEqual(float(lot1.volume_l), 50.0)
        self.assertEqual(float(lot2.volume_l), 70.0)
        # Detail should render
        detail_url = resp['Location']
        self.assertEqual(self.c.get(detail_url).status_code, 200)
