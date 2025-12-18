"""
URLs pour l'authentification web (/auth/*)
Invariant technique : chemins stables /auth/*
Implémentation selon roadmap 02_auth_flow.txt
"""

from django.urls import path
from . import views, views_invitations, views_settings, views_profile, views_dashboard_api, views_shortcuts, views_orgs

app_name = 'auth'

urlpatterns = [
    # Authentification de base
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Réinitialisation mot de passe
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # First-run guard (onboarding)
    path('first-run/', views.first_run_view, name='first_run'),
    path('first-run/org/', views.create_organization_view, name='create_organization'),
    
    # Gestion des rôles (Roadmap 04)
    path('settings/roles/', views.roles_management_view, name='roles_management'),
    path('settings/roles/invite/', views.invite_user_view, name='invite_user'),
    path('settings/roles/change/<int:membership_id>/', views.change_role_view, name='change_role'),
    path('settings/roles/deactivate/<int:membership_id>/', views.deactivate_member_view, name='deactivate_member'),
    
    # Invitations (Roadmap 07)
    path('invite/accept/<str:token>/', views_invitations.accept_invitation, name='accept_invitation'),
    path('invite/send/', views_invitations.send_invitation, name='send_invitation'),
    path('invite/cancel/<int:invitation_id>/', views_invitations.cancel_invitation, name='cancel_invitation'),
    path('invite/resend/<int:invitation_id>/', views_invitations.resend_invitation, name='resend_invitation'),
    
    # Paramètres (Roadmap 09)
    path('settings/billing/', views_settings.billing_settings, name='billing_settings'),
    path('settings/general/', views_settings.general_settings, name='general_settings'),
    
    # Profil utilisateur (Roadmap 10)
    path('me/profile/', views_profile.profile_view, name='profile'),
    path('me/team/<int:member_id>/', views_profile.member_detail_view, name='member_detail'),
    
    # Dashboard personnalisable
    path('dashboard/configure/', views.dashboard_configure, name='dashboard_configure'),
    
    # API Dashboard
    path('api/dashboard/config/', views_dashboard_api.save_dashboard_config, name='api_save_dashboard_config'),
    path('api/dashboard/widget/add/', views_dashboard_api.add_widget, name='api_add_widget'),
    path('api/dashboard/widget/remove/', views_dashboard_api.remove_widget, name='api_remove_widget'),
    path('api/dashboard/widget/reorder/', views_dashboard_api.reorder_widgets, name='api_reorder_widgets'),
    path('api/dashboard/reset/', views_dashboard_api.reset_dashboard, name='api_reset_dashboard'),

    # API Raccourcis
    path('api/shortcuts/add/', views_shortcuts.add_shortcut, name='api_shortcut_add'),
    path('api/shortcuts/delete/<int:shortcut_id>/', views_shortcuts.delete_shortcut, name='api_shortcut_delete'),
    
    # Gestion multi-chai (UX Points 1-18)
    path('organizations/', views_orgs.my_organizations, name='my_organizations'),
    path('organizations/select/', views_orgs.select_organization, name='select_organization'),
    path('organizations/create/', views_orgs.create_organization, name='create_organization'),
    path('organizations/switch/<int:org_id>/', views_orgs.switch_org, name='switch_org'),
    path('organizations/leave/<int:org_id>/', views_orgs.leave_organization, name='leave_organization'),
    path('organizations/accept/<int:invitation_id>/', views_orgs.accept_invitation_quick, name='accept_invitation_quick'),
]