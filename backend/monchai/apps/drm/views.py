from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import DRMExport
from .serializers import DRMExportSerializer

from monchai.apps.core.views import BaseDomaineMixin


class DRMExportViewSet(BaseDomaineMixin, viewsets.ModelViewSet):
    """API endpoint pour les exports DRM"""
    queryset = DRMExport.objects.all()
    serializer_class = DRMExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['periode']
    model = DRMExport
    
    def perform_create(self, serializer):
        """Associe automatiquement le domaine de l'utilisateur"""
        serializer.save(domaine=self.request.user.profile.domaine)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Endpoint pour générer un export DRM"""
        # Récupérer le paramètre mois (format YYYY-MM)
        mois = request.query_params.get('mois')
        if not mois:
            return Response(
                {"error": "Paramètre 'mois' requis (format: YYYY-MM)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ici, on devrait implémenter la logique de génération de l'export DRM
        # Pour l'instant, on retourne juste un message
        return Response({
            "message": f"Export DRM pour la période {mois} en cours de génération",
            "status": "pending"
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Endpoint pour télécharger un export DRM (CSV ou PDF)"""
        drm_export = self.get_object()
        format_type = request.query_params.get('format', 'csv')
        
        if format_type == 'csv' and drm_export.chemin_csv:
            return Response({"download_url": drm_export.chemin_csv})
        elif format_type == 'pdf' and drm_export.chemin_pdf:
            return Response({"download_url": drm_export.chemin_pdf})
        else:
            return Response(
                {"error": f"Format {format_type} non disponible pour cet export"},
                status=status.HTTP_404_NOT_FOUND
            )
