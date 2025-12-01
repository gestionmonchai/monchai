"""
Vues pour la gestion des invitations - Roadmap 07
Deux cas d'usage: invité non connecté → signup + session; invité connecté → membership direct
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import Http404
from django.views.decorators.http import require_http_methods

from .models import Invitation, Organization
from .utils import invitation_manager
from .decorators import require_membership


def accept_invitation(request, token):
    """
    Accepter une invitation selon roadmap 07.
    GET: Afficher page de confirmation
    POST: Traiter l'acceptation
    """
    if request.method == 'GET':
        # Vérifier que le token est valide
        payload = invitation_manager.verify_invitation_token(token)
        if not payload:
            messages.error(request, "Cette invitation n'est plus valide ou a expiré.")
            return redirect('auth:login')
        
        # Récupérer l'invitation
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            messages.error(request, "Invitation introuvable.")
            return redirect('auth:login')
        
        if not invitation.can_be_accepted():
            messages.error(request, "Cette invitation a expiré ou a déjà été acceptée.")
            return redirect('auth:login')
        
        # Afficher la page de confirmation
        context = {
            'invitation': invitation,
            'organization': invitation.organization,
            'role_display': invitation.get_role_display(),
            'token': token
        }
        return render(request, 'accounts/accept_invitation.html', context)
    
    elif request.method == 'POST':
        # Traiter l'acceptation
        result = invitation_manager.accept_invitation(
            token=token,
            user=request.user if request.user.is_authenticated else None
        )
        
        if not result['success']:
            messages.error(request, result['error'])
            return redirect('auth:login')
        
        if result['action'] == 'membership_created':
            # Cas utilisateur connecté → membership créé
            membership = result['membership']
            messages.success(
                request, 
                f"Vous avez rejoint l'exploitation {membership.organization.name} "
                f"avec le rôle {membership.get_role_display()}."
            )
            return redirect('auth:roles_management')
        
        elif result['action'] == 'store_in_session':
            # Cas utilisateur non connecté → stocker en session et rediriger signup
            request.session['invitation_payload'] = result['payload']
            messages.info(
                request,
                f"Pour rejoindre {result['payload']['organization_name']}, "
                "créez votre compte ou connectez-vous."
            )
            return redirect('auth:signup')
        
        else:
            messages.error(request, "Erreur lors du traitement de l'invitation.")
            return redirect('auth:login')


@login_required
@require_membership(role_min='admin')
@require_http_methods(["GET", "POST"])
def send_invitation(request):
    """
    Envoyer une invitation (réservé aux admins).
    GET: Afficher le formulaire
    POST: Traiter l'envoi
    """
    from .forms import InvitationForm
    
    if request.method == 'GET':
        form = InvitationForm()
        context = {
            'form': form,
            'organization': request.current_org
        }
        return render(request, 'accounts/send_invitation.html', context)
    
    elif request.method == 'POST':
        form = InvitationForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            
            # Créer l'invitation
            invitation = invitation_manager.create_invitation(
                email=email,
                organization=request.current_org,
                role=role,
                invited_by=request.user,
                request=request
            )
            
            if invitation:
                messages.success(
                    request,
                    f"Invitation envoyée à {email} pour le rôle {invitation.get_role_display()}."
                )
                return redirect('auth:roles_management')
            else:
                messages.error(
                    request,
                    f"Une invitation active existe déjà pour {email}."
                )
        
        context = {
            'form': form,
            'organization': request.current_org
        }
        return render(request, 'accounts/send_invitation.html', context)


@login_required
@require_membership(role_min='admin')
def cancel_invitation(request, invitation_id):
    """
    Annuler une invitation (réservé aux admins).
    """
    invitation = get_object_or_404(
        Invitation,
        id=invitation_id,
        organization=request.current_org
    )
    
    if invitation.status == Invitation.Status.SENT:
        invitation.mark_as_cancelled()
        messages.success(request, f"Invitation pour {invitation.email} annulée.")
    else:
        messages.error(request, "Cette invitation ne peut pas être annulée.")
    
    return redirect('auth:roles_management')


@login_required
@require_membership(role_min='admin')
def resend_invitation(request, invitation_id):
    """
    Renvoyer une invitation (réservé aux admins).
    """
    invitation = get_object_or_404(
        Invitation,
        id=invitation_id,
        organization=request.current_org
    )
    
    if invitation.status == Invitation.Status.SENT and not invitation.is_expired():
        # Renvoyer l'email
        success = invitation_manager.send_invitation_email(
            email=invitation.email,
            organization_name=invitation.organization.name,
            role=invitation.role,
            token=invitation.token,
            inviter_name=request.user.full_name,
            request=request
        )
        
        if success:
            messages.success(request, f"Invitation renvoyée à {invitation.email}.")
        else:
            messages.error(request, "Erreur lors de l'envoi de l'email.")
    else:
        messages.error(request, "Cette invitation ne peut pas être renvoyée.")
    
    return redirect('auth:roles_management')
