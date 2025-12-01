from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse

from apps.onboarding.models import OnboardingState


class OnboardingRedirectMiddleware(MiddlewareMixin):
    """
    Redirige les nouveaux utilisateurs vers /onboarding/ si toutes les étapes
    sont en pending et que l'onboarding n'est pas masqué. Ne s'applique qu'une fois
    (flag de session) pour éviter une boucle tant qu'il n'y a aucune donnée.
    """

    EXCLUDE_PREFIXES = (
        '/onboarding/', '/auth/', '/admin/', '/api/', '/static/', '/media/', '/monchai/'
    )

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        path = request.path or ''
        if any(path.startswith(p) for p in self.EXCLUDE_PREFIXES):
            return None
        # Nécessite CurrentOrganizationMiddleware avant
        org = getattr(request, 'current_org', None)
        if org is None:
            return None
        # Flag de session pour n'appliquer qu'une fois
        if request.session.get('onboarding_redirect_done'):
            return None
        try:
            st, _ = OnboardingState.objects.get_or_create(organization=org)
            st.ensure_all_keys()
            if st.dismissed or st.is_completed():
                return None
            all_pending = all(v == 'pending' for v in (st.state or {}).values())
            if all_pending:
                request.session['onboarding_redirect_done'] = True
                request.session.modified = True
                return redirect(reverse('onboarding:flow'))
        except Exception:
            return None
        return None
