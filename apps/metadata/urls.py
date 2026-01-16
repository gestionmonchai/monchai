"""
URLs pour l'app metadata
GIGA ROADMAP S4: Dashboard monitoring + admin feature flags
"""

from django.urls import path
from . import dashboard

app_name = 'metadata'

urlpatterns = [
    # Dashboard monitoring (staff only)
    path('surveillance/', dashboard.monitoring_dashboard, name='monitoring_dashboard'),
    path('fonctionnalites/', dashboard.feature_flags_admin, name='feature_flags_admin'),
]
