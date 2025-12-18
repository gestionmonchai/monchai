from django.urls import path
from . import views
from .views_parcelle_journal import ParcelleJournalView, ParcelleJournalPartial
from .views_quick_ops import ParcelleQuickOpCreateView
from .views_journal_entry import (
    JournalEntryDetailView,
    JournalEntryUpdateView,
    JournalEntryDeleteView,
)

app_name = 'viticulture'

urlpatterns = [
    path('cuvee/<int:pk>/change/', views.cuvee_change, name='cuvee_change'),
    # Journal de parcelle (lecture seule)
    path('parcelles/<int:pk>/journal/', ParcelleJournalView.as_view(), name='parcelle_journal'),
    path('parcelles/<int:pk>/journal/partial/', ParcelleJournalPartial.as_view(), name='parcelle_journal_partial'),
    # Création d'opérations rapides (lecture/écriture via journal)
    path('parcelles/<int:pk>/operation/<str:code>/', ParcelleQuickOpCreateView.as_view(), name='parcelle_quick_op'),
    
    # Gestion des entrées du journal (détail, modification, suppression)
    path('journal/<int:pk>/', JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('journal/<int:pk>/modifier/', JournalEntryUpdateView.as_view(), name='journal_entry_update'),
    path('journal/<int:pk>/supprimer/', JournalEntryDeleteView.as_view(), name='journal_entry_delete'),
]
