"""
Décorateurs de protection pour Mon Chai.
Implémentation selon roadmap 04_roles_acces.txt
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib import messages

from .models import Membership


def require_membership(role_min=None):
    """
    Décorateur pour protéger les vues métier avec hiérarchie des rôles.
    Roadmap 04 : Vérifie user authentifié + Membership actif + rôle minimum
    
    Usage:
    @require_membership()  # Juste un membership actif
    @require_membership('editor')  # Editor minimum (editor, admin, owner)
    @require_membership('admin')   # Admin minimum (admin, owner)
    @require_membership('owner')   # Owner uniquement
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier que l'utilisateur est connecté
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            
            # Vérifier que l'utilisateur a un Membership actif
            membership = request.user.get_active_membership()
            if not membership:
                # Rediriger vers first-run guard pour créer/rejoindre une organisation
                return redirect('/auth/first-run/')
            
            # Vérifier le rôle minimum si spécifié
            if role_min:
                if not _has_required_role(membership.role, role_min):
                    try:
                        messages.error(
                            request, 
                            f'Accès refusé. Cette action nécessite le rôle {role_min} minimum.'
                        )
                    except:
                        # Ignorer les erreurs de messages (utile pour les tests)
                        pass
                    return HttpResponseForbidden(
                        f'Accès refusé. Rôle requis: {role_min}, votre rôle: {membership.get_role_display()}'
                    )
            
            # Ajouter le membership à la request pour éviter les requêtes répétées
            request.membership = membership
            request.current_org = membership.organization
            
            # L'utilisateur a les permissions requises, continuer vers la vue
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    # Permettre d'utiliser @require_membership sans parenthèses
    if callable(role_min):
        view_func = role_min
        role_min = None
        return decorator(view_func)
    
    return decorator


def _has_required_role(user_role, required_role):
    """
    Vérifie si le rôle utilisateur satisfait le rôle requis selon la hiérarchie.
    Hiérarchie: owner > admin > editor > read_only
    """
    # Définir la hiérarchie des rôles (plus le nombre est élevé, plus le rôle est puissant)
    role_hierarchy = {
        Membership.Role.READ_ONLY: 1,
        Membership.Role.EDITOR: 2,
        Membership.Role.ADMIN: 3,
        Membership.Role.OWNER: 4,
    }
    
    # Convertir les strings en enum si nécessaire
    if isinstance(required_role, str):
        role_mapping = {
            'read_only': Membership.Role.READ_ONLY,
            'editor': Membership.Role.EDITOR,
            'admin': Membership.Role.ADMIN,
            'owner': Membership.Role.OWNER,
        }
        required_role = role_mapping.get(required_role.lower(), required_role)
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


def require_active_organization(view_func):
    """
    Décorateur plus strict qui vérifie aussi que l'organisation est initialisée.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier que l'utilisateur est connecté
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        
        # Vérifier que l'utilisateur a un Membership actif
        membership = request.user.get_active_membership()
        if not membership:
            return redirect('/auth/first-run/')
        
        # Vérifier que l'organisation est initialisée
        if not membership.organization.is_initialized:
            return redirect('/auth/first-run/org/')
        
        # Tout est OK, continuer vers la vue
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


# Alias pour compatibilité
require_organization = require_membership


def require_permission(module, action='view'):
    """
    Decorateur pour verifier les permissions granulaires.
    
    Usage:
    @require_permission('vendanges', 'view')  # Peut voir les vendanges
    @require_permission('vendanges', 'edit')  # Peut modifier les vendanges
    @require_permission('lots', 'edit')       # Peut modifier les lots
    @require_permission('stocks', 'view')     # Peut voir les stocks
    
    Modules disponibles:
    - parcelles, cuvees, vendanges, lots, stocks, ventes, factures, stats, team
    
    Actions disponibles:
    - view, edit, export (pour stats), manage (pour team)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verifier que l'utilisateur est connecte
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            
            # Recuperer le membership (depuis middleware ou fresh)
            membership = getattr(request, 'membership', None)
            if not membership:
                membership = request.user.get_active_membership()
            
            if not membership:
                return redirect('/auth/first-run/')
            
            # Verifier la permission granulaire
            if not membership.has_permission(module, action):
                messages.error(
                    request,
                    f"Acces refuse. Vous n'avez pas la permission de {action} sur {module}."
                )
                # Rediriger vers le dashboard au lieu de 403
                return redirect('auth:dashboard')
            
            # Ajouter les infos a la request
            request.membership = membership
            request.current_org = membership.organization
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def require_perm(module, action='view', role_min=None):
    """
    Decorateur combine: verifie le role ET les permissions granulaires.
    
    Usage:
    @require_perm('parcelles', 'view')           # Voir les parcelles
    @require_perm('parcelles', 'edit')           # Modifier les parcelles
    @require_perm('parcelles', 'edit', 'admin')  # Modifier + role admin minimum
    
    C'est le decorateur RECOMMANDE pour toutes les vues metier.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verifier authentification
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            
            # Recuperer le membership
            membership = getattr(request, 'membership', None)
            if not membership:
                membership = request.user.get_active_membership()
            
            if not membership:
                return redirect('/auth/first-run/')
            
            # Verifier le role minimum si specifie
            if role_min:
                if not _has_required_role(membership.role, role_min):
                    messages.error(request, f"Acces refuse. Role {role_min} minimum requis.")
                    return redirect('auth:dashboard')
            
            # Verifier la permission granulaire
            if not membership.has_permission(module, action):
                action_label = {'view': 'consulter', 'edit': 'modifier', 'export': 'exporter'}.get(action, action)
                module_label = {
                    'parcelles': 'les parcelles',
                    'cuvees': 'les cuvees', 
                    'vendanges': 'les vendanges',
                    'lots': 'les lots techniques',
                    'stocks': 'les stocks',
                    'ventes': 'les ventes',
                    'factures': 'les factures',
                    'stats': 'les statistiques',
                    'team': 'l\'equipe'
                }.get(module, module)
                messages.error(request, f"Acces refuse. Vous n'avez pas le droit de {action_label} {module_label}.")
                return redirect('auth:dashboard')
            
            # Tout OK - ajouter les infos a la request
            request.membership = membership
            request.current_org = membership.organization
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def check_permission(request, module, action='view'):
    """
    Fonction utilitaire pour verifier une permission dans une vue.
    Retourne True/False.
    
    Usage dans une vue:
    if not check_permission(request, 'vendanges', 'edit'):
        messages.error(request, "Permission refusee")
        return redirect('...')
    """
    membership = getattr(request, 'membership', None)
    if not membership:
        return False
    return membership.has_permission(module, action)
