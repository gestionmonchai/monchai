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
        return redirect('/tableau-de-bord/')
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
        return redirect('/tableau-de-bord/')
    
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
    Dashboard viticole intelligent "Smart Dashboard"
    Inspiré du wireframe avec météo, alertes IA et KPIs temps réel.
    """
    from .models import UserDashboardConfig, DashboardWidget
    from .dashboard_widgets import WidgetRenderer
    from apps.ai.smart_suggestions import WeatherService, DRMTimer, NudgeType
    from apps.referentiels.models import Parcelle
    from apps.production.models_containers import Contenant
    from apps.sales.models import Order
    from apps.billing.models import Invoice
    from django.db.models import Sum, Count
    from decimal import Decimal
    from django.utils import timezone
    import datetime
    
    organization = request.current_org
    
    # 1. CONFIGURATION DASHBOARD (Legacy support)
    config, created = UserDashboardConfig.objects.get_or_create(
        user=request.user,
        organization=organization,
        defaults={
            'active_widgets': ['alertes_critiques', 'volume_recolte', 'chiffre_affaires'],
            'layout': 'grid',
            'columns': 3,
        }
    )
    
    # 2. DONNÉES SMART DASHBOARD
    
    # --- A. MÉTÉO VIGNOBLE ---
    weather_context = {
        'city': 'Vignoble',
        'current': {'temp': '--', 'description': 'Non configuré'},
        'forecasts': [],
        'suggestion': None,
        'alerts': []
    }
    
    # Chercher la première parcelle avec coordonnées
    first_parcelle = Parcelle.objects.filter(
        organization=organization, 
        latitude__isnull=False, 
        longitude__isnull=False
    ).first()
    
    if first_parcelle:
        weather_context['city'] = first_parcelle.commune or first_parcelle.nom
        try:
            forecasts = WeatherService.get_forecast(
                float(first_parcelle.latitude), 
                float(first_parcelle.longitude)
            )
            
            if forecasts:
                current = forecasts[0]
                weather_context['current'] = {
                    'temp': current.temp_max,
                    'description': current.description,
                }
                
                # Prévisions J+1, J+2
                for f in forecasts[1:3]:
                    weather_context['forecasts'].append({
                        'day_name': f.date.strftime('%A')[:3].upper() + '.', # Lun.
                        'temp_max': f.temp_max,
                        'icon': f.icon  # Utilisation directe des icônes Bootstrap (bi-*)
                    })
                
                # Suggestions météo
                alerts = WeatherService.get_parcelle_alerts(first_parcelle)
                if alerts:
                    weather_context['alerts'] = True
                    # Prendre la suggestion la plus prioritaire
                    top_alert = max(alerts, key=lambda x: x.priority)
                    weather_context['suggestion'] = top_alert.message
                else:
                    weather_context['suggestion'] = "Conditions favorables pour travaux vigne"
                    
        except Exception as e:
            print(f"Erreur météo dashboard: {e}")

    # --- B. ACTIVITÉ CHAI (Capacité & Alertes) ---
    # Capacité totale
    all_cuves = Contenant.objects.filter(organization=organization, is_active=True)
    capacite_totale_l = sum(c.capacite_utile_effective_l or 0 for c in all_cuves)
    
    # Volume en stock (déjà calculé dans l'ancien code, on le reprend)
    from apps.stock.models import StockVracBalance
    volume_en_cuve_l = StockVracBalance.objects.filter(
        organization=organization,
        qty_l__gt=0
    ).aggregate(total=Sum('qty_l'))['total'] or Decimal('0')
    
    occupation_pct = 0
    if capacite_totale_l > 0:
        occupation_pct = int((volume_en_cuve_l / capacite_totale_l) * 100)
    
    # Alertes Chai & Qualité (Analyses via AnalyseDetective)
    from apps.ai.smart_suggestions import AnalyseDetective
    from apps.production.models import LotTechnique
    
    alerts_chai = []
    
    # Récupérer les lots actifs (non archivés/épuisés)
    # On filtre sur les cuvées de l'organisation
    active_lots = LotTechnique.objects.filter(
        cuvee__organization=organization
    ).exclude(statut__in=['epuise', 'archive', 'vendu', 'mise'])
    
    # Analyser les lots (limité aux 20 premiers pour performance dashboard)
    for lot in active_lots[:20]:
        try:
            # AnalyseDetective retourne une liste de Nudge
            nudges = AnalyseDetective.analyze_lot(lot)
            if nudges:
                # On ajoute le code du lot au titre pour le contexte
                for nudge in nudges:
                    nudge.title = f"{lot.code} : {nudge.title}"
                alerts_chai.extend(nudges)
        except Exception as e:
            # Ne pas bloquer le dashboard si une analyse échoue
            print(f"Erreur analyse lot {lot.code}: {e}")
            
    # Trier par priorité décroissante
    alerts_chai.sort(key=lambda x: x.priority, reverse=True)

    # --- C. COMMERCIAL (Mois en cours) ---
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    orders_month = Order.objects.filter(
        organization=organization,
        created_at__gte=month_start
    ).count()
    
    revenue_month = Invoice.objects.filter(
        organization=organization,
        date_issue__gte=month_start,
        status__in=['issued', 'paid']
    ).aggregate(total=Sum('total_ht'))['total'] or Decimal('0')
    
    orders_to_ship = Order.objects.filter(
        organization=organization,
        status='confirmed' # Ou status logistique spécifique
    ).count()

    # --- D. DATA GLOBALE ---
    
    # Indicateur compte vierge
    from apps.referentiels.models import Parcelle as RefParcelle
    from apps.viticulture.models import Cuvee
    from apps.production.models import VendangeReception
    
    nb_parcelles = RefParcelle.objects.filter(organization=organization).count()
    nb_cuvees = Cuvee.objects.filter(organization=organization).count()
    nb_vendanges = VendangeReception.objects.filter(organization=organization).count()
    is_empty_account = (nb_parcelles == 0 and nb_cuvees == 0 and nb_vendanges == 0)

    # Campagne
    current_year = now.year
    current_campaign = f"{current_year}-{current_year + 1}"

    # DRM Status
    drm_status = DRMTimer.get_drm_status(organization)

    context = {
        # Météo
        'weather_city': weather_context['city'],
        'weather_current': weather_context['current'],
        'weather_forecasts': weather_context['forecasts'],
        'weather_suggestion': weather_context['suggestion'],
        'weather_alerts': weather_context['alerts'],
        
        # Chai
        'occupation_pct': occupation_pct,
        'volume_en_cuve_hl': volume_en_cuve_l / 100,
        'capacite_totale_hl': capacite_totale_l / 100,
        'chai_status': "Saturé" if occupation_pct > 90 else "Actif" if occupation_pct > 50 else "Calme",
        'alerts_chai': alerts_chai,
        
        # Commercial
        'orders_count_month': orders_month,
        'revenue_month': revenue_month,
        'orders_to_ship': orders_to_ship,
        
        # Général / Agenda
        'current_campaign': current_campaign,
        'is_empty_account': is_empty_account,
        'nb_parcelles': nb_parcelles,
        'nb_cuvees': nb_cuvees,
        'nb_vendanges': nb_vendanges,
        'drm_status': drm_status,
        
        # Config (pour compatibilité)
        'config': config,
    }
    
    return render(request, 'accounts/dashboard_smart.html', context)


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
            return redirect('/tableau-de-bord/')
        
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
