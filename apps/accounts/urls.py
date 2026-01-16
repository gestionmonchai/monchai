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
    path('connexion/', views.LoginView.as_view(), name='login'),
    path('inscription/', views.SignupView.as_view(), name='signup'),
    path('deconnexion/', views.logout_view, name='logout'),
    
    # Réinitialisation mot de passe
    path('mot-de-passe/reinitialisation/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('mot-de-passe/reinitialisation/termine/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reinitialisation/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reinitialisation/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # First-run guard (onboarding)
    path('demarrage/', views.first_run_view, name='first_run'),
    path('demarrage/organisation/', views.create_organization_view, name='create_organization'),
    
    # Gestion des rôles (Roadmap 04)
    path('parametres/roles/', views.roles_management_view, name='roles_management'),
    path('parametres/roles/inviter/', views.invite_user_view, name='invite_user'),
    path('parametres/roles/changer/<int:membership_id>/', views.change_role_view, name='change_role'),
    path('parametres/roles/desactiver/<int:membership_id>/', views.deactivate_member_view, name='deactivate_member'),
    
    # Invitations (Roadmap 07)
    path('invitation/accepter/<str:token>/', views_invitations.accept_invitation, name='accept_invitation'),
    path('invitation/envoyer/', views_invitations.send_invitation, name='send_invitation'),
    path('invitation/annuler/<int:invitation_id>/', views_invitations.cancel_invitation, name='cancel_invitation'),
    path('invitation/renvoyer/<int:invitation_id>/', views_invitations.resend_invitation, name='resend_invitation'),
    
    # Paramètres (Roadmap 09)
    # Note: Des alias "pretty" existent à la racine (/parametres/facturation/)
    path('parametres/facturation/', views_settings.billing_settings, name='billing_settings'),
    path('parametres/general/', views_settings.general_settings, name='general_settings'),
    
    # Profil utilisateur (Roadmap 10)
    path('mon-profil/', views_profile.profile_view, name='profile'),
    path('equipe/<int:member_id>/', views_profile.member_detail_view, name='member_detail'),
    
    # Dashboard personnalisable
    path('tableau-de-bord/configuration/', views.dashboard_configure, name='dashboard_configure'),
    
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
    path('organisations/', views_orgs.my_organizations, name='my_organizations'),
    path('organisations/selection/', views_orgs.select_organization, name='select_organization'),
    path('organisations/creer/', views_orgs.create_organization, name='create_organization'),
    path('organisations/changer/<int:org_id>/', views_orgs.switch_org, name='switch_org'),
    path('organisations/quitter/<int:org_id>/', views_orgs.leave_organization, name='leave_organization'),
    path('organisations/accepter/<int:invitation_id>/', views_orgs.accept_invitation_quick, name='accept_invitation_quick'),
]
