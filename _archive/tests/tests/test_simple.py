"""
Test simple pour vérifier la configuration - Sprint 08
"""

import pytest
from django.test import Client
from django.urls import reverse


def test_simple():
    """Test simple pour vérifier que pytest fonctionne"""
    assert True


@pytest.mark.django_db
def test_login_page_accessible():
    """Test que la page de login est accessible"""
    client = Client()
    response = client.get(reverse('auth:login'))
    assert response.status_code == 200
