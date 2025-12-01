"""
Vues API d'authentification pour Mon Chai.
Implémentation selon roadmap 02_auth_flow.txt
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import User


class LoginAPIView(APIView):
    """
    API de connexion avec session.
    Roadmap : POST {email,password} → 200/401 ; crée session
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'success': True,
                'message': f'Connexion réussie pour {user.full_name}',
                'user': {
                    'email': user.email,
                    'full_name': user.full_name,
                    'has_active_membership': user.has_active_membership()
                }
            })
        else:
            return Response(
                {'error': 'Email ou mot de passe incorrect'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class WhoAmIAPIView(APIView):
    """
    API pour obtenir les informations de l'utilisateur connecté.
    Roadmap : GET /api/auth/whoami/ → renvoie email, nom, org courante, rôle
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Utiliser le current_org du middleware (roadmap 06)
        membership = getattr(request, 'membership', None) or user.get_active_membership()
        current_org = getattr(request, 'current_org', None)
        
        data = {
            'email': user.email,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'has_active_membership': user.has_active_membership(),
            'current_org_id': current_org.id if current_org else None
        }
        
        if membership and current_org:
            data['organization'] = {
                'id': current_org.id,
                'name': current_org.name,
                'siret': current_org.siret,
                'currency': current_org.currency,
                'is_initialized': current_org.is_initialized
            }
            data['role'] = {
                'code': membership.role,
                'display': membership.get_role_display(),
                'level': membership.get_role_level()
            }
        else:
            data['organization'] = None
            data['role'] = None
        
        return Response(data)


class LogoutAPIView(APIView):
    """
    API de déconnexion.
    Roadmap : POST /api/auth/logout/ → détruit session → 204
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_204_NO_CONTENT
        )


class CSRFTokenAPIView(APIView):
    """
    API pour obtenir le token CSRF (utile pour les clients JavaScript).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'csrfToken': get_token(request)
        })
