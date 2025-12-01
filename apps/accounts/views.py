"""
Vues d'authentification web pour Mon Chai.
Implémentation selon roadmap 02_auth_flow.txt
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

from .forms import LoginForm, SignupForm, PasswordResetRequestForm, OrganizationCreationForm, InviteUserForm, ChangeRoleForm
from .models import User, Organization, Membership
from .decorators import require_membership
from .utils import invitation_manager
from apps.onboarding.models import OnboardingState


class LoginView(FormView):
    """
    Vue de connexion avec email comme identifiant.
    Roadmap : POST valide → login() ; sinon renvoyer form avec erreurs
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = settings.LOGIN_REDIRECT_URL
    
    def dispatch(self, request, *args, **kwargs):
        # Rediriger si déjà connecté
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Authentifier et connecter l'utilisateur"""
        email = form.cleaned_data['username']  # Le champ s'appelle username mais contient l'email
        password = form.cleaned_data['password']
        
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Bienvenue {user.full_name} !')
            
            # Gérer les redirections après connexion
            next_url = self.request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(self.success_url)
        else:
            form.add_error(None, 'Email ou mot de passe incorrect.')
            return self.form_invalid(form)


class SignupView(FormView):
    """
    Vue d'inscription avec création de compte.
    Roadmap : crée l'utilisateur, set_password, login(); gère pending_invite
    """
    template_name = 'accounts/signup.html'
    form_class = SignupForm
    success_url = settings.LOGIN_REDIRECT_URL
    
    def dispatch(self, request, *args, **kwargs):
        # Rediriger si déjà connecté
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Créer le compte et connecter automatiquement"""
        user = form.save()
        
        # Gérer une éventuelle invitation en session (roadmap 07)
        invitation_payload = self.request.session.get('invitation_payload')
        if invitation_payload:
            # Vérifier que l'email correspond
            if user.email == invitation_payload['email']:
                # Créer le membership selon l'invitation
                try:
                    from .models import Invitation
                    organization = Organization.objects.get(id=invitation_payload['organization_id'])
                    
                    # Créer le membership
                    membership = Membership.objects.create(
                        user=user,
                        organization=organization,
                        role=invitation_payload['role'],
                        is_active=True
                    )
                    
                    # Marquer l'invitation comme acceptée
                    try:
                        invitation = Invitation.objects.get(id=invitation_payload['invitation_id'])
                        invitation.mark_as_accepted(user)
                    except Invitation.DoesNotExist:
                        pass  # L'invitation pourrait avoir été supprimée
                    
                    messages.success(
                        self.request,
                        f'Vous avez rejoint {organization.name} avec le rôle {invitation_payload["role_display"]} !'
                    )
                    # Nettoyer la session
                    del self.request.session['invitation_payload']
                except Organization.DoesNotExist:
                    messages.error(self.request, 'Organisation d\'invitation introuvable.')
            else:
                messages.warning(
                    self.request,
                    f'L\'invitation était destinée à {invitation_payload["email"]}. '
                    f'Vous vous êtes inscrit avec {user.email}.'
                )
        
        # Connecter automatiquement après inscription
        login(self.request, user)
        messages.success(
            self.request, 
            f'Compte créé avec succès ! Bienvenue {user.full_name} !'
        )
        
        return redirect(self.success_url)


def logout_view(request):
    """
    Vue de déconnexion.
    Roadmap : appelle logout(); redirige vers LOGIN_URL
    """
    if request.user.is_authenticated:
        messages.info(request, 'Vous avez été déconnecté avec succès.')
        logout(request)
    return redirect(settings.LOGIN_URL)


class CustomPasswordResetView(PasswordResetView):
    """
    Vue de demande de réinitialisation de mot de passe.
    Roadmap : utilise PasswordResetForm.save() avec email template texte
    """
    template_name = 'accounts/password_reset.html'
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('auth:password_reset_done')
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    
    def form_valid(self, form):
        """Envoyer l'email de reset si l'utilisateur existe"""
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email)
            # Générer le token et l'UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construire l'URL de reset
            reset_url = self.request.build_absolute_uri(
                f'/auth/reset/{uid}/{token}/'
            )
            
            # Envoyer l'email (console en dev)
            subject = 'Réinitialisation de votre mot de passe Mon Chai'
            message = f"""
