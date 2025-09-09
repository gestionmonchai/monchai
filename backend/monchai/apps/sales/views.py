from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Produit, Client, Commande, LigneCommande, Facture, Paiement
from .serializers import (
    ProduitSerializer, ClientSerializer, CommandeSerializer,
    CommandeCreateSerializer, LigneCommandeSerializer, 
    FactureSerializer, PaiementSerializer
)

from monchai.apps.core.views import BaseDomaineMixin


class ProduitViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les produits"""
    queryset = Produit.objects.all().select_related('bouteille_lot')
    serializer_class = ProduitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bouteille_lot']
    search_fields = ['nom', 'sku']
    model = Produit
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)


class ClientViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    search_fields = ['nom', 'email']
    model = Client
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)


class CommandeViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les commandes"""
    queryset = Commande.objects.all().select_related('client')
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'status', 'date']
    model = Commande
    
    def get_serializer_class(self):
        """Utilise un sérialiseur différent pour la création"""
        if self.action == 'create':
            return CommandeCreateSerializer
        return CommandeSerializer
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Endpoint pour valider une commande"""
        commande = self.get_object()
        
        # Vérifier que la commande est en brouillon
        if commande.status != 'brouillon':
            return Response(
                {"error": "Seules les commandes en brouillon peuvent être validées"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Implémenter ici la logique de validation (stock, etc.)
        commande.status = 'confirmee'
        commande.save()
        
        # Ici on devrait créer un mouvement de type 'vente_sortie_stock'
        
        serializer = self.get_serializer(commande)
        return Response(serializer.data)


class LigneCommandeViewSet(viewsets.ModelViewSet):
    """API endpoint pour les lignes de commande"""
    queryset = LigneCommande.objects.all().select_related('commande', 'produit')
    serializer_class = LigneCommandeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['commande', 'produit']
    
    def get_queryset(self):
        """Filtre les lignes de commande par domaine de l'utilisateur"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return LigneCommande.objects.none()
        
        try:
            domaine = user.profile.domaine
            return queryset.filter(commande__domaine=domaine)
        except:
            return LigneCommande.objects.none()


class FactureViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les factures"""
    queryset = Facture.objects.all().select_related('commande', 'commande__client')
    serializer_class = FactureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['commande', 'status', 'date_emission']
    search_fields = ['numero']
    model = Facture
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)
    
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Endpoint pour générer/récupérer le PDF d'une facture"""
        facture = self.get_object()
        
        # Ici, on devrait implémenter la logique de génération du PDF
        # Pour l'instant, on retourne juste le chemin s'il existe
        if not facture.pdf_path:
            return Response(
                {"error": "PDF non généré pour cette facture"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({"pdf_url": facture.pdf_path})


class PaiementViewSet(viewsets.ModelViewSet):
    """API endpoint pour les paiements"""
    queryset = Paiement.objects.all().select_related('facture')
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['facture', 'mode', 'date']
    
    def get_queryset(self):
        """Filtre les paiements par domaine de l'utilisateur"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return Paiement.objects.none()
        
        try:
            domaine = user.profile.domaine
            return queryset.filter(facture__domaine=domaine)
        except:
            return Paiement.objects.none()
