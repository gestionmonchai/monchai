from django.test import TestCase, Client


class RedirectsTest(TestCase):
    def setUp(self):
        self.c = Client()

    def assertRedirect301(self, src, dst):
        resp = self.c.get(src, follow=False)
        assert resp.status_code == 301, f"{src} → {resp.status_code}"
        loc = resp['Location']
        assert loc == dst, f"{src} should redirect to {dst}, got {loc}"

    def test_catalogue_redirects(self):
        self.assertRedirect301('/catalogue/', '/produits/cuvees/')
        self.assertRedirect301('/catalogue/produits/', '/produits/cuvees/')
        self.assertRedirect301('/catalogue/produits/cuvees/nouveau/', '/produits/cuvees/nouveau/')
        self.assertRedirect301('/catalogue/produits/lots/', '/production/lots-techniques/')

    def test_clients_redirects(self):
        self.assertRedirect301('/clients/', '/ventes/clients/')
        self.assertRedirect301('/clients/nouveau/', '/ventes/clients/nouveau/')

    def test_stocks_redirects(self):
        self.assertRedirect301('/stocks/', '/stock/mouvements/')
        self.assertRedirect301('/stocks/inventaire/', '/stock/inventaire/')