Bonjour {user.full_name or user.email},

Vous avez demandé la réinitialisation de votre mot de passe sur Mon Chai.

Cliquez sur le lien suivant pour définir un nouveau mot de passe :
{reset_url}

Si vous n'avez pas fait cette demande, ignorez cet email.

Cordialement,
L'équipe Mon Chai
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@monchai.fr',
                recipient_list=[email],
                fail_silently=False,
            )
            
        except User.DoesNotExist:
            # Ne pas révéler que l'email n'existe pas (sécurité)
            pass
        
        messages.success(
            self.request,
            'Si un compte existe avec cette adresse, vous recevrez un email de réinitialisation.'
        )
        return redirect(self.success_url)


class PasswordResetDoneView(TemplateView):
    """Vue de confirmation d'envoi d'email de reset"""
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Vue de confirmation de réinitialisation avec nouveau mot de passe.
    Roadmap : vérifie token/uid; SetPasswordForm; redirige login
    """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('auth:password_reset_complete')
    
    def form_valid(self, form):
        """Sauvegarder le nouveau mot de passe"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Votre mot de passe a été modifié avec succès !'
        )
        return response


class PasswordResetCompleteView(TemplateView):
    """Vue de confirmation finale après reset du mot de passe"""
    template_name = 'accounts/password_reset_complete.html'


@login_required
def first_run_view(request):
    """
    Vue du first-run guard.
    Roadmap 03 : Si user possède au moins un Membership actif → redirect /dashboard/
    Sinon → redirect /auth/first-run/org/ (form de création exploitation)
    """
    user = request.user
    
    # Vérifier si l'utilisateur a un Membership actif
    if user.has_active_membership():
        # L'utilisateur a déjà une organisation, rediriger vers dashboard
        return redirect('/dashboard/')
    else:
        # Pas d'organisation, rediriger vers création d'exploitation
        return redirect('/auth/first-run/org/')


@login_required
def create_organization_view(request):
    """
    Vue de création d'exploitation pour l'onboarding rapide.
    Roadmap 03 : GET/POST /auth/first-run/org/
    Champs: name (obligatoire), siret (optionnel), tax_id (optionnel), currency
    """
    # Si l'utilisateur a déjà un Membership, rediriger vers dashboard
    if request.user.has_active_membership():
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST)
        if form.is_valid():
            # Créer l'organisation et le membership owner
            organization = form.save(user=request.user)
            
            messages.success(
                request,
                f'Exploitation "{organization.name}" créée avec succès ! '
                f'Vous êtes maintenant propriétaire de cette exploitation.'
            )
            
            # Rediriger vers dashboard
            return redirect('/dashboard/')
    else:
        form = OrganizationCreationForm()
    
    return render(request, 'accounts/create_organization.html', {
        'form': form
    })


