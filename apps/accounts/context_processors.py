"""
Context processors pour multi-chai UX.
Fournit les donnees de chai a tous les templates.
"""
from .models import Membership, Invitation


def multi_chai_context(request):
    """
    Context processor pour l'UX multi-chai (Points 1, 5, 6, 18).
    Ajoute aux templates:
    - current_org: Organisation courante
    - membership: Membership courant avec role
    - user_orgs: Liste des memberships de l'utilisateur
    - pending_invitations_count: Nombre d'invitations en attente
    """
    context = {
        'current_org': None,
        'membership': None,
        'user_orgs': [],
        'pending_invitations_count': 0,
    }
    
    if not request.user.is_authenticated:
        return context
    
    # Organisation courante (depuis middleware ou session)
    current_org = getattr(request, 'current_org', None)
    membership = getattr(request, 'membership', None)
    
    context['current_org'] = current_org
    context['membership'] = membership
    
    # Liste des chais de l'utilisateur pour le switcher
    context['user_orgs'] = Membership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization').order_by('organization__name')
    
    # Invitations en attente
    context['pending_invitations_count'] = Invitation.objects.filter(
        email=request.user.email,
        status=Invitation.Status.SENT
    ).count()
    
    return context
