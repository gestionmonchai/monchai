from __future__ import annotations
from django.db import models, transaction
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization
from django.conf import settings
from apps.core.tenancy import TenantManager
# Register MS models (lightweight) from separate module
try:
    from .models_ms import MSItem, MSEmplacement, MSMove, MSMoveNature, MSReservation, MSFamily  # noqa: F401
except Exception:
    # Safe import guard during migrations or partial environments
    MSItem = MSEmplacement = MSMove = MSMoveNature = MSReservation = MSFamily = None

# Register Contenants model from separate module
try:
    from .models_containers import Contenant  # noqa: F401
except Exception:
    Contenant = None


class Parcelle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200)
    cepage = models.CharField(max_length=120, blank=True)
    surface_ha = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        ordering = ("nom",)

    def __str__(self) -> str:
        return self.nom


class VendangeReception(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200, blank=True)
    date = models.DateField(default=timezone.now)
    # Code lisible de type VND-YYYY-###
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    parcelle = models.ForeignKey('referentiels.Parcelle', on_delete=models.PROTECT, related_name="vendanges")
    cepage = models.ForeignKey('referentiels.Cepage', on_delete=models.SET_NULL, null=True, blank=True, related_name='vendanges', verbose_name="Cépage")
    cuvee = models.ForeignKey('referentiels.Cuvee', on_delete=models.SET_NULL, null=True, blank=True, related_name='vendanges')
    # Rangs vendangés (auto-détecte le cépage selon l'encépagement de la parcelle)
    rang_debut = models.PositiveIntegerField(null=True, blank=True, verbose_name="Rang début")
    rang_fin = models.PositiveIntegerField(null=True, blank=True, verbose_name="Rang fin")
    # Poids total (peut être calculé depuis les lignes ou saisi directement)
    poids_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    degre_potentiel = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    prix_raisin_eur_kg = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="Prix d'achat raisin (EUR/kg)")
    # Types & statut
    TYPE_VENDANGE_CHOICES = (
        ("manuel", "Manuel"),
        ("machine", "Machine"),
    )
    TYPE_RECOLTE_CHOICES = (
        ("blanc", "Blanc"),
        ("rouge", "Rouge"),
        ("rose", "Rosé"),
        ("base_effervescente", "Base effervescente"),
    )
    STATUT_CHOICES = (
        ("brouillon", "Brouillon"),
        ("receptionnee", "Réceptionnée"),
        ("affectee_cuvee", "Affectée à une cuvée"),
        ("encuvee", "Encuvée/Pressurée"),
        ("close", "Clôturée"),
    )
    type_vendange = models.CharField(max_length=12, choices=TYPE_VENDANGE_CHOICES, default="manuel")
    type_recolte = models.CharField(max_length=20, choices=TYPE_RECOLTE_CHOICES, default="blanc")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="receptionnee")
    temperature_c = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tri = models.BooleanField(default=False)
    tri_notes = models.CharField(max_length=200, blank=True)
    bennes_palox = models.CharField(max_length=200, blank=True)
    volume_mesure_l = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rendement_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    etat_sanitaire = models.CharField(max_length=40, blank=True)
    etat_sanitaire_notes = models.CharField(max_length=200, blank=True)
    contenant = models.CharField(max_length=64, blank=True, help_text="Contenant cible saisi à l'encuvage")
    notes = models.TextField(blank=True)
    campagne = models.CharField(max_length=9, help_text="AAAA-AAAA", blank=True)
    # Suivi fractionnement encuvage: kg débités cumulés
    kg_debites_cumules = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    auto_create_lot = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    TENANT_ORG_LOOKUPS = (
        'organization',
        'cuvee__organization',
    )
    objects = TenantManager()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-created_at")
        indexes = [
            models.Index(fields=["cuvee", "date"]),
            models.Index(fields=["campagne"]),
            models.Index(fields=["organization"]),
        ]

    def save(self, *args, **kwargs):
        if not self.campagne and self.date:
            y = self.date.year
            self.campagne = f"{y}-{y+1}"
        # Générer un code lisible si absent
        if not self.code:
            year = (self.date.year if self.date else timezone.now().year)
            # Tentative de génération de code unique (max 5 essais)
            for _ in range(5):
                try:
                    code = generate_vendange_code(year)
                    # Utiliser _base_manager pour vérifier l'existence globale (toutes organisations)
                    if not VendangeReception._base_manager.filter(code=code).exists():
                        self.code = code
                        break
                except Exception:
                    pass
            
            # Fallback si échec de la séquence
            if not self.code:
                self.code = f"VND-{year}-{uuid.uuid4().hex[:6].upper()}"
                
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Vendange {self.date} - {self.parcelle}"

    @property
    def poids_total(self):
        """Poids total = somme des lignes ou poids_kg si pas de lignes."""
        from decimal import Decimal
        lignes_total = self.lignes.aggregate(total=models.Sum('quantite_kg'))['total']
        if lignes_total:
            return lignes_total
        return self.poids_kg or Decimal('0')

    @property
    def kg_restant(self):
        """Poids restant disponible pour encuvage.
        Protège contre des valeurs négatives si données incohérentes.
        """
        try:
            from decimal import Decimal
            tot = Decimal(str(self.poids_total or 0))
            deb = Decimal(str(getattr(self, 'kg_debites_cumules', 0) or 0))
            rem = tot - deb
            return rem if rem > 0 else Decimal('0')
        except Exception:
            return 0


