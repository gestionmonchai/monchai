from django.urls import path
from . import views
from .views_parcelle_journal import ParcelleJournalView, ParcelleJournalPartial
from .views_quick_ops import ParcelleQuickOpCreateView

app_name = 'viticulture'

urlpatterns = [
    path('cuvee/<uuid:pk>/change/', views.cuvee_change, name='cuvee_change'),
    # Journal de parcelle (lecture seule)
    path('parcelles/<int:pk>/journal/', ParcelleJournalView.as_view(), name='parcelle_journal'),
    path('parcelles/<int:pk>/journal/partial/', ParcelleJournalPartial.as_view(), name='parcelle_journal_partial'),
    # Création d'opérations rapides (lecture/écriture via journal)
    path('parcelles/<int:pk>/operation/<str:code>/', ParcelleQuickOpCreateView.as_view(), name='parcelle_quick_op'),
]
