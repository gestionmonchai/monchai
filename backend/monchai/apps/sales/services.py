"""
Services pour la gestion des ventes et déduction de stock
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import Produit, Client, Commande, LigneCommande, Facture
from monchai.apps.core.models import Mouvement, BouteilleLot
from monchai.apps.accounts.models import Domaine


class StockService:
    """Service pour la gestion du stock de produits"""
    
    @staticmethod
    def get_stock_disponible(produit_id):
        """Calcule le stock disponible pour un produit"""
        try:
            produit = Produit.objects.get(id=produit_id)
            bouteille_lot = produit.bouteille_lot
            
            # Stock initial = nb_bouteilles du BouteilleLot
            stock_initial = bouteille_lot.nb_bouteilles
            
            # Déductions = somme des mouvements de vente validés
            mouvements_vente = Mouvement.objects.filter(
                domaine=produit.domaine,
                type='vente_sortie_stock',
                status='valide',
                produit_id=produit_id
            )
            
            total_vendu = sum(
                int(mouvement.commentaire.split('quantite:')[1].split(',')[0]) 
                if 'quantite:' in mouvement.commentaire else 0
                for mouvement in mouvements_vente
            )
            
            return max(0, stock_initial - total_vendu)
            
        except Produit.DoesNotExist:
            return 0


class VenteService:
    """Service pour la gestion des ventes avec déduction de stock"""
    
    @staticmethod
    @transaction.atomic
    def creer_commande(client_id, lignes_data, date_commande, commentaire="", domaine=None):
        """
        Crée une commande avec validation du stock
        
        Args:
            client_id: ID du client
            lignes_data: Liste de dict avec produit_id, quantite, prix_unitaire_ttc_eur
            date_commande: Date de la commande
            commentaire: Commentaire optionnel
            domaine: Domaine (requis)
        
        Returns:
            Commande créée
        """
        if not domaine:
            raise ValidationError("Le domaine est requis")
        
        # Vérifier le client
        try:
            client = Client.objects.get(id=client_id, domaine=domaine)
        except Client.DoesNotExist:
            raise ValidationError(f"Client {client_id} non trouvé dans ce domaine")
        
        # Valider le stock pour chaque ligne
        for ligne_data in lignes_data:
            produit_id = ligne_data['produit_id']
            quantite = ligne_data['quantite']
            
            try:
                produit = Produit.objects.get(id=produit_id, domaine=domaine)
            except Produit.DoesNotExist:
                raise ValidationError(f"Produit {produit_id} non trouvé dans ce domaine")
            
            stock_disponible = StockService.get_stock_disponible(produit_id)
            
            if quantite > stock_disponible:
                raise ValidationError(
                    f"Stock insuffisant pour {produit.nom}. "
                    f"Demandé: {quantite}, Disponible: {stock_disponible}"
                )
        
        # Créer la commande
        commande = Commande.objects.create(
            domaine=domaine,
            client=client,
            date=date_commande,
            status='brouillon',
            commentaire=commentaire
        )
        
        # Créer les lignes
        for ligne_data in lignes_data:
            produit = Produit.objects.get(id=ligne_data['produit_id'], domaine=domaine)
            
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=ligne_data['quantite'],
                prix_unitaire_ttc_eur=ligne_data.get('prix_unitaire_ttc_eur', produit.prix_ttc_eur),
                tva_pct=ligne_data.get('tva_pct', produit.tva_pct)
            )
        
        return commande
    
    @staticmethod
    @transaction.atomic
    def confirmer_commande(commande_id):
        """
        Confirme une commande et crée les mouvements de sortie de stock
        
        Args:
            commande_id: ID de la commande
            
        Returns:
            Commande confirmée avec mouvements créés
        """
        try:
            commande = Commande.objects.get(id=commande_id)
        except Commande.DoesNotExist:
            raise ValidationError(f"Commande {commande_id} non trouvée")
        
        if commande.status != 'brouillon':
            raise ValidationError(f"Seules les commandes brouillon peuvent être confirmées")
        
        # Vérifier à nouveau le stock (sécurité)
        for ligne in commande.lignes.all():
            stock_disponible = StockService.get_stock_disponible(ligne.produit.id)
            
            if ligne.quantite > stock_disponible:
                raise ValidationError(
                    f"Stock insuffisant pour {ligne.produit.nom}. "
                    f"Demandé: {ligne.quantite}, Disponible: {stock_disponible}"
                )
        
        # Créer les mouvements de sortie de stock
        mouvements_crees = []
        
        for ligne in commande.lignes.all():
            # Créer un mouvement de sortie de stock
            mouvement = Mouvement.objects.create(
                domaine=commande.domaine,
                type='vente_sortie_stock',
                date=commande.date,
                volume_hl=Decimal('0'),  # Les ventes ne concernent pas les volumes HL
                status='valide',  # Directement validé
                commentaire=f"Vente commande #{commande.id} - {ligne.produit.nom} - quantite:{ligne.quantite}, prix_unitaire:{ligne.prix_unitaire_ttc_eur}",
                produit_id=ligne.produit.id
            )
            mouvements_crees.append(mouvement)
        
        # Mettre à jour le statut de la commande
        commande.status = 'confirmee'
        commande.save()
        
        return commande, mouvements_crees


class FactureService:
    """Service pour la génération de factures"""
    
    @staticmethod
    def generer_numero_facture(domaine):
        """Génère un numéro de facture unique pour le domaine"""
        annee = date.today().year
        
        # Compter les factures de l'année
        nb_factures = Facture.objects.filter(
            domaine=domaine,
            date_emission__year=annee
        ).count()
        
        return f"FAC{annee}{domaine.id:03d}{nb_factures + 1:04d}"
    
    @staticmethod
    @transaction.atomic
    def creer_facture_depuis_commande(commande_id, date_emission=None, date_echeance=None):
        """
        Crée une facture à partir d'une commande confirmée
        
        Args:
            commande_id: ID de la commande
            date_emission: Date d'émission (par défaut aujourd'hui)
            date_echeance: Date d'échéance (par défaut +30 jours)
            
        Returns:
            Facture créée
        """
        try:
            commande = Commande.objects.get(id=commande_id)
        except Commande.DoesNotExist:
            raise ValidationError(f"Commande {commande_id} non trouvée")
        
        if commande.status != 'confirmee':
            raise ValidationError("Seules les commandes confirmées peuvent être facturées")
        
        if hasattr(commande, 'facture'):
            raise ValidationError("Cette commande a déjà une facture")
        
        if not date_emission:
            date_emission = date.today()
        
        if not date_echeance:
            date_echeance = date_emission + timedelta(days=30)
        
        # Calculer les totaux et TVA
        total_ttc = commande.total_ttc_eur
        
        # Calculer la répartition TVA
        tva_details = {}
        for ligne in commande.lignes.all():
            taux = float(ligne.tva_pct)
            if taux not in tva_details:
                tva_details[taux] = {
                    'base_ht': 0,
                    'montant_tva': 0
                }
            
            base_ht = float(ligne.total_ht_eur)
            montant_tva = float(ligne.total_ttc_eur - ligne.total_ht_eur)
            
            tva_details[taux]['base_ht'] += base_ht
            tva_details[taux]['montant_tva'] += montant_tva
        
        # Créer la facture
        facture = Facture.objects.create(
            domaine=commande.domaine,
            commande=commande,
            numero=FactureService.generer_numero_facture(commande.domaine),
            date_emission=date_emission,
            date_echeance=date_echeance,
            status='emise',
            total_ttc=total_ttc,
            tva=tva_details
        )
        
        return facture
