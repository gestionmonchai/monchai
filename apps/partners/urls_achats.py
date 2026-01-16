"""
URLs pour l'intégration des partenaires dans le module Achats
Monté sous /achats/fournisseurs/
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.suppliers_list_simple, name='suppliers_list'),
    path('tableau/', views.partners_table_ajax, {'role': 'supplier'}, name='suppliers_table'),
]