# Dashboard viticole principal
@login_required
def dashboard_placeholder(request):
    """
    Dashboard viticole personnalisable avec métriques clés
    """
    from .models import UserDashboardConfig, DashboardWidget
    from .dashboard_widgets import WidgetRenderer
    
    organization = request.current_org
    
    # Récupérer ou créer la configuration utilisateur
    config, created = UserDashboardConfig.objects.get_or_create(
        user=request.user,
        organization=organization,
        defaults={
            'active_widgets': [
                'alertes_critiques',      # NOUVEAU: Alertes en premier !
                'volume_recolte',
                'volume_cuve',
                'chiffre_affaires',
                'clients_actifs',
                'cuvees_actives',
                'dernieres_actions',      # NOUVEAU: Activité récente
                'top_clients',            # NOUVEAU: Top clients
            ],
            'layout': 'grid',
            'columns': 3,
        }
    )
    
    # Charger les widgets actifs avec leurs données
    widgets_data = []
    for widget_code in config.active_widgets:
        try:
            widget = DashboardWidget.objects.get(code=widget_code, is_active=True)
            data = WidgetRenderer.get_widget_data(widget_code, organization)
            if data:
                widgets_data.append({
                    'widget': widget,
                    'data': data,
                    'code': widget_code,
                })
        except DashboardWidget.DoesNotExist:
            pass
    
    # Pour compatibilité avec l'ancien template (fallback)
    from django.db.models import Sum, Count
    from decimal import Decimal
    from apps.production.models import VendangeReception
    from apps.stock.models import StockVracBalance
    from apps.billing.models import Invoice
    from apps.sales.models import Customer, Order
    from apps.viticulture.models import Cuvee
    
    organization = request.current_org
    
    # 1. VOLUME RÉCOLTÉ (vendanges de la campagne en cours)
    from django.utils import timezone
    current_year = timezone.now().year
    current_campaign = f"{current_year}-{current_year + 1}"
    
    vendanges_stats = VendangeReception.objects.filter(
        organization=organization,
        campagne=current_campaign
    ).aggregate(
        total_kg=Sum('poids_kg'),
        total_volume_l=Sum('volume_mesure_l'),
        count=Count('id')
    )
    
    volume_recolte_kg = vendanges_stats['total_kg'] or Decimal('0')
    volume_recolte_l = vendanges_stats['total_volume_l'] or Decimal('0')
    nb_vendanges = vendanges_stats['count'] or 0
    
    # 2. VOLUMES EN CUVE (stocks actuels)
    stock_stats = StockVracBalance.objects.filter(
        organization=organization,
        qty_l__gt=0
    ).aggregate(
        total_volume=Sum('qty_l'),
        nb_lots=Count('lot', distinct=True)
    )
    
    volume_en_cuve_l = stock_stats['total_volume'] or Decimal('0')
    nb_lots_stock = stock_stats['nb_lots'] or 0
    
    # 3. CHIFFRE D'AFFAIRES (factures émises de l'année)
    factures_stats = Invoice.objects.filter(
        organization=organization,
        date_issue__year=current_year,
        status__in=['issued', 'paid']
    ).aggregate(
        ca_ht=Sum('total_ht'),
        ca_ttc=Sum('total_ttc'),
        count=Count('id')
    )
    
    ca_ht = factures_stats['ca_ht'] or Decimal('0')
    ca_ttc = factures_stats['ca_ttc'] or Decimal('0')
    nb_factures = factures_stats['count'] or 0
    
    # 4. STATISTIQUES COMPLÉMENTAIRES
    nb_clients = Customer.objects.filter(organization=organization, is_active=True).count()
    nb_cuvees = Cuvee.objects.filter(organization=organization, is_active=True).count()
    
    # Compteur parcelles pour "getting started"
    from apps.referentiels.models import Parcelle
    nb_parcelles = Parcelle.objects.filter(organization=organization).count()
    
    # Indicateur "compte vierge" pour afficher les CTA
    is_empty_account = (nb_parcelles == 0 and nb_cuvees == 0 and nb_vendanges == 0)
    
    # Commandes en cours
    nb_commandes_en_cours = Order.objects.filter(
        organization=organization,
        status__in=['draft', 'confirmed']
    ).count()
    
    # Factures impayées (calcul en Python car amount_due est une property)
    factures_impayees = Invoice.objects.filter(
        organization=organization,
        status='issued'
    )
    montant_impaye = sum(facture.amount_due for facture in factures_impayees)
    
    # Onboarding CTA visibility: show unless explicitly dismissed
    try:
        ob_state, _ = OnboardingState.objects.get_or_create(organization=organization)
        show_onboarding_button = not ob_state.dismissed
    except Exception:
        show_onboarding_button = True

    # Tous les widgets disponibles (pour le modal d'ajout)
    all_widgets = DashboardWidget.objects.filter(is_active=True).order_by('widget_type', 'name')
    
    context = {
        # Dashboard personnalisable
        'widgets_data': widgets_data,
        'config': config,
        'all_widgets': all_widgets,
        
        # Métriques principales (compatibilité)
        'volume_recolte_kg': volume_recolte_kg,
        'volume_recolte_l': volume_recolte_l,
        'nb_vendanges': nb_vendanges,
        'volume_en_cuve_l': volume_en_cuve_l,
        'nb_lots_stock': nb_lots_stock,
        'ca_ht': ca_ht,
        'ca_ttc': ca_ttc,
        'nb_factures': nb_factures,
        
        # Statistiques complémentaires
        'nb_clients': nb_clients,
        'nb_cuvees': nb_cuvees,
        'nb_commandes_en_cours': nb_commandes_en_cours,
        'montant_impaye': montant_impaye,
        'nb_parcelles': nb_parcelles,
        
        # Infos contexte
        'current_campaign': current_campaign,
        'current_year': current_year,
        # Onboarding CTA
        'show_onboarding_button': show_onboarding_button,
        'is_empty_account': is_empty_account,
    }
    
    # Utiliser le nouveau template avec édition inline
    return render(request, 'accounts/dashboard_inline.html', context)


