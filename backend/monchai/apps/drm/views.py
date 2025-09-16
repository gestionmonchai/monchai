from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
import os

from .models import DRMExport
from .serializers import DRMExportSerializer, DRMExportCreateSerializer
from .services import DRMExportService

from monchai.apps.core.views import BaseDomaineMixin


class DRMExportViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les exports DRM"""
    queryset = DRMExport.objects.all()
    serializer_class = DRMExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['periode', 'status', 'region']
    model = DRMExport
    
    def get_serializer_class(self):
        """Utilise un serializer différent pour la création"""
        if self.action == 'create':
            return DRMExportCreateSerializer
        return DRMExportSerializer
    
    def create(self, request, *args, **kwargs):
        """Crée un nouvel export DRM avec génération automatique des fichiers"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Récupérer le domaine de l'utilisateur
            domaine = self.get_domaine()
            
            # Générer l'export complet
            drm_export = DRMExportService.generer_export_complet(
                domaine=domaine,
                periode=serializer.validated_data['periode'],
                region=serializer.validated_data.get('region', 'Loire')
            )
            
            # Sérialiser la réponse
            response_serializer = DRMExportSerializer(drm_export)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération de l'export: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generer(self, request):
        """Endpoint pour générer un export DRM"""
        serializer = DRMExportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Récupérer le domaine de l'utilisateur
            domaine = self.get_domaine()
            
            # Générer l'export complet
            drm_export = DRMExportService.generer_export_complet(
                domaine=domaine,
                periode=serializer.validated_data['periode'],
                region=serializer.validated_data.get('region', 'Loire')
            )
            
            # Sérialiser la réponse
            response_serializer = DRMExportSerializer(drm_export)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la génération de l'export: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_csv(self, request, pk=None):
        """Endpoint pour télécharger le fichier CSV"""
        drm_export = self.get_object()
        
        if not drm_export.chemin_csv:
            return Response(
                {"error": "Fichier CSV non disponible pour cet export"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Vérifier que le fichier existe
            if not default_storage.exists(drm_export.chemin_csv):
                return Response(
                    {"error": "Fichier CSV introuvable"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Lire le contenu du fichier
            with default_storage.open(drm_export.chemin_csv, 'r') as f:
                content = f.read()
            
            # Créer la réponse HTTP avec le bon type de contenu
            response = HttpResponse(content, content_type='text/csv; charset=utf-8')
            filename = f"DRM_{drm_export.periode}_{drm_export.domaine.nom.replace(' ', '_')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du téléchargement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Endpoint pour télécharger le fichier PDF"""
        drm_export = self.get_object()
        
        if not drm_export.chemin_pdf:
            return Response(
                {"error": "Fichier PDF non disponible pour cet export"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Vérifier que le fichier existe
            if not default_storage.exists(drm_export.chemin_pdf):
                return Response(
                    {"error": "Fichier PDF introuvable"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Lire le contenu du fichier
            with default_storage.open(drm_export.chemin_pdf, 'rb') as f:
                content = f.read()
            
            # Créer la réponse HTTP avec le bon type de contenu
            response = HttpResponse(content, content_type='application/pdf')
            filename = f"DRM_{drm_export.periode}_{drm_export.domaine.nom.replace(' ', '_')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du téléchargement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def regenerer(self, request, pk=None):
        """Régénère les fichiers d'export pour un DRM existant"""
        drm_export = self.get_object()
        
        if drm_export.status in ['transmis', 'valide']:
            return Response(
                {"error": "Impossible de régénérer un export déjà transmis ou validé"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Régénérer les fichiers
            DRMExportService.generer_csv(drm_export)
            DRMExportService.generer_pdf(drm_export)
            
            # Recharger l'objet depuis la base
            drm_export.refresh_from_db()
            
            # Sérialiser la réponse
            serializer = DRMExportSerializer(drm_export)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la régénération: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
