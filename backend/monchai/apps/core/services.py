"""
Services pour la gestion des mouvements de vin avec règles métier
"""
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Mouvement, Lot, Cuve, BouteilleLot


class MouvementService:
    """Service pour gérer les mouvements de vin avec règles métier"""
    
    @staticmethod
    def create_inter_cuves(source_lot_id, destination_cuve_id, volume_hl, date, commentaire="", domaine=None):
        """
        Crée un mouvement inter-cuves avec validation des règles métier
        
        Args:
            source_lot_id: ID du lot source
            destination_cuve_id: ID de la cuve destination
            volume_hl: Volume à transférer (Decimal)
            date: Date du mouvement
            commentaire: Commentaire optionnel
            domaine: Domaine (sera déduit du lot source si non fourni)
        
        Returns:
            Mouvement: Le mouvement créé
            
        Raises:
            ValidationError: Si les règles métier ne sont pas respectées
        """
        try:
            source_lot = Lot.objects.get(id=source_lot_id)
            destination_cuve = Cuve.objects.get(id=destination_cuve_id)
        except (Lot.DoesNotExist, Cuve.DoesNotExist):
            raise ValidationError("Lot source ou cuve destination introuvable")
        
        # Validation du domaine
        if domaine is None:
            domaine = source_lot.domaine
        
        if source_lot.domaine != domaine or destination_cuve.domaine != domaine:
            raise ValidationError("Le lot source et la cuve destination doivent appartenir au même domaine")
        
        # Validation du volume
        volume_hl = Decimal(str(volume_hl))
        if volume_hl <= 0:
            raise ValidationError("Le volume doit être positif")
        
        if volume_hl > source_lot.volume_disponible_hl:
            raise ValidationError(
                f"Volume insuffisant dans le lot source. "
                f"Disponible: {source_lot.volume_disponible_hl} hl, "
                f"Demandé: {volume_hl} hl"
            )
        
        # Création du mouvement
        mouvement = Mouvement.objects.create(
            domaine=domaine,
            type="inter_cuves",
            source_lot=source_lot,
            destination_cuve=destination_cuve,
            volume_hl=volume_hl,
            date=date,
            commentaire=commentaire,
            status="draft"
        )
        
        return mouvement
    
    @staticmethod
    def create_perte(source_lot_id, volume_hl, date, commentaire="", domaine=None):
        """
        Crée un mouvement de perte
        
        Args:
            source_lot_id: ID du lot source
            volume_hl: Volume de perte (Decimal)
            date: Date du mouvement
            commentaire: Commentaire obligatoire pour les pertes
            domaine: Domaine (sera déduit du lot source si non fourni)
        
        Returns:
            Mouvement: Le mouvement créé
        """
        try:
            source_lot = Lot.objects.get(id=source_lot_id)
        except Lot.DoesNotExist:
            raise ValidationError("Lot source introuvable")
        
        if domaine is None:
            domaine = source_lot.domaine
        
        if source_lot.domaine != domaine:
            raise ValidationError("Le lot source doit appartenir au domaine")
        
        # Validation du volume
        volume_hl = Decimal(str(volume_hl))
        if volume_hl <= 0:
            raise ValidationError("Le volume de perte doit être positif")
        
        if volume_hl > source_lot.volume_disponible_hl:
            raise ValidationError(
                f"Volume insuffisant dans le lot source. "
                f"Disponible: {source_lot.volume_disponible_hl} hl, "
                f"Demandé: {volume_hl} hl"
            )
        
        if not commentaire.strip():
            raise ValidationError("Un commentaire est obligatoire pour les pertes")
        
        # Création du mouvement
        mouvement = Mouvement.objects.create(
            domaine=domaine,
            type="perte",
            source_lot=source_lot,
            volume_hl=volume_hl,
            date=date,
            commentaire=commentaire,
            status="draft"
        )
        
        return mouvement
    
    @staticmethod
    def create_vendange_vers_cuve(vendange_id, destination_cuve_id, date=None):
        """
        Crée un mouvement vendange vers cuve
        
        Args:
            vendange_id: ID de la vendange
            destination_cuve_id: ID de la cuve destination
            date: Date du mouvement (par défaut date de vendange)
        
        Returns:
            Mouvement: Le mouvement créé
        """
        from .models import Vendange
        
        try:
            vendange = Vendange.objects.get(id=vendange_id)
            destination_cuve = Cuve.objects.get(id=destination_cuve_id)
        except (Vendange.DoesNotExist, Cuve.DoesNotExist):
            raise ValidationError("Vendange ou cuve destination introuvable")
        
        if vendange.parcelle.domaine != destination_cuve.domaine:
            raise ValidationError("La vendange et la cuve destination doivent appartenir au même domaine")
        
        if date is None:
            date = vendange.date
        
        # Volume net = volume brut - déchets
        volume_net = vendange.volume_hl - vendange.dechets_hl
        
        if volume_net <= 0:
            raise ValidationError("Le volume net de la vendange doit être positif")
        
        # Création du mouvement
        mouvement = Mouvement.objects.create(
            domaine=vendange.parcelle.domaine,
            type="vendange_vers_cuve",
            destination_cuve=destination_cuve,
            volume_hl=volume_net,
            pertes_hl=vendange.dechets_hl,
            date=date,
            commentaire=f"Vendange {vendange.parcelle.nom} - {vendange.date}",
            status="draft",
            meta_json={"vendange_id": vendange_id}
        )
        
        return mouvement
    
    @staticmethod
    @transaction.atomic
    def valider_mouvement(mouvement_id):
        """
        Valide un mouvement et applique les changements aux lots
        
        Args:
            mouvement_id: ID du mouvement à valider
        
        Returns:
            Mouvement: Le mouvement validé
        
        Raises:
            ValidationError: Si le mouvement ne peut pas être validé
        """
        try:
            mouvement = Mouvement.objects.select_for_update().get(id=mouvement_id)
        except Mouvement.DoesNotExist:
            raise ValidationError("Mouvement introuvable")
        
        if mouvement.status != "draft":
            raise ValidationError(f"Seuls les mouvements en brouillon peuvent être validés. Statut actuel: {mouvement.status}")
        
        # Appliquer les changements selon le type de mouvement
        if mouvement.type == "inter_cuves":
            MouvementService._appliquer_inter_cuves(mouvement)
        elif mouvement.type == "perte":
            MouvementService._appliquer_perte(mouvement)
        elif mouvement.type == "vendange_vers_cuve":
            MouvementService._appliquer_vendange_vers_cuve(mouvement)
        elif mouvement.type == "mise_en_bouteille":
            MouvementService._appliquer_mise_en_bouteille(mouvement)
        
        # Marquer le mouvement comme validé
        mouvement.status = "valide"
        mouvement.save()
        
        return mouvement
    
    @staticmethod
    def _appliquer_inter_cuves(mouvement):
        """Applique un mouvement inter-cuves"""
        # Débit du lot source
        mouvement.source_lot.volume_disponible_hl -= mouvement.volume_hl
        mouvement.source_lot.save()
        
        # Crédit vers la cuve destination (créer ou mettre à jour le lot)
        lot_destination, created = Lot.objects.get_or_create(
            domaine=mouvement.domaine,
            cuve=mouvement.destination_cuve,
            defaults={
                'volume_disponible_hl': Decimal('0'),
                'ref_interne': f"Lot-{mouvement.destination_cuve.nom}-{mouvement.date}"
            }
        )
        
        lot_destination.volume_disponible_hl += mouvement.volume_hl
        lot_destination.save()
    
    @staticmethod
    def _appliquer_perte(mouvement):
        """Applique un mouvement de perte"""
        # Débit du lot source
        mouvement.source_lot.volume_disponible_hl -= mouvement.volume_hl
        mouvement.source_lot.save()
    
    @staticmethod
    def _appliquer_vendange_vers_cuve(mouvement):
        """Applique un mouvement vendange vers cuve"""
        # Crédit vers la cuve destination
        lot_destination, created = Lot.objects.get_or_create(
            domaine=mouvement.domaine,
            cuve=mouvement.destination_cuve,
            defaults={
                'volume_disponible_hl': Decimal('0'),
                'ref_interne': f"Vendange-{mouvement.destination_cuve.nom}-{mouvement.date}"
            }
        )
        
        lot_destination.volume_disponible_hl += mouvement.volume_hl
        lot_destination.save()
    
    @staticmethod
    def _appliquer_mise_en_bouteille(mouvement):
        """Applique un mouvement de mise en bouteille"""
        # Débit du lot source
        mouvement.source_lot.volume_disponible_hl -= mouvement.volume_hl
        mouvement.source_lot.save()
        
        # La création du BouteilleLot est gérée par le service MiseEnBouteilleService


