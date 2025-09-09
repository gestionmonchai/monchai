from rest_framework import serializers
from .models import Produit, Client, Commande, LigneCommande, Facture, Paiement


class ProduitSerializer(serializers.ModelSerializer):
    bouteille_lot_info = serializers.SerializerMethodField()
    prix_ht_eur = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'domaine', 'bouteille_lot', 'bouteille_lot_info', 'nom', 'sku',
            'prix_ttc_eur', 'prix_ht_eur', 'tva_pct', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bouteille_lot_info(self, obj):
        return {
            'id': obj.bouteille_lot.id,
            'nb_bouteilles': obj.bouteille_lot.nb_bouteilles,
            'contenance_ml': obj.bouteille_lot.contenance_ml,
            'ref_interne': obj.bouteille_lot.ref_interne
        }


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 'domaine', 'nom', 'email', 'telephone', 'adresse',
            'code_postal', 'ville', 'pays', 'siret', 'tva_intra',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LigneCommandeSerializer(serializers.ModelSerializer):
    produit_nom = serializers.ReadOnlyField(source='produit.nom')
    produit_sku = serializers.ReadOnlyField(source='produit.sku')
    total_ttc_eur = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_ht_eur = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = LigneCommande
        fields = [
            'id', 'commande', 'produit', 'produit_nom', 'produit_sku',
            'quantite', 'prix_unitaire_ttc_eur', 'prix_unitaire_ht_eur',
            'tva_pct', 'total_ttc_eur', 'total_ht_eur', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommandeSerializer(serializers.ModelSerializer):
    client_nom = serializers.ReadOnlyField(source='client.nom')
    lignes = LigneCommandeSerializer(many=True, read_only=True)
    total_ttc_eur = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Commande
        fields = [
            'id', 'domaine', 'client', 'client_nom', 'date',
            'status', 'commentaire', 'lignes', 'total_ttc_eur',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommandeCreateSerializer(serializers.ModelSerializer):
    lignes = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = Commande
        fields = ['domaine', 'client', 'date', 'commentaire', 'lignes']
    
    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        commande = Commande.objects.create(**validated_data)
        
        for ligne_data in lignes_data:
            LigneCommande.objects.create(
                commande=commande,
                **ligne_data
            )
        
        return commande


class FactureSerializer(serializers.ModelSerializer):
    commande_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Facture
        fields = [
            'id', 'domaine', 'commande', 'commande_info', 'numero',
            'date_emission', 'date_echeance', 'status', 'pdf_path',
            'total_ttc', 'tva', 'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_commande_info(self, obj):
        return {
            'id': obj.commande.id,
            'client_nom': obj.commande.client.nom,
            'date': obj.commande.date,
            'status': obj.commande.status
        }


class PaiementSerializer(serializers.ModelSerializer):
    facture_numero = serializers.ReadOnlyField(source='facture.numero')
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'facture', 'facture_numero', 'date', 'montant',
            'mode', 'reference', 'commentaire', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
