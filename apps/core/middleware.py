"""
Core middlewares
- ClientsRedirectMiddleware: targeted admin→front redirects (existing)
- RobotsNoIndexMiddleware: adds X-Robots-Tag: noindex by default (except public site)
"""

from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class ClientsRedirectMiddleware:
    """
    Middleware ciblé pour rediriger UNIQUEMENT les URLs clients
    /admin/sales/customer/* → /clients/*
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        path = request.path_info
        
        # SUPPRIMÉ : Redirections automatiques admin → référentiels
        # Ces redirections créaient de la confusion entre workbenches ventes/référentiels
        # Les utilisateurs doivent choisir explicitement leur contexte
        
        # Continuer normalement pour toutes les autres URLs
        response = self.get_response(request)
        return response


from apps.core.tenancy import _current_org


class ActiveOrgContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            _current_org.set(getattr(request, 'current_org', None))
        except Exception:
            _current_org.set(None)
        return None


class PgRlsMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            from django.db import connection
            org = getattr(request, 'current_org', None)
            if org:
                with connection.cursor() as c:
                    # Prefer session fn (app.set_current_org); fallback to SET LOCAL if absent
                    try:
                        c.execute("SELECT app.set_current_org(%s)", [str(org.id)])
                    except Exception:
                        c.execute("SET LOCAL app.current_org = %s", [str(org.id)])
        except Exception:
            pass
        return None


class RobotsNoIndexMiddleware(MiddlewareMixin):
    """Add X-Robots-Tag: noindex for all private namespaces.
    - Skip if resolver namespace is 'site' (public)
    - Skip admin and static/media
    """

    def process_response(self, request, response):
        try:
            path = request.path_info or ''
            if path.startswith('/admin/') or path.startswith('/static/') or path.startswith('/media/'):
                return response
            match = getattr(request, 'resolver_match', None)
            ns = match.namespace if match else ''
            if ns != 'site':
                # Do not overwrite an explicit header
                if not response.has_header('X-Robots-Tag'):
                    response['X-Robots-Tag'] = 'noindex'
        except Exception:
            # Never break response on middleware error
            return response
        return response
