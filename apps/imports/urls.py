"""
URLs pour système d'import générique
Endpoints REST selon roadmaps CSV 1-5
"""

from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    # CSV_1: Upload & Preview
    path('<str:entity>/upload/', views.upload_file, name='upload_file'),
    path('<int:job_id>/preview/', views.preview_file, name='preview_file'),
    
    # CSV_2: Mapping & Schema
    path('schema/<str:entity>/', views.get_entity_schema, name='entity_schema'),
    path('<int:job_id>/auto-map/', views.auto_map_columns, name='auto_map_columns'),
    
    # CSV_4: Status & Polling
    path('<int:job_id>/status/', views.job_status, name='job_status'),
    
    # CSV_5: Historique
    path('jobs/', views.list_jobs, name='list_jobs'),
]
