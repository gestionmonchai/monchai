"""
Vues pour le profil utilisateur - Roadmap 10
Page /me/profile/ avec gestion des préférences personnelles
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse

from .models import UserProfile, Membership, Invitation
from .utils import invitation_manager


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """
    Page Mon Compte complète avec:
    - Profil utilisateur
    - Organisation
    - Équipe (membres + invitations)
    - Préférences
    """
    # Obtenir ou créer le profil
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'locale': 'fr', 'timezone': 'Europe/Paris'}
    )
    
    # Organisation courante
    organization = getattr(request, 'current_org', None)
    membership = getattr(request, 'membership', None)
    
    # Permissions
    can_manage_team = membership and membership.role in ['owner', 'admin'] if membership else False
    
    # Membres de l'organisation
    members = []
    pending_invitations = []
    if organization:
        members = Membership.objects.filter(
            organization=organization, 
            is_active=True
        ).select_related('user', 'user__profile').order_by('-role', 'user__first_name')
        
        pending_invitations = Invitation.objects.filter(
            organization=organization,
            status=Invitation.Status.SENT
        ).order_by('-created_at')
    
    # Traitement des formulaires POST
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Mise à jour profil utilisateur
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.save(update_fields=['first_name', 'last_name'])
            
            profile.display_name = request.POST.get('display_name', '').strip()
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
            
            messages.success(request, 'Profil mis à jour.')
            return HttpResponseRedirect(reverse('auth:profile'))
        
        elif form_type == 'organization' and organization:
            # Mise à jour organisation
            org_name = request.POST.get('org_name', '').strip()
            if org_name:
                organization.name = org_name
                organization.siret = request.POST.get('org_siret', '').strip() or None
                organization.tva_number = request.POST.get('org_tva', '').strip()
                organization.currency = request.POST.get('org_currency', 'EUR')
                organization.address = request.POST.get('org_address', '').strip()
                organization.postal_code = request.POST.get('org_postal_code', '').strip()
                organization.city = request.POST.get('org_city', '').strip()
                organization.country = request.POST.get('org_country', '').strip() or 'France'
                organization.save()
                messages.success(request, 'Organisation mise à jour.')
            else:
                messages.error(request, 'Le nom est obligatoire.')
            return HttpResponseRedirect(reverse('auth:profile') + '#organisation')
        
        elif form_type == 'preferences':
            # Mise à jour préférences
            profile.locale = request.POST.get('locale', 'fr')
            tz = request.POST.get('timezone', '').strip()
            if tz:
                profile.timezone = tz
            # Si vide, on garde la valeur actuelle ou le default
            profile.save()
            messages.success(request, 'Préférences mises à jour.')
            return HttpResponseRedirect(reverse('auth:profile') + '#preferences')
        
        elif form_type == 'password':
            # Changement mot de passe
            current = request.POST.get('current_password', '')
            new_pwd = request.POST.get('new_password', '')
            confirm = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current):
                messages.error(request, 'Mot de passe actuel incorrect.')
            elif new_pwd != confirm:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            elif len(new_pwd) < 8:
                messages.error(request, 'Le mot de passe doit faire au moins 8 caractères.')
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Mot de passe changé avec succès.')
            return HttpResponseRedirect(reverse('auth:profile'))
        
        elif form_type == 'invite' and can_manage_team:
            # Invitation via invitation_manager (génère token + email)
            email = request.POST.get('invite_email', '').strip().lower()
            role = request.POST.get('invite_role', 'member')
            
            if email:
                # Vérifier si déjà membre
                if Membership.objects.filter(organization=organization, user__email=email).exists():
                    messages.warning(request, f'{email} est déjà membre de l\'organisation.')
                else:
                    # Utiliser invitation_manager pour créer + envoyer email
                    invitation = invitation_manager.create_invitation(
                        email=email,
                        organization=organization,
                        role=role,
                        invited_by=request.user,
                        request=request
                    )
                    if invitation:
                        # Afficher le code en console pour le dev
                        print(f"\n{'='*60}")
                        print(f"INVITATION ENVOYEE")
                        print(f"   Email: {email}")
                        print(f"   Organisation: {organization.name}")
                        print(f"   Role: {role}")
                        print(f"   CODE: {invitation.invite_code}")
                        print(f"{'='*60}\n")
                        
                        messages.success(
                            request, 
                            f'Invitation creee ! Partagez le code {invitation.invite_code} avec {email}.'
                        )
                    else:
                        messages.warning(request, f'Une invitation est déjà en attente pour {email}.')
            return HttpResponseRedirect(reverse('auth:profile'))
        
        elif form_type == 'cancel_invite' and can_manage_team:
            # Annuler une invitation
            invite_id = request.POST.get('invite_id')
            if invite_id:
                try:
                    inv = Invitation.objects.get(
                        id=invite_id,
                        organization=organization,
                        status=Invitation.Status.SENT
                    )
                    inv.status = Invitation.Status.EXPIRED
                    inv.save(update_fields=['status'])
                    messages.success(request, f'Invitation pour {inv.email} annulée.')
                except Invitation.DoesNotExist:
                    messages.error(request, 'Invitation introuvable.')
            return HttpResponseRedirect(reverse('auth:profile'))
        
        elif form_type == 'join_by_code':
            # Rejoindre une organisation avec un code
            code = request.POST.get('invite_code', '').strip().upper()
            if code:
                result = invitation_manager.accept_by_code(code, request.user)
                if result['success']:
                    # Mettre à jour la session pour l'organisation
                    request.session['current_org_id'] = result['organization'].id
                    messages.success(
                        request, 
                        f"Bienvenue dans {result['organization'].name} ! "
                        f"Vous avez rejoint en tant que {result['role_display']}."
                    )
                else:
                    messages.error(request, result['error'])
            else:
                messages.error(request, 'Veuillez entrer un code d\'invitation.')
            return HttpResponseRedirect(reverse('auth:profile'))
    
    context = {
        'profile': profile,
        'user': request.user,
        'organization': organization,
        'membership': membership,
        'members': members,
        'pending_invitations': pending_invitations,
        'can_manage_team': can_manage_team,
        'page_title': 'Mon compte'
    }
    
    return render(request, 'accounts/profile_v3.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def member_detail_view(request, member_id):
    """
    Page de gestion d'un collaborateur - droits et permissions
    Accessible uniquement aux admins/owners
    """
    organization = getattr(request, 'current_org', None)
    membership = getattr(request, 'membership', None)
    
    # Vérifier les permissions
    if not membership or membership.role not in ['owner', 'admin']:
        messages.error(request, "Vous n'avez pas les droits pour gérer les collaborateurs.")
        return HttpResponseRedirect(reverse('auth:profile'))
    
    # Récupérer le membre
    member = get_object_or_404(
        Membership.objects.select_related('user', 'user__profile'),
        id=member_id,
        organization=organization
    )
    
    # Ne pas permettre de modifier son propre compte ici
    if member.user == request.user:
        return HttpResponseRedirect(reverse('auth:profile'))
    
    # Ne pas permettre de modifier un owner
    if member.role == 'owner':
        messages.warning(request, "Impossible de modifier les droits d'un proprietaire.")
        return HttpResponseRedirect(reverse('auth:profile'))
    
    # Charger les permissions effectives
    perms = member.get_permissions()
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'change_role':
            new_role = request.POST.get('new_role')
            # Les vrais roles du modele: admin, editor, read_only (owner ne peut pas etre attribue)
            if new_role in ['admin', 'editor', 'read_only']:
                member.role = new_role
                # Reset permissions to defaults for new role
                member.permissions = {}
                member.save(update_fields=['role', 'permissions'])
                messages.success(request, f"Role de {member.user.get_full_name() or member.user.email} modifie.")
            return HttpResponseRedirect(reverse('auth:member_detail', args=[member_id]))
        
        elif form_type == 'permissions':
            # Sauvegarder les permissions granulaires
            modules = ['parcelles', 'cuvees', 'vendanges', 'lots', 'stocks', 'ventes', 'factures', 'stats']
            new_perms = {}
            
            for module in modules:
                new_perms[module] = {
                    'view': request.POST.get(f'{module}_view') == 'on',
                    'edit': request.POST.get(f'{module}_edit') == 'on',
                }
            
            # Stats a 'export' au lieu de 'edit'
            new_perms['stats'] = {
                'view': request.POST.get('stats_view') == 'on',
                'export': request.POST.get('stats_export') == 'on',
            }
            
            member.permissions = new_perms
            member.save(update_fields=['permissions'])
            messages.success(request, "Permissions mises a jour.")
            return HttpResponseRedirect(reverse('auth:member_detail', args=[member_id]))
        
        elif form_type == 'remove_member':
            user_name = member.user.get_full_name() or member.user.email
            member.is_active = False
            member.save(update_fields=['is_active'])
            messages.success(request, f"{user_name} a ete retire de l'organisation.")
            return HttpResponseRedirect(reverse('auth:profile'))
    
    context = {
        'member': member,
        'perms': perms,
        'organization': organization,
        'page_title': f"Gestion - {member.user.get_full_name() or member.user.email}"
    }
    
    return render(request, 'accounts/member_detail.html', context)
