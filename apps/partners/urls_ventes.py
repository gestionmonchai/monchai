"""
URLs pour l'intégration des partenaires dans le module Ventes
Monté sous /ventes/clients/
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.clients_list_simple, name='clients_list'),
    path('tableau/', views.partners_table_ajax, {'role': 'client'}, name='clients_table'),
]
