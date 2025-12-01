from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid


class RoutesSmokeTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(email='test@example.com', password='pass1234')

    def test_named_routes_exist(self):
        # Ensure each route returns 200 when logged in or 302 if login required
        self.client.login(email='test@example.com', password='pass1234')
        uid = uuid.UUID('00000000-0000-0000-0000-000000000000')

        route_names = [
            # Production
            ('production:parcelles_list', {}),
            ('production:parcelle_new', {}),
            ('production:parcelle_detail', {'pk': uid}),
            ('production:vendanges_list', {}),
            ('production:vendange_new', {}),
            ('production:vendange_detail', {'pk': uid}),
            ('production:lots_tech_list', {}),
            ('production:lot_tech_detail', {'pk': uid}),
            ('production:assemblage_new', {}),
            ('production:assemblage_detail', {'pk': uid}),
            ('production:mises_list', {}),
            ('production:mise_new', {}),
            ('production:mise_detail', {'pk': uid}),
            # Produits
            ('produits:cuvees_list', {}),
            ('produits:cuvee_new', {}),
            ('produits:cuvee_detail', {'pk': uid}),
            ('produits:skus_list', {}),
            ('produits:sku_detail', {'pk': uid}),
            ('produits:lots_com_list', {}),
            ('produits:lot_com_detail', {'pk': uid}),
            # Ventes
            ('ventes:cmd_list', {}),
            ('ventes:cmd_new', {}),
            ('ventes:cmd_detail', {'pk': uid}),
            ('ventes:clients_list', {}),
            ('ventes:client_new', {}),
            ('ventes:client_detail', {'pk': uid}),
            # Stock & DRM
            ('stock:mov_list', {}),
            ('stock:inv_list', {}),
            ('drm:dashboard', {}),
            ('drm:brouillon', {}),
            ('drm:export', {}),
            # Ref
            ('ref:unites_list', {}),
            ('ref:formats_list', {}),
            ('ref:cepages_list', {}),
            ('ref:appellations_list', {}),
            # Public
            ('site:cuvee_public', {'slug': 'ma-jolie-cuvee-2024'}),
        ]

        for name, kwargs in route_names:
            url = reverse(name, kwargs=kwargs)
            resp = self.client.get(url)
            self.assertIn(resp.status_code, (200, 302), f"{name} → {resp.status_code}")
