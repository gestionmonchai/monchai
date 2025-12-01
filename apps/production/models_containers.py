import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.core.tenancy import TenantManager


class Contenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    temperature_cible = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    thermo_regule = models.BooleanField(default=False)

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
