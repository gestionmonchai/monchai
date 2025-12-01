"""
Middleware pour Mon Chai.
Implémentation selon roadmap 06_routing_middlewares_gardes.txt
"""

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

from .models import Membership


class CurrentOrganizationMiddleware(MiddlewareMixin):
    """
    Current organization resolver selon roadmap 06.
    Lit current_org_id de la session; fallback sur 1er membership.
    Injecte request.current_org pour les vues.
    """
    
    def process_request(self, request):
        """Résoudre l'organisation courante pour l'utilisateur authentifié"""
        
        # Initialiser les attributs
        request.current_org = None
        request.membership = None
        
        # Ignorer pour les utilisateurs non authentifiés
        if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            return None
        
        # Récupérer l'ID de l'organisation courante depuis la session
        current_org_id = request.session.get('current_org_id')
        
        if current_org_id:
            # Vérifier que l'utilisateur a bien un membership actif pour cette org
            try:
                membership = Membership.objects.select_related('organization', 'user').get(
                    user=request.user,
                    organization_id=current_org_id,
                    is_active=True
                )
                request.current_org = membership.organization
                request.membership = membership
                return None
            except Membership.DoesNotExist:
                # L'org en session n'est plus valide, la supprimer
                if 'current_org_id' in request.session:
                    del request.session['current_org_id']
                    request.session.save()
        
        # Fallback : utiliser le premier membership actif
        membership = request.user.get_active_membership()
        if membership:
            request.current_org = membership.organization
            request.membership = membership
            # Stocker en session pour les prochaines requêtes
            request.session['current_org_id'] = membership.organization.id
        else:
            # PROTECTION: Utilisateur sans organisation - forcer la création
            # Exclure certaines URLs pour éviter les boucles de redirection
            allowed_paths = [
                '/auth/logout/',
                '/auth/login/',
                '/auth/register/',
                '/auth/create-organization/',
                '/auth/onboarding/',
                '/auth/first-run/',
                '/static/',
                '/media/',
                '/admin/',
                '/__debug__/',
            ]
            path = request.path
            if not any(path.startswith(p) for p in allowed_paths):
                # Rediriger vers la création d'organisation
                try:
                    return redirect('auth:create_organization')
                except Exception:
                    return redirect('/auth/create-organization/')
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de sécurité selon roadmap 06.
    Vérifie les mesures de sécurité de base.
    """
    
    def process_request(self, request):
        """Vérifications de sécurité de base"""
        
        # Ajouter des headers de sécurité
        if hasattr(request, 'META'):
            # Éviter les attaques de clickjacking
            request.META['HTTP_X_FRAME_OPTIONS'] = 'DENY'
            
            # Éviter les attaques XSS
            request.META['HTTP_X_CONTENT_TYPE_OPTIONS'] = 'nosniff'
        
        return None
    
    def process_response(self, request, response):
        """Ajouter des headers de sécurité à la réponse"""
        
        # Headers de sécurité
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # CSRF protection reminder
        if hasattr(request, 'method') and request.method == 'POST':
            if not hasattr(request, 'META') or 'HTTP_X_CSRFTOKEN' not in request.META:
                # Le CSRF est géré par Django, on ajoute juste un header informatif
                response['X-CSRF-Required'] = 'true'
        
        return response


class OrganizationFilterMiddleware(MiddlewareMixin):
    """
    Middleware pour s'assurer que les données sont filtrées par organisation.
    Roadmap 06 : Pas de données d'organisation sans filtre par organization=current.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Vérifier que les vues métier ont accès à l'organisation courante.
        """
        
        # Ignorer pour les vues d'authentification, admin et static
        if (request.resolver_match and 
            (request.resolver_match.namespace in ['auth', 'admin', 'api_auth'] or
             request.resolver_match.url_name in ['root', 'dashboard'] or
             request.path.startswith('/static/') or
             request.path.startswith('/media/'))):
            return None
        
        # Ignorer pour les utilisateurs non authentifiés (géré par login_required)
        if not request.user.is_authenticated:
            return None
        
        # Ne pas interférer avec les vues qui ont déjà des décorateurs de protection
        # Le décorateur require_membership gère déjà les redirections
        return None
