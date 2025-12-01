"""
URLs pour l'API d'authentification (/api/auth/*)
Invariant technique : chemins stables /api/auth/*
Implémentation selon roadmap 02_auth_flow.txt
"""

from django.urls import path
from . import api_views

app_name = 'api_auth'

urlpatterns = [
    # Authentification API
    path('session/', api_views.LoginAPIView.as_view(), name='login'),
    path('whoami/', api_views.WhoAmIAPIView.as_view(), name='whoami'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='logout'),
    
    # Utilitaires
    path('csrf/', api_views.CSRFTokenAPIView.as_view(), name='csrf_token'),
]
