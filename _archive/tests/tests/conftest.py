"""
Configuration pytest et fixtures communes - Sprint 08
"""

import pytest
from django.test import Client


@pytest.fixture
def client():
    """Client de test Django"""
    return Client()
