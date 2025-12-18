import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.core.tenancy import TenantManager


class Contenant(models.Model):
    # id auto-généré par Django (BigAutoField)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)
    # Hotfix: default manager scoped by current organization
    objects = TenantManager()

    code = models.CharField(max_length=50)
    label = models.CharField(max_length=120, blank=True)

    TYPE_CHOICES = [
        ('cuve_inox', 'Cuve inox'),
        ('cuve_beton', 'Cuve béton'),
        ('cuve_fibre', 'Cuve fibre'),
        ('fut_225', 'Fût 225L'),
        ('foudre', 'Foudre'),
        ('amphore', 'Amphore'),
        ('autre', 'Autre'),
    ]
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default='cuve_inox')

    capacite_l = models.DecimalField(max_digits=12, decimal_places=2)
    capacite_utile_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    localisation = models.CharField(max_length=120, blank=True)
    
    # ══════════════════════════════════════════════════════════════════════════════
    # CHAMPS SPÉCIFIQUES CUVES (thermorégulation)
    # ══════════════════════════════════════════════════════════════════════════════
    thermo_regule = models.BooleanField(default=False)
    TYPE_THERMOREGULATION_CHOICES = [
        ('double_enveloppe', 'Double enveloppe'),
        ('serpentin', 'Serpentin'),
        ('drapeaux', 'Drapeaux'),
        ('ceinture', 'Ceinture extérieure'),
        ('autre', 'Autre'),
    ]
    type_thermoregulation = models.CharField(
        max_length=32, choices=TYPE_THERMOREGULATION_CHOICES, blank=True,
        help_text="Type de système de thermorégulation"
    )
    # Plage de température conseillée (plus réaliste que temperature_cible seule)
    temperature_cible = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Température cible (legacy) - préférer min/max"
    )
    temperature_min = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Température minimale conseillée (°C)"
    )
    temperature_max = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Température maximale conseillée (°C)"
    )
    FORME_CHOICES = [
        ('cylindrique', 'Cylindrique'),
        ('tronconique', 'Tronconique'),
        ('ovoide', 'Ovoïde'),
        ('rectangulaire', 'Rectangulaire'),
        ('autre', 'Autre'),
    ]
    forme = models.CharField(
        max_length=32, choices=FORME_CHOICES, blank=True,
        help_text="Forme de la cuve (optionnel)"
    )
    
    # ══════════════════════════════════════════════════════════════════════════════
    # CHAMPS SPÉCIFIQUES BARRIQUES / FOUDRES (bois & élevage)
    # ══════════════════════════════════════════════════════════════════════════════
    ORIGINE_BOIS_CHOICES = [
        ('francais', 'Français'),
        ('americain', 'Américain'),
        ('mixte', 'Mixte'),
        ('hongrois', 'Hongrois'),
        ('autre', 'Autre'),
    ]
    origine_bois = models.CharField(
        max_length=32, choices=ORIGINE_BOIS_CHOICES, blank=True,
        help_text="Origine du bois (barriques/foudres)"
    )
    GRAIN_BOIS_CHOICES = [
        ('extra_fin', 'Extra fin'),
        ('fin', 'Fin'),
        ('moyen', 'Moyen'),
        ('gros', 'Gros'),
    ]
    grain_bois = models.CharField(
        max_length=32, choices=GRAIN_BOIS_CHOICES, blank=True,
        help_text="Grain du bois"
    )
    TYPE_CHAUFFE_CHOICES = [
        ('legere', 'Légère'),
        ('moyenne_moins', 'Moyenne -'),
        ('moyenne', 'Moyenne'),
        ('moyenne_plus', 'Moyenne +'),
        ('forte', 'Forte'),
    ]
    type_chauffe = models.CharField(
        max_length=32, choices=TYPE_CHAUFFE_CHOICES, blank=True,
        help_text="Type de chauffe"
    )
    tonnelier = models.CharField(
        max_length=100, blank=True,
        help_text="Nom du tonnelier / fabricant"
    )
    STATUT_BARRIQUE_CHOICES = [
        ('neuve', 'Neuve'),
        ('1_vin', '1 vin'),
        ('2_vins', '2 vins'),
        ('3_vins_plus', '3 vins et +'),
        ('a_reformer', 'À réformer'),
    ]
    statut_barrique = models.CharField(
        max_length=20, choices=STATUT_BARRIQUE_CHOICES, blank=True,
        help_text="Statut d'usage de la barrique/foudre"
    )
    annee_mise_service = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Année de première utilisation"
    )

    # Sanitaire / maintenance
    date_dernier_nettoyage = models.DateField(null=True, blank=True)
    cycle_nettoyage_j = models.IntegerField(null=True, blank=True)
    date_dernier_ouillage = models.DateField(null=True, blank=True)
    cycle_ouillage_j = models.IntegerField(null=True, blank=True)
    note_sanitaire = models.TextField(blank=True)

    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('occupe', 'Occupé'),
        ('nettoyage', 'En nettoyage'),
        ('maintenance', 'En maintenance'),
        ('hors_service', 'Hors service'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')

    # Lot en place (optionnel)
    lot_courant = models.ForeignKey('production.LotTechnique', null=True, blank=True, on_delete=models.SET_NULL, related_name='contenants')
    volume_occupe_l = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Sécurité / audit
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('organization', 'code')]
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'statut']),
        ]
        ordering = ('code',)

    def __str__(self):
        return f"{self.code} ({self.get_type_display()})"

    @property
    def capacite_utile_effective_l(self) -> Decimal:
        return self.capacite_utile_l or self.capacite_l

    def free_capacity_l(self) -> Decimal:
        try:
            cap = Decimal(str(self.capacite_utile_effective_l or 0))
            occ = Decimal(str(self.volume_occupe_l or 0))
            free = cap - occ
            return free if free > 0 else Decimal('0')
        except Exception:
            return Decimal('0')

    def can_receive(self, volume_l: float) -> bool:
        try:
            from decimal import Decimal as _D
            if self.statut == 'hors_service':
                return False
            if volume_l is None:
                return False
            vol = _D(str(volume_l))
            return self.statut in ('disponible', 'occupe') and vol <= self.free_capacity_l()
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════════
    # HELPERS pour UI contextuelle
    # ══════════════════════════════════════════════════════════════════════════════
    @property
    def is_cuve(self) -> bool:
        """Retourne True si le contenant est une cuve (inox, béton, fibre)"""
        return self.type in ('cuve_inox', 'cuve_beton', 'cuve_fibre')

    @property
    def is_barrique_or_foudre(self) -> bool:
        """Retourne True si le contenant est une barrique, fût ou foudre"""
        return self.type in ('fut_225', 'foudre')

    @property
    def temperature_range_display(self) -> str:
        """Affiche la plage de température ou la cible legacy"""
        if self.temperature_min is not None and self.temperature_max is not None:
            return f"{self.temperature_min}°C - {self.temperature_max}°C"
        elif self.temperature_cible is not None:
            return f"{self.temperature_cible}°C"
        return "—"

    @property
    def occupancy_pct(self) -> Decimal:
        """Calcule le taux d'occupation en pourcentage"""
        try:
            cap = Decimal(str(self.capacite_utile_effective_l or self.capacite_l or 0))
            if cap <= 0:
                return Decimal('0')
            occ = Decimal(str(self.volume_occupe_l or 0))
            pct = (occ / cap) * Decimal('100')
            return pct.quantize(Decimal('0.1'))
        except Exception:
            return Decimal('0')

    @property
    def occupancy_ratio(self) -> int:
        """Alias pour occupancy_pct en entier (pour les templates)"""
        try:
            return int(self.occupancy_pct)
        except Exception:
            return 0

    def recalculate_occupancy(self) -> None:
        """Recalcule le volume occupé à partir du lot courant"""
        if self.lot_courant_id:
            try:
                vol = self.lot_courant.volume_l or Decimal('0')
                self.volume_occupe_l = vol
                self.statut = 'occupe' if vol > 0 else 'disponible'
            except Exception:
                pass
        else:
            self.volume_occupe_l = Decimal('0')
            self.statut = 'disponible'
