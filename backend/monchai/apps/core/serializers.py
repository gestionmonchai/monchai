from rest_framework import serializers
from .models import Parcelle, Vendange, Cuve, Lot, Mouvement, BouteilleLot


class ParcelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcelle
        fields = [
            'id', 'domaine', 'nom', 'cepage', 'surface_ha',
            'lat', 'lng', 'annee_plantation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendangeSerializer(serializers.ModelSerializer):
    parcelle_nom = serializers.ReadOnlyField(source='parcelle.nom')
    parcelle_cepage = serializers.ReadOnlyField(source='parcelle.cepage')
    
    class Meta:
        model = Vendange
        fields = [
            'id', 'parcelle', 'parcelle_nom', 'parcelle_cepage', 'date',
            'volume_hl', 'dechets_hl', 'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CuveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuve
        fields = [
            'id', 'domaine', 'nom', 'capacite_hl', 'materiau',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LotSerializer(serializers.ModelSerializer):
    cuve_nom = serializers.ReadOnlyField(source='cuve.nom')
    
    class Meta:
        model = Lot
        fields = [
            'id', 'domaine', 'cuve', 'cuve_nom', 'volume_disponible_hl',
            'ref_interne', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MouvementSerializer(serializers.ModelSerializer):
    source_lot_info = serializers.SerializerMethodField()
    destination_cuve_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Mouvement
        fields = [
            'id', 'domaine', 'type', 'source_lot', 'source_lot_info',
            'destination_cuve', 'destination_cuve_info', 'volume_hl',
            'pertes_hl', 'date', 'status', 'verrouille', 'commentaire',
            'meta_json', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verrouille', 'created_at', 'updated_at']
        
    def get_source_lot_info(self, obj):
        if obj.source_lot:
            return {
                'id': obj.source_lot.id,
                'ref_interne': obj.source_lot.ref_interne,
                'volume_disponible_hl': obj.source_lot.volume_disponible_hl,
                'cuve_nom': obj.source_lot.cuve.nom
            }
        return None
    
    def get_destination_cuve_info(self, obj):
        if obj.destination_cuve:
            return {
                'id': obj.destination_cuve.id,
                'nom': obj.destination_cuve.nom,
                'capacite_hl': obj.destination_cuve.capacite_hl
            }
        return None


class BouteilleLotSerializer(serializers.ModelSerializer):
    source_lot_info = serializers.SerializerMethodField()
    
    class Meta:
        model = BouteilleLot
        fields = [
            'id', 'domaine', 'source_lot', 'source_lot_info', 'nb_bouteilles',
            'contenance_ml', 'date', 'ref_interne', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_source_lot_info(self, obj):
        return {
            'id': obj.source_lot.id,
            'ref_interne': obj.source_lot.ref_interne,
            'cuve_nom': obj.source_lot.cuve.nom
        }