class VendangeLigne(models.Model):
    """Ligne de détail par cépage pour une vendange."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendange = models.ForeignKey(VendangeReception, on_delete=models.CASCADE, related_name='lignes')
    cepage = models.ForeignKey('referentiels.Cepage', on_delete=models.PROTECT, related_name='vendange_lignes')
    quantite_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité (kg)")
    # Rangs concernés (optionnel)
    rang_debut = models.PositiveIntegerField(null=True, blank=True, verbose_name="Rang début")
    rang_fin = models.PositiveIntegerField(null=True, blank=True, verbose_name="Rang fin")
    rangs_texte = models.CharField(max_length=100, blank=True, help_text="Ex: 1-5, 10-12")
    # Mesures spécifiques à ce cépage
    degre_potentiel = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    etat_sanitaire = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['cepage__nom']
        verbose_name = "Ligne de vendange"
        verbose_name_plural = "Lignes de vendange"

    def __str__(self):
        rangs = ""
        if self.rang_debut and self.rang_fin:
            rangs = f" (rangs {self.rang_debut}-{self.rang_fin})"
        elif self.rangs_texte:
            rangs = f" ({self.rangs_texte})"
        return f"{self.cepage.nom}: {self.quantite_kg} kg{rangs}"


class LotTechnique(models.Model):
    STATUT_CHOICES = (
        # Compat héritée
        ("en_cours", "En cours"),
        ("stabilise", "Stabilisé"),
        ("pret_mise", "Prêt mise"),
        ("conditionne_partiel", "Conditionné partiel"),
        ("epuise", "Épuisé"),
        # Machine d'états étendue (viticole)
        ("MOUT_ENCUVE", "Moût encuvé"),
        ("MOUT_PRESSE", "Moût de presse"),
        ("MOUT_DEBOURBE", "Moût débourbé"),
        ("VIN_EN_FA", "Vin en FA"),
        ("VIN_POST_FA", "Vin post-FA"),
        ("VIN_EN_FML", "Vin en FML"),
        ("VIN_POST_FML", "Vin post-FML"),
        ("VIN_ELEVAGE", "Vin en élevage"),
        ("VIN_STABILISE", "Vin stabilisé"),
        ("VIN_FILTRATION_STERILE", "Vin filtré stérile"),
        ("VIN_PRET_MISE", "Vin prêt mise"),
        # Effervescents
        ("BASE_EFF", "Base effervescente"),
        ("SUR_LATTES", "Sur lattes (tirage)"),
        ("DEGORGEMENT", "Dégorgement/Dosage"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    nom = models.CharField(max_length=200, blank=True)
    campagne = models.CharField(max_length=9)
    contenant = models.CharField(max_length=64, blank=True)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Volume de référence à 20°C (hL)
    volume_v20_hl = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    # Nouveau champ canonique: volume normalisé hL @ 20°C (SYSTEM)
    volume_hl20 = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    # Localisation (SITE/EXTERNE/TRANSIT) – utilisé pour badges OFFSITE et règles d'opérations
    LOCATION_CHOICES = (
        ("ONSITE", "Sur site"),
        ("OFFSITE", "Hors site"),
        ("IN_TRANSIT", "En transit"),
    )
    location_kind = models.CharField(max_length=16, choices=LOCATION_CHOICES, default="ONSITE")
    statut = models.CharField(max_length=32, choices=STATUT_CHOICES, default="en_cours")
    cuvee = models.ForeignKey('referentiels.Cuvee', on_delete=models.PROTECT, null=True, blank=True, related_name='lots_techniques')
    source = models.ForeignKey(VendangeReception, on_delete=models.SET_NULL, null=True, blank=True, related_name="lots_crees")
    # Composition & analyses (MVP JSON)
    composition_json = models.JSONField(default=dict, blank=True)
    analytics_json = models.JSONField(default=dict, blank=True)
    # Pont futur vers un lot externe (ex: viticulture.Lot) sans dépendance forte
    external_lot_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Pont vers lot externe")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["cuvee", "statut", "campagne"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.volume_l} L)"

    @property
    def organization(self):
        try:
            return self.cuvee.organization if self.cuvee_id else None
        except Exception:
            return None

    def volume_net_calculated(self):
        """Somme algébrique des mouvements pour référence serveur.
        ENTREE_INITIALE/ASSEMBLAGE_IN/TRANSFERT_IN = +
        PERTE/SOUTIRAGE/ASSEMBLAGE_OUT/TRANSFERT_OUT/MISE_OUT = -
        """
        total = 0
        try:
            from decimal import Decimal
            total = Decimal('0')
            for mv in self.mouvements.order_by('date', 'id').only('type', 'volume_l'):
                if mv.type in ('ENTREE_INITIALE', 'ASSEMBLAGE_IN', 'TRANSFERT_IN'):
                    total += mv.volume_l
                elif mv.type in ('PERTE', 'SOUTIRAGE', 'ASSEMBLAGE_OUT', 'TRANSFERT_OUT', 'MISE_OUT'):
                    total -= mv.volume_l
        except Exception:
            try:
                return self.volume_l
            except Exception:
                return 0
        return total

    # Transitions simples et extensibles (MVP)
    LOT_STATUS_TRANSITIONS = {
        'MOUT_ENCUVE': {'VIN_EN_FA', 'MOUT_PRESSE', 'MOUT_DEBOURBE'},
        'MOUT_PRESSE': {'VIN_EN_FA'},
        'MOUT_DEBOURBE': {'VIN_EN_FA'},
        'VIN_EN_FA': {'VIN_POST_FA'},
        'VIN_POST_FA': {'VIN_EN_FML', 'VIN_ELEVAGE'},
        'VIN_EN_FML': {'VIN_POST_FML'},
        'VIN_POST_FML': {'VIN_ELEVAGE', 'VIN_STABILISE'},
        'VIN_ELEVAGE': {'VIN_STABILISE', 'VIN_FILTRATION_STERILE', 'VIN_PRET_MISE'},
        'VIN_STABILISE': {'VIN_FILTRATION_STERILE', 'VIN_PRET_MISE'},
        'VIN_FILTRATION_STERILE': {'VIN_PRET_MISE'},
        'VIN_PRET_MISE': set(),
        'BASE_EFF': {'SUR_LATTES'},
        'SUR_LATTES': {'DEGORGEMENT'},
        'DEGORGEMENT': {'VIN_PRET_MISE'},
        # Compat: laisser passer transitions vers anciens codes
        'en_cours': {'stabilise', 'pret_mise'},
        'stabilise': {'pret_mise'},
    }

    def can_transition(self, target: str) -> bool:
        try:
            cur = getattr(self, 'statut')
            return target == cur or target in (self.LOT_STATUS_TRANSITIONS.get(cur) or set())
        except Exception:
            return True

    def transition_to(self, target: str, save: bool = True) -> None:
        if not self.can_transition(target):
            raise ValueError(f"Transition de statut invalide: {self.statut} → {target}")
        self.statut = target
        if save:
            self.save(update_fields=['statut'])


class Assemblage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    nom = models.CharField(max_length=200, blank=True)
    date = models.DateField(default=timezone.now)
    campagne = models.CharField(max_length=9)
    notes = models.TextField(blank=True)
    result_lot = models.ForeignKey('LotTechnique', on_delete=models.PROTECT, null=True, blank=True, related_name='assemblages_result')
    TENANT_ORG_LOOKUPS = (
        'result_lot__cuvee__organization',
        'result_lot__source__organization',
    )
    objects = TenantManager()

    class Meta:
        ordering = ("-date",)

    def __str__(self) -> str:
        return self.code


class AssemblageLigne(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assemblage = models.ForeignKey(Assemblage, on_delete=models.CASCADE, related_name="lignes")
    lot_source = models.ForeignKey(LotTechnique, on_delete=models.PROTECT, related_name="utilisations_assemblage")
    volume_l = models.DecimalField(max_digits=12, decimal_places=2)
    TENANT_ORG_LOOKUPS = (
        'lot_source__cuvee__organization',
        'lot_source__source__organization',
    )
    objects = TenantManager()

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.lot_source.code} → {self.volume_l} L"


# Mouvements par lot technique (journal volumétrique)
class MouvementLot(models.Model):
    TYPE_CHOICES = (
        ("ENTREE_INITIALE", "Entrée initiale"),
        ("SOUTIRAGE", "Soutirage"),
        ("ASSEMBLAGE_IN", "Assemblage (entrée)"),
        ("ASSEMBLAGE_OUT", "Assemblage (sortie)"),
        ("TRANSFERT_IN", "Transfert (entrée)"),
        ("TRANSFERT_OUT", "Transfert (sortie)"),
        ("PERTE", "Perte"),
        ("MISE_OUT", "Mise (sortie)"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(LotTechnique, on_delete=models.CASCADE, related_name="mouvements")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateTimeField(default=timezone.now)
    volume_l = models.DecimalField(max_digits=12, decimal_places=2)
    meta = models.JSONField(default=dict, blank=True)
    TENANT_ORG_LOOKUPS = (
        'lot__cuvee__organization',
        'lot__source__organization',
    )
    objects = TenantManager()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date", "-id")
        indexes = [
            models.Index(fields=["lot", "date", "type"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} {self.volume_l} L"

# Helpers

def next_sequence(prefix: str) -> int:
    """Obtenir un numéro séquentiel naïf basé sur le prefix dans LotTechnique.code ou Assemblage.code."""
    Model = LotTechnique if prefix.startswith("LT-") else Assemblage
    latest = Model.objects.filter(code__startswith=prefix).order_by("-code").first()
    if not latest:
        return 1
    try:
        return int(latest.code.split("-")[-1]) + 1
    except Exception:
        return 1


def generate_lot_tech_code(campagne: str) -> str:
    seq = next_sequence(f"LT-{campagne}-")
    return f"LT-{campagne}-{seq:03d}"


def generate_assemblage_code(campagne: str) -> str:
    seq = next_sequence(f"A-{campagne}-")
    return f"A-{campagne}-{seq:03d}"


def next_vendange_sequence(year: int) -> int:
    """Obtenir un numéro séquentiel pour VND-YYYY-### dans VendangeReception.code.
    Scan tous les codes existants pour trouver le max numérique fiable.
    Utilise _base_manager pour éviter les filtres tenant et voir tous les codes.
    """
    prefix = f"VND-{year}-"
    # Utiliser _base_manager pour bypasser le TenantManager et voir TOUS les codes
    existing_codes = VendangeReception._base_manager.filter(code__startswith=prefix).values_list('code', flat=True)
    
    max_seq = 0
    for code in existing_codes:
        if not code: continue
        try:
            # Extraction suffixe
            parts = code.split('-')
            # VND-YYYY-XXX -> suffixe est le dernier
            suffix = parts[-1]
            if suffix.isdigit():
                seq = int(suffix)
                if seq > max_seq:
                    max_seq = seq
        except Exception:
            continue
            
    return max_seq + 1


def generate_vendange_code(year: int) -> str:
    seq = next_vendange_sequence(year)
    return f"VND-{year}-{seq:03d}"

# ==========================
# Opérations & Filiation (MVP)
# ==========================

class Operation(models.Model):
    KIND_CHOICES = [
        ('encuvage', 'Encuvage'),
        ('pressurage', 'Pressurage/Décuvage'),
        ('assemblage', 'Assemblage'),
        ('fa', 'Fermentation alcoolique'),
        ('fml', 'Fermentation malolactique'),
        ('stabilisation', 'Stabilisation/Collage'),
        ('filtration_sterile', 'Filtration stérile'),
        ('tirage', 'Tirage (effervescents)'),
        ('degorgement', 'Dégorgement/Dosage'),
        ('mise', 'Mise'),
        ('vrac_charge', 'Chargement vrac'),
        ('transfert', 'Transfert interne'),
        ('offsite_send', 'Envoi hors site'),
        ('offsite_return_neutral', 'Retour hors site (neutre)'),
        ('offsite_return_non_neutral', 'Retour hors site (non neutre)'),
        ('analyse', 'Analyse'),
        ('autre', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    date = models.DateTimeField(default=timezone.now)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-date', '-id')
        indexes = [
            models.Index(fields=['organization', 'kind', 'date']),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} – {self.date:%Y-%m-%d}"


class LotLineage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='lineages')
    parent_lot = models.ForeignKey(LotTechnique, null=True, blank=True, on_delete=models.SET_NULL, related_name='children_links')
    child_lot = models.ForeignKey(LotTechnique, on_delete=models.CASCADE, related_name='parent_links')
    ratio = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True, help_text='Part du parent dans l’enfant (0..1)')

    class Meta:
        indexes = [
            models.Index(fields=['operation']),
            models.Index(fields=['parent_lot']),
            models.Index(fields=['child_lot']),
        ]
        verbose_name = 'Filiation de lot'
        verbose_name_plural = 'Filiations de lots'

    def __str__(self) -> str:
        try:
            return f"{self.parent_lot and self.parent_lot.code or '—'} → {self.child_lot.code}"
        except Exception:
            return str(self.id)

# ==========================
# Compta matière & main d'œuvre (générique)
# ==========================

User = get_user_model()


class CostEntry(models.Model):
    """Journal des coûts matière/MO pour entités de production.
    entity_type: 'lottech' | 'mise' | 'tirage' | 'ms_stock'
    nature: 'vrac_in' | 'vrac_out' | 'vrac_loss' | 'ms_in' | 'ms_out' | 'mo' | 'overhead'
    """

    ENTITY_CHOICES = [
        ("lottech", "Lot technique"),
        ("mise", "Mise (OF)"),
        ("tirage", "Tirage / Lot commercial"),
        ("ms_stock", "Stock matières sèches"),
    ]

    NATURE_CHOICES = [
        ("vrac_in", "Entrée vrac"),
        ("vrac_out", "Sortie vrac"),
        ("vrac_loss", "Perte vrac"),
        ("ms_in", "Entrée MS"),
        ("ms_out", "Consommation MS"),
        ("mo", "Main d'œuvre"),
        ("overhead", "Frais généraux"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    entity_type = models.CharField(max_length=20, choices=ENTITY_CHOICES)
    entity_id = models.UUIDField(help_text="UUID de l'entité de référence")
    nature = models.CharField(max_length=20, choices=NATURE_CHOICES)
    qty = models.DecimalField(max_digits=14, decimal_places=4, help_text="Quantité (L ou unité MS)")
    amount_eur = models.DecimalField(max_digits=14, decimal_places=4, help_text="Montant en EUR")
    meta = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    objects = TenantManager()

    class Meta:
        verbose_name = "Écriture de coût"
        verbose_name_plural = "Écritures de coûts"
        ordering = ("-date", "-id")
        indexes = [
            models.Index(fields=["organization", "entity_type", "entity_id", "date"]),
            models.Index(fields=["organization", "nature", "date"]),
        ]


class CostSnapshot(models.Model):
    """Snapshot synthétique de coûts par entité.
    Pour lottech: cmp_vrac_eur_l.
    Pour tirage: cout_unitaire_eur_u (+ détails pack/MO).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=20, choices=CostEntry.ENTITY_CHOICES)
    entity_id = models.UUIDField()
    cmp_vrac_eur_l = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    cmp_pack_eur_u = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    mo_eur_u = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    cout_unitaire_eur_u = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TenantManager()

    class Meta:
        verbose_name = "Snapshot de coût"
        verbose_name_plural = "Snapshots de coûts"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "entity_type", "entity_id"],
                name="unique_cost_snapshot_per_entity",
            )
        ]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]
