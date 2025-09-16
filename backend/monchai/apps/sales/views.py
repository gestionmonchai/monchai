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
    def confirmer(self, request, pk=None):
        """Endpoint pour confirmer une commande et créer les mouvements de stock"""
        from .services import VenteService
        
        commande = self.get_object()
        
        try:
            commande_confirmee, mouvements = VenteService.confirmer_commande(commande.id)
            
            serializer = self.get_serializer(commande_confirmee)
            return Response({
                "commande": serializer.data,
                "mouvements_crees": len(mouvements),
                "message": "Commande confirmée avec succès"
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


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
        from .pdf_generator import generer_pdf_facture
        from django.http import FileResponse
        from django.conf import settings
        import os
        
        facture = self.get_object()
        
        try:
            # Générer le PDF s'il n'existe pas
            if not facture.pdf_path:
                pdf_path = generer_pdf_facture(facture.id)
            else:
                pdf_path = facture.pdf_path
            
            # Retourner le fichier PDF
            full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
            if os.path.exists(full_path):
                return FileResponse(
                    open(full_path, 'rb'),
                    as_attachment=True,
                    filename=f"facture_{facture.numero}.pdf"
                )
            else:
                return Response(
                    {"error": "Fichier PDF non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération du PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def creer_depuis_commande(self, request):
        """Endpoint pour créer une facture depuis une commande"""
        from .services import FactureService
        
        commande_id = request.data.get('commande_id')
        if not commande_id:
            return Response(
                {"error": "commande_id requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            facture = FactureService.creer_facture_depuis_commande(
                commande_id=commande_id,
                date_emission=request.data.get('date_emission'),
                date_echeance=request.data.get('date_echeance')
            )
            
            serializer = self.get_serializer(facture)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


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