# ============================================================================
# VUES DE GESTION DES RÔLES (Roadmap 04)
# ============================================================================

@require_membership('admin')
def roles_management_view(request):
    """
    Vue de gestion des rôles et membres.
    Roadmap 07 : Page /settings/roles avec table des membres et invitations
    """
    from .models import Invitation
    
    organization = request.current_org
    current_membership = request.membership
    
    # Récupérer tous les membres actifs
    members = organization.get_active_members().order_by('user__first_name', 'user__last_name')
    
    # Récupérer les invitations en attente (roadmap 07)
    pending_invitations = Invitation.objects.filter(
        organization=organization,
        status=Invitation.Status.SENT
    ).order_by('-created_at')
    
    # Statistiques
    stats = {
        'total_members': members.count(),
        'owners': members.filter(role=Membership.Role.OWNER).count(),
        'admins': members.filter(role=Membership.Role.ADMIN).count(),
        'editors': members.filter(role=Membership.Role.EDITOR).count(),
        'readers': members.filter(role=Membership.Role.READ_ONLY).count(),
        'pending_invitations': pending_invitations.count(),
    }
    
    context = {
        'organization': organization,
        'members': members,
        'pending_invitations': pending_invitations,
        'current_membership': current_membership,
        'stats': stats,
        'can_invite': current_membership.can_invite_users(),
    }
    
    return render(request, 'accounts/roles_management.html', context)


@require_membership('admin')
def invite_user_view(request):
    """
    Vue d'invitation d'un nouvel utilisateur.
    Roadmap 04 : Form d'invitation (email + rôle) visible seulement owner/admin
    """
    organization = request.current_org
    current_membership = request.membership
    
    if request.method == 'POST':
        form = InviteUserForm(request.POST, current_user_role=current_membership.role)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            
            # Vérifier que l'utilisateur n'est pas déjà membre
            existing_membership = Membership.objects.filter(
                user__email=email,
                organization=organization,
                is_active=True
            ).first()
            
            if existing_membership:
                messages.error(
                    request,
                    f'{email} est déjà membre de cette organisation avec le rôle {existing_membership.get_role_display()}.'
                )
            else:
                # Créer le token d'invitation
                token = invitation_manager.create_invitation_token(
                    email=email,
                    organization_id=organization.id,
                    role=role
                )
                
                # Envoyer l'email d'invitation
                success = invitation_manager.send_invitation_email(
                    email=email,
                    organization_name=organization.name,
                    role=role,
                    token=token,
                    inviter_name=request.user.full_name,
                    request=request
                )
                
                if success:
                    messages.success(
                        request,
                        f'Invitation envoyée à {email} avec le rôle {dict(Membership.Role.choices)[role]}.'
                    )
                    return redirect('auth:roles_management')
                else:
                    messages.error(
                        request,
                        'Erreur lors de l\'envoi de l\'invitation. Veuillez réessayer.'
                    )
    else:
        form = InviteUserForm(current_user_role=current_membership.role)
    
    context = {
        'form': form,
        'organization': organization,
        'current_membership': current_membership,
    }
    
    return render(request, 'accounts/invite_user.html', context)