class MiseEnBouteilleService:
    """Service pour la mise en bouteille"""
    
    @staticmethod
    @transaction.atomic
    def executer_mise_en_bouteille(source_lot_id, nb_bouteilles, contenance_ml, taux_perte_hl=0, date=None, domaine=None):
        """
        Exécute une mise en bouteille complète
        
        Args:
            source_lot_id: ID du lot source
            nb_bouteilles: Nombre de bouteilles
            contenance_ml: Contenance en ml
            taux_perte_hl: Taux de perte en hl (optionnel)
            date: Date de mise en bouteille
            domaine: Domaine
        
        Returns:
            tuple: (mouvement, bouteille_lot)
        """
        try:
            source_lot = Lot.objects.get(id=source_lot_id)
        except Lot.DoesNotExist:
            raise ValidationError("Lot source introuvable")
        
        if domaine is None:
            domaine = source_lot.domaine
        
        # Calcul du volume théorique nécessaire
        volume_theorique_hl = Decimal(str(nb_bouteilles * contenance_ml)) / Decimal('100000')  # ml vers hl
        volume_total_hl = volume_theorique_hl + Decimal(str(taux_perte_hl))
        
        if volume_total_hl > source_lot.volume_disponible_hl:
            raise ValidationError(
                f"Volume insuffisant. Nécessaire: {volume_total_hl} hl, "
                f"Disponible: {source_lot.volume_disponible_hl} hl"
            )
        
        # Créer le mouvement de mise en bouteille
        mouvement = Mouvement.objects.create(
            domaine=domaine,
            type="mise_en_bouteille",
            source_lot=source_lot,
            volume_hl=volume_total_hl,
            pertes_hl=taux_perte_hl,
            date=date,
            commentaire=f"Mise en bouteille: {nb_bouteilles} x {contenance_ml}ml",
            status="draft"
        )
        
        # Créer le lot de bouteilles
        bouteille_lot = BouteilleLot.objects.create(
            domaine=domaine,
            source_lot=source_lot,
            nb_bouteilles=nb_bouteilles,
            contenance_ml=contenance_ml,
            date=date,
            ref_interne=f"BL-{source_lot.cuve.nom}-{date}"
        )
        
        # Valider le mouvement
        mouvement = MouvementService.valider_mouvement(mouvement.id)
        
        return mouvement, bouteille_lot
