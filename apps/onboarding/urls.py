"""
URLs pour l'onboarding - Roadmap 09
Route: GET /onboarding/checklist/ (require_membership)
"""

from django.urls import path
from .views import (
    checklist_view,
    onboarding_flow,
    onboarding_skip_step,
    onboarding_dismiss,
    onboarding_reset,
)

app_name = 'onboarding'

urlpatterns = [
    # Guided flow root
    path('', onboarding_flow, name='flow'),

    # Existing org-setup checklist
    path('liste-taches/', checklist_view, name='checklist'),

    # Actions
    path('passer/<str:step_key>/', onboarding_skip_step, name='skip'),
    path('ignorer/', onboarding_dismiss, name='dismiss'),
    path('reinitialiser/', onboarding_reset, name='reset'),
]
