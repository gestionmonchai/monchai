from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Parcelle, Vendange, Cuve, Lot, Mouvement, BouteilleLot
from .serializers import (
    ParcelleSerializer, VendangeSerializer, CuveSerializer,
    LotSerializer, MouvementSerializer, BouteilleLotSerializer
)
from .services import MouvementService, MiseEnBouteilleService


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
        
        try:
            mouvement_valide = MouvementService.valider_mouvement(mouvement.id)
            serializer = self.get_serializer(mouvement_valide)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def inter_cuves(self, request):
        """Endpoint pour créer un mouvement inter-cuves"""
        try:
            data = request.data
            mouvement = MouvementService.create_inter_cuves(
                source_lot_id=data.get('source_lot_id'),
                destination_cuve_id=data.get('destination_cuve_id'),
                volume_hl=Decimal(str(data.get('volume_hl'))),
                date=data.get('date'),
                commentaire=data.get('commentaire', ''),
                domaine=request.user.profile.domaine
            )
            serializer = self.get_serializer(mouvement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du mouvement: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def perte(self, request):
        """Endpoint pour créer un mouvement de perte"""
        try:
            data = request.data
            mouvement = MouvementService.create_perte(
                source_lot_id=data.get('source_lot_id'),
                volume_hl=Decimal(str(data.get('volume_hl'))),
                date=data.get('date'),
                commentaire=data.get('commentaire', ''),
                domaine=request.user.profile.domaine
            )
            serializer = self.get_serializer(mouvement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du mouvement: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def vendange_vers_cuve(self, request):
        """Endpoint pour créer un mouvement vendange vers cuve"""
        try:
            data = request.data
            mouvement = MouvementService.create_vendange_vers_cuve(
                vendange_id=data.get('vendange_id'),
                destination_cuve_id=data.get('destination_cuve_id'),
                date=data.get('date')
            )
            serializer = self.get_serializer(mouvement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du mouvement: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
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
    
    @action(detail=False, methods=['post'])
    def mise_en_bouteille(self, request):
        """Endpoint pour exécuter une mise en bouteille complète"""
        try:
            data = request.data
            mouvement, bouteille_lot = MiseEnBouteilleService.executer_mise_en_bouteille(
                source_lot_id=data.get('source_lot_id'),
                nb_bouteilles=int(data.get('nb_bouteilles')),
                contenance_ml=int(data.get('contenance_ml')),
                taux_perte_hl=Decimal(str(data.get('taux_perte_hl', 0))),
                date=data.get('date'),
                domaine=request.user.profile.domaine
            )
            
            # Retourner les informations du lot de bouteilles créé
            serializer = self.get_serializer(bouteille_lot)
            return Response({
                'bouteille_lot': serializer.data,
                'mouvement_id': mouvement.id
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la mise en bouteille: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
