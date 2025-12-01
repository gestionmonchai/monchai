from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.production.models import Parcelle, VendangeReception, LotTechnique
from django.urls import reverse
from datetime import date


class VendangesFlowTest(TestCase):
    def setUp(self):
        self.c = Client()
        User = get_user_model()
        self.user = User.objects.create_user(email='user@example.com', password='pass1234')
        self.c.login(email='user@example.com', password='pass1234')
        self.parcelle = Parcelle.objects.create(nom='Les Vignes', cepage='Syrah', surface_ha=1.2)

    def test_create_vendange_creates_lot_technique(self):
        url = reverse('production:vendange_new')
        resp = self.c.post(url, data={
            'parcelle': self.parcelle.id,
            'date': date.today().isoformat(),
            'poids_kg': '1200',
            'degre_potentiel': '12.5',
            'notes': 'Test vendange',
            'auto_create_lot': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        v = VendangeReception.objects.first()
        self.assertIsNotNone(v)
        lot = LotTechnique.objects.filter(source=v).first()
        self.assertIsNotNone(lot)
        # volume approximated poids/1.2
        self.assertGreater(float(lot.volume_l), 0)

    def test_list_and_detail(self):
        v = VendangeReception.objects.create(parcelle=self.parcelle, date=date.today(), poids_kg=1000)
        list_url = reverse('production:vendanges_list')
        d_url = reverse('production:vendange_detail', kwargs={'pk': v.id})
        self.assertEqual(self.c.get(list_url).status_code, 200)
        self.assertEqual(self.c.get(d_url).status_code, 200)
