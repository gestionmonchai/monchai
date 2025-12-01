"""
Modèles pour la gestion des stocks, entrepôts et mouvements
DB Roadmap 02 - Stocks, Entrepôts & Mouvements (Bouteilles & Vrac)
"""

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Organization
from apps.viticulture.models import Lot, Cuvee, UnitOfMeasure, Warehouse

User = get_user_model()


class BaseStockModel(models.Model):
    """Modèle de base pour tous les modèles de stock avec UUID et row_version"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        help_text="Organisation propriétaire"
    )
    row_version = models.PositiveIntegerField(
        default=1,
        help_text="Version pour locking optimiste"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.row_version += 1
        super().save(*args, **kwargs)



class SKU(BaseStockModel):
    """
    Stock Keeping Unit - Référence produit fini (bouteilles)
    sku(id, organization_id, cuvee_id, uom_id, volume_by_uom_to_l, label, code_barres, is_active, row_version)
    UNIQUE(organization_id, cuvee_id, uom_id)
    """
    
    cuvee = models.ForeignKey(
        Cuvee,
        on_delete=models.CASCADE,
        verbose_name="Cuvée"
    )
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.CASCADE,
        verbose_name="Unité de mesure"
    )
    volume_by_uom_to_l = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="Volume unitaire en litres",
        help_text="Volume d'une unité convertie en litres (ex: 0.75 pour une bouteille)"
    )
    label = models.CharField(
        max_length=200,
        verbose_name="Étiquette",
        help_text="Nom commercial du produit fini"
    )
    code_barres = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Code-barres",
        help_text="Code-barres EAN13 ou autre"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="SKU en production active"
    )
    
    class Meta:
        verbose_name = "SKU (Produit fini)"
        verbose_name_plural = "SKUs (Produits finis)"
        unique_together = [['organization', 'cuvee', 'uom']]
        ordering = ['label']
    
    def __str__(self):
        return f"{self.label} ({self.uom.code})"
    
    def clean(self):
        super().clean()
        
        # Validation: même organisation pour cuvée et UOM
        if self.cuvee and self.cuvee.organization != self.organization:
            raise ValidationError({
                'cuvee': 'La cuvée doit appartenir à la même organisation.'
            })
        
        if self.uom and self.uom.organization != self.organization:
            raise ValidationError({
                'uom': 'L\'unité de mesure doit appartenir à la même organisation.'
            })


class StockVracBalance(BaseStockModel):
    """
    Solde de stock vrac (liquide) par lot et entrepôt
    stock_vrac_balance(id, organization_id, lot_id, warehouse_id, qty_l, updated_at)
    UNIQUE(organization_id, lot_id, warehouse_id)
    """
    
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        verbose_name="Lot"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Entrepôt"
    )
    qty_l = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Quantité en litres"
    )
    
    class Meta:
        verbose_name = "Solde stock vrac"
        verbose_name_plural = "Soldes stock vrac"
        unique_together = [['organization', 'lot', 'warehouse']]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.lot} - {self.warehouse}: {self.qty_l}L"
    
    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.lot and self.lot.organization != self.organization:
            raise ValidationError({
                'lot': 'Le lot doit appartenir à la même organisation.'
            })
        
        if self.warehouse and self.warehouse.organization != self.organization:
            raise ValidationError({
                'warehouse': 'L\'entrepôt doit appartenir à la même organisation.'
            })


class StockSKUBalance(BaseStockModel):
    """
    Solde de stock SKU (bouteilles) par SKU et entrepôt
    stock_sku_balance(id, organization_id, sku_id, warehouse_id, qty_units, updated_at)
    UNIQUE(organization_id, sku_id, warehouse_id)
    """
    
    sku = models.ForeignKey(
        SKU,
        on_delete=models.CASCADE,
        verbose_name="SKU"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Entrepôt"
    )
    qty_units = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantité en unités"
    )
    
    class Meta:
        verbose_name = "Solde stock SKU"
        verbose_name_plural = "Soldes stock SKU"
        unique_together = [['organization', 'sku', 'warehouse']]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.sku} - {self.warehouse}: {self.qty_units} unités"
    
    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.sku and self.sku.organization != self.organization:
            raise ValidationError({
                'sku': 'Le SKU doit appartenir à la même organisation.'
            })
        
        if self.warehouse and self.warehouse.organization != self.organization:
            raise ValidationError({
                'warehouse': 'L\'entrepôt doit appartenir à la même organisation.'
            })


class StockVracMove(BaseStockModel):
    """
    Mouvement de stock vrac (append-only)
    stock_vrac_move(id, organization_id, lot_id, src_warehouse_id, dst_warehouse_id, qty_l, 
                   move_type, ref_type, ref_id, created_at, user_id)
    """
    
    MOVE_TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('transfert', 'Transfert'),
        ('ajustement', 'Ajustement inventaire'),
    ]
    
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        verbose_name="Lot"
    )
    src_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vrac_moves_src',
        verbose_name="Entrepôt source"
    )
    dst_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vrac_moves_dst',
        verbose_name="Entrepôt destination"
    )
    qty_l = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité en litres"
    )
    move_type = models.CharField(
        max_length=20,
        choices=MOVE_TYPE_CHOICES,
        verbose_name="Type de mouvement"
    )
    ref_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Type de référence",
        help_text="Type d'objet référencé (ex: 'order', 'production')"
    )
    ref_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="ID de référence",
        help_text="ID de l'objet référencé"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    class Meta:
        verbose_name = "Mouvement stock vrac"
        verbose_name_plural = "Mouvements stock vrac"
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['organization', 'lot']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['move_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_move_type_display()} - {self.lot}: {self.qty_l}L"
    
    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.lot and self.lot.organization != self.organization:
            raise ValidationError({
                'lot': 'Le lot doit appartenir à la même organisation.'
            })
        
        # Validation des entrepôts selon le type de mouvement
        if self.move_type == 'transfert':
            if not self.src_warehouse or not self.dst_warehouse:
                raise ValidationError(
                    'Un transfert nécessite un entrepôt source et destination.'
                )
            if self.src_warehouse == self.dst_warehouse:
                raise ValidationError(
                    'L\'entrepôt source et destination doivent être différents.'
                )
        elif self.move_type == 'entree':
            if self.src_warehouse:
                raise ValidationError(
                    'Une entrée ne doit pas avoir d\'entrepôt source.'
                )
            if not self.dst_warehouse:
                raise ValidationError(
                    'Une entrée doit avoir un entrepôt destination.'
                )
        elif self.move_type == 'sortie':
            if not self.src_warehouse:
                raise ValidationError(
                    'Une sortie doit avoir un entrepôt source.'
                )
            if self.dst_warehouse:
                raise ValidationError(
                    'Une sortie ne doit pas avoir d\'entrepôt destination.'
                )
        elif self.move_type == 'ajustement':
            if not self.dst_warehouse:
                raise ValidationError(
                    'Un ajustement doit spécifier l\'entrepôt concerné.'
                )
        
        # Validation: entrepôts de la même organisation
        if self.src_warehouse and self.src_warehouse.organization != self.organization:
            raise ValidationError({
                'src_warehouse': 'L\'entrepôt source doit appartenir à la même organisation.'
            })
        
        if self.dst_warehouse and self.dst_warehouse.organization != self.organization:
            raise ValidationError({
                'dst_warehouse': 'L\'entrepôt destination doit appartenir à la même organisation.'
            })


class StockSKUMove(BaseStockModel):
    """
    Mouvement de stock SKU (append-only)
    stock_sku_move(id, organization_id, sku_id, src_warehouse_id, dst_warehouse_id, qty_units,
                  move_type, ref_type, ref_id, created_at, user_id)
    """
    
    MOVE_TYPE_CHOICES = [
        ('fabrication', 'Fabrication (embouteillage)'),
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('transfert', 'Transfert'),
        ('ajustement', 'Ajustement inventaire'),
    ]
    
    sku = models.ForeignKey(
        SKU,
        on_delete=models.CASCADE,
        verbose_name="SKU"
    )
    src_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sku_moves_src',
        verbose_name="Entrepôt source"
    )
    dst_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sku_moves_dst',
        verbose_name="Entrepôt destination"
    )
    qty_units = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantité en unités"
    )
    move_type = models.CharField(
        max_length=20,
        choices=MOVE_TYPE_CHOICES,
        verbose_name="Type de mouvement"
    )
    ref_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Type de référence"
    )
    ref_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="ID de référence"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    class Meta:
        verbose_name = "Mouvement stock SKU"
        verbose_name_plural = "Mouvements stock SKU"
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['organization', 'sku']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['move_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_move_type_display()} - {self.sku}: {self.qty_units} unités"
    
    def clean(self):
        super().clean()
        
        # Validation: même organisation
        if self.sku and self.sku.organization != self.organization:
            raise ValidationError({
                'sku': 'Le SKU doit appartenir à la même organisation.'
            })
        
        # Validation des entrepôts selon le type de mouvement
        if self.move_type == 'transfert':
            if not self.src_warehouse or not self.dst_warehouse:
                raise ValidationError(
                    'Un transfert nécessite un entrepôt source et destination.'
                )
            if self.src_warehouse == self.dst_warehouse:
                raise ValidationError(
                    'L\'entrepôt source et destination doivent être différents.'
                )
        elif self.move_type in ['entree', 'fabrication']:
            if self.src_warehouse:
                raise ValidationError(
                    f'Une {self.move_type} ne doit pas avoir d\'entrepôt source.'
                )
            if not self.dst_warehouse:
                raise ValidationError(
                    f'Une {self.move_type} doit avoir un entrepôt destination.'
                )
        elif self.move_type == 'sortie':
            if not self.src_warehouse:
                raise ValidationError(
                    'Une sortie doit avoir un entrepôt source.'
                )
            if self.dst_warehouse:
                raise ValidationError(
                    'Une sortie ne doit pas avoir d\'entrepôt destination.'
                )
        elif self.move_type == 'ajustement':
            if not self.dst_warehouse:
                raise ValidationError(
                    'Un ajustement doit spécifier l\'entrepôt concerné.'
                )
        
        # Validation: entrepôts de la même organisation
        if self.src_warehouse and self.src_warehouse.organization != self.organization:
            raise ValidationError({
                'src_warehouse': 'L\'entrepôt source doit appartenir à la même organisation.'
            })
        
        if self.dst_warehouse and self.dst_warehouse.organization != self.organization:
            raise ValidationError({
                'dst_warehouse': 'L\'entrepôt destination doit appartenir à la même organisation.'
            })


# Managers pour les opérations de stock
class StockManager:
    """Manager pour les opérations de stock avec intégrité transactionnelle"""
    
    @staticmethod
    @transaction.atomic
    def move_vrac(lot, src_warehouse, dst_warehouse, qty_l, move_type, user, 
                  ref_type=None, ref_id=None, notes=''):
        """
        Effectue un mouvement de stock vrac avec mise à jour des soldes
        Garantit l'intégrité transactionnelle et la non-négativité des soldes
        """
        organization = lot.organization
        
        # Validation des soldes avant mouvement
        if move_type in ['sortie', 'transfert'] and src_warehouse:
            src_balance, _ = StockVracBalance.objects.get_or_create(
                organization=organization,
                lot=lot,
                warehouse=src_warehouse,
                defaults={'qty_l': Decimal('0')}
            )
            
            if src_balance.qty_l < qty_l:
                raise ValidationError(
                    f'Stock insuffisant: {src_balance.qty_l}L disponible, '
                    f'{qty_l}L demandé'
                )
        
        # Créer le mouvement
        move = StockVracMove.objects.create(
            organization=organization,
            lot=lot,
            src_warehouse=src_warehouse,
            dst_warehouse=dst_warehouse,
            qty_l=qty_l,
            move_type=move_type,
            ref_type=ref_type or '',
            ref_id=ref_id,
            user=user,
            notes=notes
        )
        
        # Mettre à jour les soldes
        if src_warehouse:
            src_balance, _ = StockVracBalance.objects.get_or_create(
                organization=organization,
                lot=lot,
                warehouse=src_warehouse,
                defaults={'qty_l': Decimal('0')}
            )
            src_balance.qty_l -= qty_l
            src_balance.save()
        
        if dst_warehouse:
            dst_balance, _ = StockVracBalance.objects.get_or_create(
                organization=organization,
                lot=lot,
                warehouse=dst_warehouse,
                defaults={'qty_l': Decimal('0')}
            )
            dst_balance.qty_l += qty_l
            dst_balance.save()
        
        return move
    
    @staticmethod
    @transaction.atomic
    def move_sku(sku, src_warehouse, dst_warehouse, qty_units, move_type, user,
                 ref_type=None, ref_id=None, notes=''):
        """
        Effectue un mouvement de stock SKU avec mise à jour des soldes
        """
        organization = sku.organization
        
        # Validation des soldes avant mouvement
        if move_type in ['sortie', 'transfert'] and src_warehouse:
            src_balance, _ = StockSKUBalance.objects.get_or_create(
                organization=organization,
                sku=sku,
                warehouse=src_warehouse,
                defaults={'qty_units': 0}
            )
            
            if src_balance.qty_units < qty_units:
                raise ValidationError(
                    f'Stock insuffisant: {src_balance.qty_units} unités disponibles, '
                    f'{qty_units} unités demandées'
                )
        
        # Créer le mouvement
        move = StockSKUMove.objects.create(
            organization=organization,
            sku=sku,
            src_warehouse=src_warehouse,
            dst_warehouse=dst_warehouse,
            qty_units=qty_units,
            move_type=move_type,
            ref_type=ref_type or '',
            ref_id=ref_id,
            user=user,
            notes=notes
        )
        
        # Mettre à jour les soldes
        if src_warehouse:
            src_balance, _ = StockSKUBalance.objects.get_or_create(
                organization=organization,
                sku=sku,
                warehouse=src_warehouse,
                defaults={'qty_units': 0}
            )
            src_balance.qty_units -= qty_units
            src_balance.save()
        
        if dst_warehouse:
            dst_balance, _ = StockSKUBalance.objects.get_or_create(
                organization=organization,
                sku=sku,
                warehouse=dst_warehouse,
                defaults={'qty_units': 0}
            )
            dst_balance.qty_units += qty_units
            dst_balance.save()
        
        return move
    
    @staticmethod
    @transaction.atomic
    def fabrication_sku(lot, sku, warehouse, qty_units, user, notes=''):
        """
        Fabrication de bouteilles: consomme du vrac et produit des SKU
        """
        organization = sku.organization
        
        # Calculer la quantité de vrac nécessaire
        qty_l_needed = Decimal(str(qty_units)) * sku.volume_by_uom_to_l
        
        # Vérifier le stock de vrac disponible
        vrac_balance, _ = StockVracBalance.objects.get_or_create(
            organization=organization,
            lot=lot,
            warehouse=warehouse,
            defaults={'qty_l': Decimal('0')}
        )
        
        if vrac_balance.qty_l < qty_l_needed:
            raise ValidationError(
                f'Stock vrac insuffisant: {vrac_balance.qty_l}L disponible, '
                f'{qty_l_needed}L nécessaire pour {qty_units} unités'
            )
        
        # Créer les mouvements
        vrac_move = StockManager.move_vrac(
            lot=lot,
            src_warehouse=warehouse,
            dst_warehouse=None,
            qty_l=qty_l_needed,
            move_type='sortie',
            user=user,
            ref_type='fabrication',
            notes=f'Fabrication {qty_units} x {sku.label}'
        )
        
        sku_move = StockManager.move_sku(
            sku=sku,
            src_warehouse=None,
            dst_warehouse=warehouse,
            qty_units=qty_units,
            move_type='fabrication',
            user=user,
            ref_type='fabrication',
            ref_id=vrac_move.id,
            notes=notes
        )
        
        return vrac_move, sku_move


class StockTransfer(BaseStockModel):
    """
    Journal des transferts entre entrepôts - Roadmap 32
    stock_transfer(id, org_id, lot_id, from_warehouse_id, to_warehouse_id, 
                  volume_l, client_token, created_by, created_at)
    """
    
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        verbose_name="Lot"
    )
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='transfers_from',
        verbose_name="Entrepôt source"
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='transfers_to',
        verbose_name="Entrepôt destination"
    )
    volume_l = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Volume transféré (L)"
    )
    client_token = models.CharField(
        max_length=100,
        help_text="Token client pour idempotence"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Créé par"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    class Meta:
        verbose_name = "Transfert stock"
        verbose_name_plural = "Transferts stock"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'client_token']),
            models.Index(fields=['organization', 'lot', 'created_at']),
            models.Index(fields=['organization', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'client_token'],
                name='unique_org_client_token'
            ),
            models.CheckConstraint(
                check=~models.Q(from_warehouse=models.F('to_warehouse')),
                name='different_warehouses'
            )
        ]
    
    def __str__(self):
        return f"Transfert {self.lot} : {self.from_warehouse} → {self.to_warehouse} ({self.volume_l}L)"
    
    @classmethod
    def create_transfer(cls, organization, lot, from_warehouse, to_warehouse, 
                       volume_l, user, client_token, notes=""):
        """
        Crée un transfert atomique avec double mouvement
        Implémente la logique de la roadmap 32
        """
        from django.db import transaction
        from .services import StockService
        
        # Vérifications préliminaires
        if from_warehouse == to_warehouse:
            raise ValidationError("Les entrepôts source et destination doivent être différents")
        
        if volume_l <= 0:
            raise ValidationError("Le volume doit être positif")
        
        # Vérifier idempotence
        existing = cls.objects.filter(
            organization=organization,
            client_token=client_token
        ).first()
        
        if existing:
            return existing, False  # Déjà créé
        
        with transaction.atomic():
            # Vérifier solde disponible
            balance = StockService.get_lot_balance(organization, lot, from_warehouse)
            if balance < volume_l:
                raise ValidationError(f"Solde insuffisant: {balance}L disponible, {volume_l}L demandé")
            
            # Créer le transfert
            transfer = cls.objects.create(
                organization=organization,
                lot=lot,
                from_warehouse=from_warehouse,
                to_warehouse=to_warehouse,
                volume_l=volume_l,
                client_token=client_token,
                created_by=user,
                notes=notes
            )
            
            # Créer les 2 mouvements
            out_move = StockVracMove.objects.create(
                organization=organization,
                lot=lot,
                src_warehouse=from_warehouse,
                dst_warehouse=None,
                qty_l=volume_l,
                move_type='transfert',
                ref_type='transfer',
                ref_id=transfer.id,
                user=user,
                notes=f"Transfert vers {to_warehouse.name}"
            )
            
            in_move = StockVracMove.objects.create(
                organization=organization,
                lot=lot,
                src_warehouse=None,
                dst_warehouse=to_warehouse,
                qty_l=volume_l,
                move_type='transfert',
                ref_type='transfer',
                ref_id=transfer.id,
                user=user,
                notes=f"Transfert depuis {from_warehouse.name}"
            )
            
            # Mettre à jour les balances
            StockService.update_balance_after_move(out_move)
            StockService.update_balance_after_move(in_move)
            
            return transfer, True  # Nouvellement créé


class StockThreshold(BaseStockModel):
    """
    Seuils de stock pour alertes - Roadmap 34
    stock_threshold(org, scope, ref_id?, threshold_l, is_active, created_by, updated_at)
    """
    
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('cuvee', 'Par cuvée'),
        ('lot', 'Par lot'),
        ('warehouse', 'Par entrepôt'),
    ]
    
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        verbose_name="Portée du seuil"
    )
    ref_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID de référence (cuvée, lot, entrepôt) selon scope"
    )
    threshold_l = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Seuil en litres"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Seuil actif"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Créé par"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    class Meta:
        verbose_name = "Seuil de stock"
        verbose_name_plural = "Seuils de stock"
        ordering = ['scope', 'threshold_l']
        indexes = [
            models.Index(fields=['organization', 'scope', 'is_active']),
            models.Index(fields=['organization', 'ref_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'scope', 'ref_id'],
                name='unique_threshold_per_scope_ref'
            ),
            models.CheckConstraint(
                check=models.Q(threshold_l__gt=0),
                name='positive_threshold'
            )
        ]
    
    def clean(self):
        super().clean()
        
        # Validation scope vs ref_id
        if self.scope == 'global' and self.ref_id is not None:
            raise ValidationError("Le seuil global ne doit pas avoir de ref_id")
        
        if self.scope != 'global' and self.ref_id is None:
            raise ValidationError(f"Le seuil {self.scope} doit avoir un ref_id")
        
        # Validation same organization pour ref_id
        if self.ref_id:
            if self.scope == 'cuvee':
                try:
                    cuvee = Cuvee.objects.get(id=self.ref_id)
                    if cuvee.organization != self.organization:
                        raise ValidationError("La cuvée doit appartenir à la même organisation")
                except Cuvee.DoesNotExist:
                    raise ValidationError("Cuvée non trouvée")
            
            elif self.scope == 'lot':
                try:
                    lot = Lot.objects.get(id=self.ref_id)
                    if lot.organization != self.organization:
                        raise ValidationError("Le lot doit appartenir à la même organisation")
                except Lot.DoesNotExist:
                    raise ValidationError("Lot non trouvé")
            
            elif self.scope == 'warehouse':
                try:
                    warehouse = Warehouse.objects.get(id=self.ref_id)
                    if warehouse.organization != self.organization:
                        raise ValidationError("L'entrepôt doit appartenir à la même organisation")
                except Warehouse.DoesNotExist:
                    raise ValidationError("Entrepôt non trouvé")
    
    def __str__(self):
        if self.scope == 'global':
            return f"Seuil global: {self.threshold_l}L"
        else:
            return f"Seuil {self.scope}: {self.threshold_l}L (ref: {self.ref_id})"
    
    def get_reference_object(self):
        """Retourne l'objet de référence selon le scope"""
        if not self.ref_id:
            return None
        
        if self.scope == 'cuvee':
            return Cuvee.objects.filter(id=self.ref_id, organization=self.organization).first()
        elif self.scope == 'lot':
            return Lot.objects.filter(id=self.ref_id, organization=self.organization).first()
        elif self.scope == 'warehouse':
            return Warehouse.objects.filter(id=self.ref_id, organization=self.organization).first()
        
        return None


