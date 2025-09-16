from rest_framework import serializers
from .models import DRMExport, DRMLigneProduit


class DRMLigneProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DRMLigneProduit
        fields = [
            'id', 'appellation', 'couleur', 'stock_debut_hl',
            'entrees_vendange_hl', 'entrees_autres_hl',
            'sorties_vente_hl', 'sorties_autres_hl', 'pertes_hl',
            'stock_fin_hl', 'references_lots'
        ]


class DRMExportSerializer(serializers.ModelSerializer):
    lignes_produits = DRMLigneProduitSerializer(many=True, read_only=True)
    domaine_nom = serializers.CharField(source='domaine.nom', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DRMExport
        fields = [
            'id', 'domaine', 'domaine_nom', 'periode', 'region', 'status', 'status_display',
            'stock_debut_hl', 'entrees_hl', 'sorties_hl', 'pertes_hl', 'stock_fin_hl',
            'chemin_csv', 'chemin_pdf', 'checksums', 'data', 'lignes_produits',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'domaine_nom', 'status_display', 'stock_debut_hl', 'entrees_hl',
            'sorties_hl', 'pertes_hl', 'stock_fin_hl', 'chemin_csv', 'chemin_pdf',
            'checksums', 'data', 'lignes_produits', 'created_at', 'updated_at'
        ]


class DRMExportCreateSerializer(serializers.Serializer):
    """Serializer pour créer un nouvel export DRM"""
    periode = serializers.CharField(
        max_length=7,
        help_text="Format : YYYY-MM (ex: 2025-09)"
    )
    region = serializers.CharField(
        max_length=50,
        default="Loire",
        help_text="Région viticole pour l'export DRM"
    )
    
    def validate_periode(self, value):
        """Valide le format de la période"""
        try:
            annee, mois = value.split('-')
            annee = int(annee)
            mois = int(mois)
            
            if not (2020 <= annee <= 2030):
                raise serializers.ValidationError("L'année doit être entre 2020 et 2030")
            if not (1 <= mois <= 12):
                raise serializers.ValidationError("Le mois doit être entre 1 et 12")
                
            return value
        except ValueError:
            raise serializers.ValidationError("Format de période invalide. Utilisez YYYY-MM")
