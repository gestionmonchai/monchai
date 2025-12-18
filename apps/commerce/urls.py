from django.urls import path
from . import views, api

app_name = 'commerce'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:side>/', views.dashboard, name='dashboard'),
    
    # Documents List
    path('documents/<str:side>/', views.DocumentListView.as_view(), name='document_list'),
    
    # Document CRUD
    path('document/new/<str:side>/<str:type>/', views.DocumentCreateView.as_view(), name='document_create'),
    path('document/<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('document/<uuid:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('document/<uuid:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Actions
    path('document/<uuid:pk>/transform/<str:target_type>/', views.transform_document, name='document_transform'),
    path('document/<uuid:pk>/validate/', views.validate_document, name='document_validate'),
    path('document/<uuid:pk>/execute/', views.execute_document, name='document_execute'),
    path('document/<uuid:pk>/payment/add/', views.add_payment, name='payment_add'),
    path('document/<uuid:pk>/line/add/', views.add_line, name='line_add'),
    path('line/<uuid:pk>/delete/', views.delete_line, name='line_delete'),
    
    # Payments
    path('payments/<str:side>/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/schedule/<str:side>/', views.PaymentScheduleView.as_view(), name='payment_schedule'),
    
    # API
    path('api/sku/<int:pk>/', api.get_sku_details, name='api_sku_details'),
]