@require_membership('admin')
def change_role_view(request, membership_id):
    """
    Vue de changement de rôle d'un membre.
    Roadmap 04 : Change role avec protection anti-suppression du dernier owner
    """
    organization = request.current_org
    current_membership = request.membership
    
    # Récupérer le membership à modifier
    try:
        target_membership = Membership.objects.get(
            id=membership_id,
            organization=organization,
            is_active=True
        )
    except Membership.DoesNotExist:
        messages.error(request, 'Membre introuvable.')
        return redirect('auth:roles_management')
    
    # Vérifier les permissions
    if (current_membership.role == Membership.Role.ADMIN and 
        target_membership.role == Membership.Role.OWNER):
        messages.error(request, 'Vous ne pouvez pas modifier le rôle d\'un propriétaire.')
        return redirect('auth:roles_management')
    
    if request.method == 'POST':
        form = ChangeRoleForm(
            request.POST,
            membership=target_membership,
            current_user_role=current_membership.role,
            organization=organization
        )
        if form.is_valid():
            new_role = form.cleaned_data['role']
            old_role = target_membership.role
            
            # Effectuer le changement
            target_membership.role = new_role
            target_membership.save()
            
            messages.success(
                request,
                f'Rôle de {target_membership.user.full_name} changé de '
                f'{dict(Membership.Role.choices)[old_role]} vers '
                f'{dict(Membership.Role.choices)[new_role]}.'
            )
            return redirect('auth:roles_management')
    else:
        form = ChangeRoleForm(
            membership=target_membership,
            current_user_role=current_membership.role,
            organization=organization
        )
    
    context = {
        'form': form,
        'target_membership': target_membership,
        'organization': organization,
        'current_membership': current_membership,
    }
    
    return render(request, 'accounts/change_role.html', context)


@require_membership('admin')
def deactivate_member_view(request, membership_id):
    """
    Vue de désactivation d'un membre.
    Roadmap 04 : Désactivation membership via is_active=False
    """
    organization = request.current_org
    current_membership = request.membership
    
    # Récupérer le membership à désactiver
    try:
        target_membership = Membership.objects.get(
            id=membership_id,
            organization=organization,
            is_active=True
        )
    except Membership.DoesNotExist:
        messages.error(request, 'Membre introuvable.')
        return redirect('auth:roles_management')
    
    # Vérifications de sécurité
    if target_membership.user == request.user:
        messages.error(request, 'Vous ne pouvez pas vous désactiver vous-même.')
        return redirect('auth:roles_management')
    
    if (target_membership.role == Membership.Role.OWNER and 
        not organization.has_multiple_owners()):
        messages.error(request, 'Impossible de désactiver le dernier propriétaire.')
        return redirect('auth:roles_management')
    
    if request.method == 'POST':
        # Désactiver le membership
        target_membership.is_active = False
        target_membership.save()
        
        messages.success(
            request,
            f'{target_membership.user.full_name} a été retiré de l\'organisation.'
        )
        return redirect('auth:roles_management')
    
    context = {
        'target_membership': target_membership,
        'organization': organization,
        'current_membership': current_membership,
    }
    
    return render(request, 'accounts/confirm_deactivate.html', context)


