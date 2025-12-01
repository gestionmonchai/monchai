"""
Vues pour la gestion multi-chai - UX Points 1-18
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from .models import Organization, Membership, Invitation, User


@login_required
def switch_org(request, org_id):
    """
    Point 5: Switcher de chai rapide
    Change l'organisation active dans la session
    """
    # Verifier que l'utilisateur est membre de cette org
    membership = Membership.objects.filter(
        user=request.user,
        organization_id=org_id,
        is_active=True
    ).select_related('organization').first()
    
    if not membership:
        messages.error(request, "Vous n'etes pas membre de ce chai.")
        return redirect('auth:my_organizations')
    
    # Mettre a jour la session
    request.session['current_org_id'] = org_id
    
    # Mettre a jour last_org dans le profil (Point 13)
    if hasattr(request.user, 'profile'):
        request.user.profile.last_org = membership.organization
        request.user.profile.save(update_fields=['last_org'])
    
    messages.success(request, f"Vous travaillez maintenant sur {membership.organization.name}")
    
    # Rediriger vers le dashboard du nouveau chai
    return redirect('dashboard')


@login_required
def my_organizations(request):
    """
    Point 14: Page "Mes chais" bien structuree
    Liste tous les chais de l'utilisateur avec roles et actions
    """
    memberships = Membership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization').annotate(
        member_count=Count('organization__memberships', filter=Q(organization__memberships__is_active=True))
    ).order_by('-organization__created_at')
    
    # Recuperer les owners de chaque org
    for m in memberships:
        owners = Membership.objects.filter(
            organization=m.organization,
            role=Membership.Role.OWNER,
            is_active=True
        ).select_related('user')[:3]
        m.owners = owners
    
    # Invitations en attente (Point 3)
    pending_invitations = Invitation.objects.filter(
        email=request.user.email,
        status=Invitation.Status.SENT
    ).select_related('organization', 'invited_by')
    
    context = {
        'memberships': memberships,
        'pending_invitations': pending_invitations,
        'page_title': 'Mes chais',
    }
    
    return render(request, 'accounts/my_organizations.html', context)


@login_required
def select_organization(request):
    """
    Points 2, 3, 13: Ecran de selection de chai apres connexion
    - Skip si un seul chai
    - Priorite aux invitations en attente
    - Pre-selection du dernier chai
    """
    # Verifier s'il y a des invitations en attente (Point 3)
    pending_invitations = Invitation.objects.filter(
        email=request.user.email,
        status=Invitation.Status.SENT
    ).select_related('organization', 'invited_by')
    
    # Recuperer les memberships actifs
    memberships = Membership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization').order_by('-organization__created_at')
    
    # Point 2: Si un seul chai et pas d'invitation, on skip
    if memberships.count() == 1 and not pending_invitations.exists():
        m = memberships.first()
        request.session['current_org_id'] = m.organization.id
        if hasattr(request.user, 'profile'):
            request.user.profile.last_org = m.organization
            request.user.profile.save(update_fields=['last_org'])
        return redirect('dashboard')
    
    # Point 15: Aucun chai et pas d'invitation
    if memberships.count() == 0 and not pending_invitations.exists():
        return redirect('auth:create_organization')
    
    # Dernier chai utilise (Point 13)
    last_org_id = None
    if hasattr(request.user, 'profile') and request.user.profile.last_org_id:
        last_org_id = request.user.profile.last_org_id
    
    context = {
        'memberships': memberships,
        'pending_invitations': pending_invitations,
        'last_org_id': last_org_id,
        'page_title': 'Choisir un chai',
    }
    
    return render(request, 'accounts/select_organization.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_organization(request):
    """
    Point 4: Creation de chai avec garde-fous
    Empecher la creation de chais "par erreur"
    """
    # Verifier s'il y a des invitations en attente
    pending_invitations = Invitation.objects.filter(
        email=request.user.email,
        status=Invitation.Status.SENT
    ).count()
    
    if request.method == 'POST':
        # Verifier la case de confirmation
        confirmed = request.POST.get('confirm_create') == 'on'
        if not confirmed:
            messages.error(request, "Veuillez confirmer que vous comprenez les implications.")
            return redirect('auth:create_organization')
        
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Le nom du chai est obligatoire.")
            return redirect('auth:create_organization')
        
        # Creer l'organisation
        org = Organization.objects.create(
            name=name,
            is_initialized=False
        )
        
        # Creer le membership owner
        Membership.objects.create(
            user=request.user,
            organization=org,
            role=Membership.Role.OWNER,
            is_active=True
        )
        
        # Mettre a jour la session et le profil
        request.session['current_org_id'] = org.id
        if hasattr(request.user, 'profile'):
            request.user.profile.last_org = org
            request.user.profile.save(update_fields=['last_org'])
        
        messages.success(request, f"Le chai '{name}' a ete cree avec succes !")
        return redirect('dashboard')
    
    context = {
        'pending_invitations_count': pending_invitations,
        'page_title': 'Creer un nouveau chai',
    }
    
    return render(request, 'accounts/create_organization_new.html', context)


@login_required
@require_http_methods(["POST"])
def leave_organization(request, org_id):
    """
    Point 14: Quitter un chai
    """
    membership = get_object_or_404(
        Membership,
        user=request.user,
        organization_id=org_id,
        is_active=True
    )
    
    # Ne peut pas quitter si owner unique
    if membership.role == Membership.Role.OWNER:
        other_owners = Membership.objects.filter(
            organization_id=org_id,
            role=Membership.Role.OWNER,
            is_active=True
        ).exclude(user=request.user).count()
        
        if other_owners == 0:
            messages.error(request, "Vous etes le seul proprietaire. Transferez la propriete avant de quitter.")
            return redirect('auth:my_organizations')
    
    # Desactiver le membership
    membership.is_active = False
    membership.save(update_fields=['is_active'])
    
    messages.success(request, f"Vous avez quitte {membership.organization.name}")
    
    # Si c'etait le chai actif, en choisir un autre
    if request.session.get('current_org_id') == org_id:
        other = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        if other:
            request.session['current_org_id'] = other.organization_id
        else:
            request.session.pop('current_org_id', None)
    
    return redirect('auth:my_organizations')


@login_required
@require_http_methods(["POST"])
def accept_invitation_quick(request, invitation_id):
    """
    Point 3: Accepter une invitation rapidement depuis l'ecran de selection
    """
    invitation = get_object_or_404(
        Invitation,
        id=invitation_id,
        email=request.user.email,
        status=Invitation.Status.SENT
    )
    
    # Verifier expiration
    if invitation.is_expired():
        invitation.mark_as_expired()
        messages.error(request, "Cette invitation a expire.")
        return redirect('auth:select_organization')
    
    # Verifier si deja membre
    if Membership.objects.filter(
        user=request.user,
        organization=invitation.organization,
        is_active=True
    ).exists():
        invitation.mark_as_accepted(request.user)
        messages.info(request, f"Vous etes deja membre de {invitation.organization.name}")
        return redirect('auth:select_organization')
    
    # Creer le membership
    Membership.objects.create(
        user=request.user,
        organization=invitation.organization,
        role=invitation.role,
        is_active=True
    )
    
    # Marquer l'invitation comme acceptee
    invitation.mark_as_accepted(request.user)
    
    # Mettre a jour la session
    request.session['current_org_id'] = invitation.organization.id
    
    messages.success(
        request,
        f"Bienvenue dans {invitation.organization.name} ! "
        f"Vous avez rejoint en tant que {invitation.get_role_display()}."
    )
    
    return redirect('dashboard')

