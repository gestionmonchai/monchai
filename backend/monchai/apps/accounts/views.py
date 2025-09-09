from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout

from .models import User, Domaine, Profile
from .serializers import UserSerializer, DomaineSerializer, ProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint pour les utilisateurs"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Limite les utilisateurs à ceux du domaine de l'utilisateur connecté"""
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        
        # Récupérer le domaine de l'utilisateur
        try:
            profile = user.profile
            domaine = profile.domaine
            
            # Admin domaine peut voir tous les utilisateurs du domaine
            if profile.role == 'admin_domaine':
                return User.objects.filter(profile__domaine=domaine)
            
            # Les autres ne peuvent voir que leur propre profil
            return User.objects.filter(id=user.id)
        except:
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Endpoint de connexion"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email et mot de passe requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Identifiants invalides"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Endpoint de déconnexion"""
        logout(request)
        return Response({"message": "Déconnecté avec succès"})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retourne les informations de l'utilisateur connecté"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Non authentifié"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(request.user)
        data = serializer.data
        
        # Ajouter les informations de profil et de rôle
        try:
            profile = request.user.profile
            data['role'] = profile.role
            data['domaine'] = {
                'id': profile.domaine.id,
                'nom': profile.domaine.nom
            }
        except:
            data['role'] = None
            data['domaine'] = None
        
        return Response(data)


class DomaineViewSet(viewsets.ModelViewSet):
    """API endpoint pour les domaines"""
    queryset = Domaine.objects.all()
    serializer_class = DomaineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Limite les domaines à celui de l'utilisateur connecté"""
        user = self.request.user
        if not user.is_authenticated:
            return Domaine.objects.none()
        
        try:
            domaine = user.profile.domaine
            return Domaine.objects.filter(id=domaine.id)
        except:
            return Domaine.objects.none()


class ProfileViewSet(viewsets.ModelViewSet):
    """API endpoint pour les profils utilisateurs"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Limite les profils à ceux du domaine de l'utilisateur connecté"""
        user = self.request.user
        if not user.is_authenticated:
            return Profile.objects.none()
        
        try:
            profile = user.profile
            domaine = profile.domaine
            
            # Admin domaine peut voir tous les profils du domaine
            if profile.role == 'admin_domaine':
                return Profile.objects.filter(domaine=domaine)
            
            # Les autres ne peuvent voir que leur propre profil
            return Profile.objects.filter(user=user)
        except:
            return Profile.objects.filter(user=user)