def accept_invitation_view(request, token):
    """
    Vue d'acceptation d'invitation.
    Roadmap 04 : Cas A/B selon si l'utilisateur est connecté ou non
    """
    # Vérifier le token
    invitation_info = invitation_manager.get_invitation_info(token)
    if not invitation_info:
        messages.error(request, 'Invitation invalide ou expirée.')
        return redirect('auth:login')
    
    email = invitation_info['email']
    organization = invitation_info['organization']
    role = invitation_info['role']
    
    if request.user.is_authenticated:
        # Cas B : Utilisateur déjà connecté
        if request.user.email != email:
            messages.error(
                request,
                f'Cette invitation est destinée à {email}. '
                f'Vous êtes connecté en tant que {request.user.email}.'
            )
            return redirect('auth:login')
        
        # Vérifier s'il n'est pas déjà membre
        existing_membership = Membership.objects.filter(
            user=request.user,
            organization=organization,
            is_active=True
        ).first()
        
        if existing_membership:
            messages.info(
                request,
                f'Vous êtes déjà membre de {organization.name} avec le rôle {existing_membership.get_role_display()}.'
            )
            return redirect('/dashboard/')
        
        # Créer le membership
        Membership.objects.create(
            user=request.user,
            organization=organization,
            role=role,
            is_active=True
        )
        
        messages.success(
            request,
            f'Vous avez rejoint {organization.name} avec le rôle {dict(Membership.Role.choices)[role]} !'
        )
        return redirect('/dashboard/')
    
    else:
        # Cas A : Utilisateur non connecté → stocker en session et rediriger vers signup
        request.session['pending_invite'] = {
            'email': email,
            'organization_id': organization.id,
            'organization_name': organization.name,
            'role': role,
            'role_display': dict(Membership.Role.choices)[role],
            'token': token
        }
        
        messages.info(
            request,
            f'Vous êtes invité à rejoindre {organization.name}. '
            f'Créez votre compte ou connectez-vous pour accepter l\'invitation.'
        )
        return redirect('auth:signup')


# ============================================================================
# VUES DE CONFIGURATION DASHBOARD PERSONNALISABLE
# ============================================================================

@login_required
def dashboard_configure(request):
    """
    Page de configuration du dashboard personnalisable
    """
    from .models import DashboardWidget, UserDashboardConfig
    from .dashboard_widgets import WidgetRenderer
    
    organization = request.current_org
    
    # Récupérer ou créer la configuration
    config, created = UserDashboardConfig.objects.get_or_create(
        user=request.user,
        organization=organization,
        defaults={
            'active_widgets': [
                'alertes_critiques',      # Alertes en premier
                'volume_recolte',
                'volume_cuve',
                'chiffre_affaires',
                'clients_actifs',
                'cuvees_actives',
                'dernieres_actions',      # Activité récente
                'top_clients',            # Top clients
            ],
            'layout': 'grid',
            'columns': 3,
        }
    )
    
    # Tous les widgets disponibles
    all_widgets = DashboardWidget.objects.filter(is_active=True).order_by('widget_type', 'name')
    
    # Widgets actifs avec leurs données
    active_widgets_data = []
    for widget_code in config.active_widgets:
        try:
            widget = DashboardWidget.objects.get(code=widget_code, is_active=True)
            data = WidgetRenderer.get_widget_data(widget_code, organization)
            active_widgets_data.append({
                'widget': widget,
                'data': data,
            })
        except DashboardWidget.DoesNotExist:
            pass
    
    context = {
        'config': config,
        'all_widgets': all_widgets,
        'active_widgets_data': active_widgets_data,
    }
    
    return render(request, 'accounts/dashboard_configure.html', context)


def landing_page(request):
    """
    Landing page HTML/Tailwind accessible avant authentification.
    Accessible à l'URL /monchai/
    """
    return render(request, 'landing/landing_page_simple.html')