class StockAlert(BaseStockModel):
    """
    Alertes de stock bas - Roadmap 34
    stock_alert(org, lot_id, warehouse_id, balance_l, threshold_l, first_seen_at, acknowledged_by?, acknowledged_at?)
    """
    
    lot = models.ForeignKey(
        Lot,
        on_delete=models.CASCADE,
        verbose_name="Lot"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Entrepôt"
    )
    balance_l = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name="Solde actuel (L)"
    )
    threshold_l = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name="Seuil appliqué (L)"
    )
    threshold_source = models.CharField(
        max_length=20,
        choices=StockThreshold.SCOPE_CHOICES,
        verbose_name="Source du seuil"
    )
    first_seen_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Première détection"
    )
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Acquittée par"
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Acquittée le"
    )
    auto_resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Résolue automatiquement le"
    )
    
    class Meta:
        verbose_name = "Alerte de stock"
        verbose_name_plural = "Alertes de stock"
        ordering = ['-first_seen_at']
        indexes = [
            models.Index(fields=['organization', 'acknowledged_at', 'first_seen_at']),
            models.Index(fields=['organization', 'lot', 'warehouse']),
            models.Index(fields=['organization', 'first_seen_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'lot', 'warehouse'],
                condition=models.Q(acknowledged_at__isnull=True, auto_resolved_at__isnull=True),
                name='unique_active_alert_per_lot_warehouse'
            )
        ]
    
    def clean(self):
        super().clean()
        
        # Validation same organization
        if self.lot.organization != self.organization:
            raise ValidationError("Le lot doit appartenir à la même organisation")
        
        if self.warehouse.organization != self.organization:
            raise ValidationError("L'entrepôt doit appartenir à la même organisation")
        
        # Validation balance < threshold
        if self.balance_l >= self.threshold_l:
            raise ValidationError("Le solde doit être inférieur au seuil pour créer une alerte")
    
    def __str__(self):
        status = "Active"
        if self.acknowledged_at:
            status = "Acquittée"
        elif self.auto_resolved_at:
            status = "Résolue auto"
        
        return f"Alerte {status}: {self.lot.code} ({self.warehouse.name}) - {self.balance_l}L < {self.threshold_l}L"
    
    @property
    def is_active(self):
        """Alerte active = non acquittée et non résolue automatiquement"""
        return self.acknowledged_at is None and self.auto_resolved_at is None
    
    @property
    def criticality_ratio(self):
        """Ratio de criticité (0-1) : plus c'est proche de 0, plus c'est critique"""
        if self.threshold_l <= 0:
            return 0
        return float(self.balance_l / self.threshold_l)
    
    @property
    def days_since_first_seen(self):
        """Nombre de jours depuis la première détection"""
        return (timezone.now() - self.first_seen_at).days
    
    def acknowledge(self, user):
        """Acquitter l'alerte"""
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def auto_resolve(self):
        """Résoudre automatiquement l'alerte (stock remonté)"""
        self.auto_resolved_at = timezone.now()
        self.save()
