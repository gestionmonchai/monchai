import uuid
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _assert_anon_302(client, name, kwargs=None):
    url = reverse(name, kwargs=kwargs or {})
    resp = client.get(url)
    assert resp.status_code in (302, 301)


def test_stock_urls_require_login(client):
    _assert_anon_302(client, 'stock:dashboard')
    _assert_anon_302(client, 'stock:mouvements')
    _assert_anon_302(client, 'stock:inventaire_list')
    _assert_anon_302(client, 'stock:inventaire_new')
    _assert_anon_302(client, 'stock:entrepots')
    _assert_anon_302(client, 'stock:emplacements')

    pk = uuid.uuid4()
    _assert_anon_302(client, 'stock:inventaire_detail', {'pk': pk})
