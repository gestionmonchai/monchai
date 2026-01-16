"""
URLs pour système d'import générique
Endpoints REST selon roadmaps CSV 1-5
"""

from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    # CSV_1: Upload & Preview
    path('<str:entity>/televersement/', views.upload_file, name='upload_file'),
    path('<int:job_id>/apercu/', views.preview_file, name='preview_file'),
    
    # CSV_2: Mapping & Schema
    path('schema/<str:entity>/', views.get_entity_schema, name='entity_schema'),
    path('<int:job_id>/mappage-auto/', views.auto_map_columns, name='auto_map_columns'),
    
    # CSV_4: Status & Polling
    path('<int:job_id>/statut/', views.job_status, name='job_status'),
    
    # CSV_5: Historique
    path('taches/', views.list_jobs, name='list_jobs'),
]
