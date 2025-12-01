from django.urls import path
from .views import help_assistant, help_query

app_name = 'ai'

urlpatterns = [
    path('help/', help_assistant, name='help_assistant'),
    path('help/query', help_query, name='help_query'),
]
