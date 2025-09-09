from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Parcelle, Vendange, Cuve, Lot, Mouvement, BouteilleLot
from .serializers import (
    ParcelleSerializer, VendangeSerializer, CuveSerializer,
    LotSerializer, MouvementSerializer, BouteilleLotSerializer
)


class BaseDomaineMixin:
    """Mixin de base pour les vues qui doivent être filtrées par domaine"""
    
    def get_queryset(self):
        """Filtre les objets par domaine de l'utilisateur connecté"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return self.model.objects.none()
        
        try:
            domaine = user.profile.domaine
            return queryset.filter(domaine=domaine)
        except:
            return self.model.objects.none()


class ParcelleViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les parcelles"""
    queryset = Parcelle.objects.all()
    serializer_class = ParcelleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cepage']
    search_fields = ['nom', 'cepage']
    model = Parcelle
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)


class VendangeViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les vendanges"""
    queryset = Vendange.objects.all().select_related('parcelle')
    serializer_class = VendangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['parcelle', 'date']
    model = Vendange


class CuveViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les cuves"""
    queryset = Cuve.objects.all()
    serializer_class = CuveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['materiau']
    search_fields = ['nom']
    model = Cuve
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)


class LotViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les lots"""
    queryset = Lot.objects.all().select_related('cuve')
    serializer_class = LotSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cuve']
    search_fields = ['ref_interne']
    model = Lot
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)


class MouvementViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les mouvements"""
    queryset = Mouvement.objects.all().select_related('source_lot', 'destination_cuve')
    serializer_class = MouvementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'status', 'source_lot', 'destination_cuve', 'date']
    model = Mouvement
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Endpoint pour valider un mouvement"""
        mouvement = self.get_object()
        
        # Vérifier que le mouvement est en brouillon
        if mouvement.status != 'draft':
            return Response(
                {"error": "Seuls les mouvements en brouillon peuvent être validés"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Implémenter ici la logique de validation (contrôle volume, etc.)
        mouvement.status = 'valide'
        mouvement.save()
        
        serializer = self.get_serializer(mouvement)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Surcharge pour empêcher la suppression de mouvements validés ou verrouillés"""
        mouvement = self.get_object()
        if mouvement.status != 'draft':
            return Response(
                {"error": "Seuls les mouvements en brouillon peuvent être supprimés"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class BouteilleLotViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les lots de bouteilles"""
    queryset = BouteilleLot.objects.all().select_related('source_lot')
    serializer_class = BouteilleLotSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source_lot', 'contenance_ml', 'date']
    search_fields = ['ref_interne']
    model = BouteilleLot
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)
