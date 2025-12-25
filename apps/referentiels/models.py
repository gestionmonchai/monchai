"""
Modèles pour les référentiels viticoles
Roadmap Cut #3 : Référentiels (starter pack)
"""

from django.db import models
from django.db.models import Sum
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
import unicodedata

from apps.accounts.models import Organization
from apps.core.tenancy import TenantManager


def normalize_cepage_name(name):
    """Normalise un nom de cépage pour recherche tolérante"""
    if not name:
        return ""
    # Supprimer accents et convertir en minuscules
    normalized = unicodedata.normalize('NFD', name.lower())
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Supprimer espaces multiples et caractères spéciaux
    normalized = ' '.join(normalized.split())
    return normalized


class CepageReference(models.Model):
    """
    Référentiel officiel des cépages (non lié à une organisation)
    Données préchargées avec tous les cépages français et internationaux
    """
    COULEUR_CHOICES = [
        ('rouge', 'Rouge'),
        ('blanc', 'Blanc'),
        ('rose', 'Rosé'),
        ('gris', 'Gris'),
        ('autre', 'Autre'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom du cépage", unique=True)
    name_norm = models.CharField(max_length=100, db_index=True, unique=True, verbose_name="Nom normalisé")
    synonymes = models.JSONField(default=list, blank=True, verbose_name="Synonymes")
    couleur = models.CharField(max_length=10, choices=COULEUR_CHOICES, default='rouge', verbose_name="Couleur")
    
    # Régions viticoles où ce cépage est cultivé
    regions = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name="Régions viticoles",
        help_text="Liste des régions: bordeaux, bourgogne, alsace, champagne, loire, rhone, provence, languedoc, sud_ouest, jura, savoie, corse, beaujolais"
    )
    pays = models.CharField(max_length=50, default='France', verbose_name="Pays d'origine")
    description = models.TextField(blank=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Cépage (Référentiel)"
        verbose_name_plural = "Cépages (Référentiel)"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_couleur_display()})"
    
    def save(self, *args, **kwargs):
        self.name_norm = normalize_cepage_name(self.nom)
        super().save(*args, **kwargs)


class Cepage(models.Model):
    """
    Référentiel des cépages
    Roadmap item 14: /ref/cepages – CRUD simple (nom, code)
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cepages')
    nom = models.CharField(max_length=100, verbose_name="Nom du cépage")
    name_norm = models.CharField(max_length=100, db_index=True, verbose_name="Nom normalisé")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    row_version = models.PositiveIntegerField(default=1, verbose_name="Version")
    code = models.CharField(max_length=10, blank=True, verbose_name="Code (optionnel)")
    couleur = models.CharField(
        max_length=20,
        choices=[
            ('rouge', 'Rouge'),
            ('blanc', 'Blanc'),
            ('rose', 'Rosé'),
            ('gris', 'Gris'),
            ('autre', 'Autre'),
        ],
        default='rouge',
        verbose_name="Couleur"
    )
    couleur_libre = models.CharField(
        max_length=50, blank=True,
        verbose_name="Couleur (saisie libre)",
        help_text="Utilisé si couleur = 'Autre'"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Lien vers le référentiel officiel (optionnel)
    reference = models.ForeignKey(
        CepageReference, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='instances',
        verbose_name="Cépage de référence"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TenantManager()

    class Meta:
        verbose_name = "Cépage"
        verbose_name_plural = "Cépages"
        indexes = [models.Index(fields=['organization', 'name_norm'])]
        ordering = ['nom']
        constraints = [
            models.UniqueConstraint(fields=['organization', 'name_norm'], name='unique_cepage_name_per_org'),
            # Unicité du code seulement si non vide
            models.UniqueConstraint(
                fields=['organization', 'code'],
                name='unique_cepage_code_per_org',
                condition=models.Q(code__gt='')
            ),
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_couleur_display()})"

    def get_absolute_url(self):
        return reverse('referentiels:cepage_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """Normalisation automatique du nom"""
        self.name_norm = self.normalize_name(self.nom)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_name(name):
        """Normalise un nom pour recherche tolérante"""
        if not name:
            return ""
        # Supprimer accents et convertir en minuscules
        normalized = unicodedata.normalize('NFD', name.lower())
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        # Supprimer espaces multiples et caractères spéciaux
        normalized = ' '.join(normalized.split())
        return normalized

    def can_delete(self):
        """Vérifie si le cépage peut être supprimé (pas de références)"""
        return not self.cuvees.exists()


class Parcelle(models.Model):
    """
    Référentiel des parcelles
    Roadmap item 15: /ref/parcelles – CRUD minimal (nom, surface)
    
    Les certifications (BIO, HVE, etc.) sont stockées dans le champ 'tags' 
    sous forme de liste JSON. Ex: ["BIO", "HVE"]
    """
    # Certifications disponibles pour les parcelles
    CERTIFICATION_CHOICES = [
        ('BIO', 'Agriculture Biologique'),
        ('HVE', 'Haute Valeur Environnementale'),
        ('TERRA_VITIS', 'Terra Vitis'),
        ('BIODYNAMIE', 'Biodynamie (Demeter/Biodyvin)'),
        ('NATURE_PROGRES', 'Nature & Progrès'),
        ('RSE', 'RSE/Développement Durable'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='parcelles')
    nom = models.CharField(max_length=100, verbose_name="Nom de la parcelle")
    surface = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Surface (hectares)"
    )
    lieu_dit = models.CharField(max_length=200, blank=True, verbose_name="Lieu-dit")
    commune = models.CharField(max_length=100, blank=True, verbose_name="Commune")
    appellation = models.CharField(max_length=100, blank=True, verbose_name="Appellation")
    notes = models.TextField(blank=True, verbose_name="Notes")
    conseils = models.TextField(blank=True, verbose_name="Conseils")
    # Géométrie (facultative)
    geojson = models.JSONField(blank=True, null=True, verbose_name="Géométrie GeoJSON")
    # Zones de rangs dessinées sur la carte (GeoJSON FeatureCollection)
    zones_geojson = models.JSONField(blank=True, null=True, verbose_name="Zones de rangs")
    area_m2 = models.FloatField(null=True, blank=True)
    perimeter_m = models.FloatField(null=True, blank=True)
    # BBOX/centroid pour filtres rapides (Lite, sans PostGIS)
    minx = models.FloatField(null=True, blank=True, db_index=True)
    miny = models.FloatField(null=True, blank=True, db_index=True)
    maxx = models.FloatField(null=True, blank=True, db_index=True)
    maxy = models.FloatField(null=True, blank=True, db_index=True)
    centroid_x = models.FloatField(null=True, blank=True, db_index=True)
    centroid_y = models.FloatField(null=True, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitude")
    tags = models.JSONField(default=list, blank=True, verbose_name="Tags")
    cepages = models.ManyToManyField(Cepage, blank=True, verbose_name="Cépages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TenantManager()

    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
        unique_together = ['organization', 'nom']
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.surface} ha)"

    def get_absolute_url(self):
        return reverse('referentiels:parcelle_detail', kwargs={'pk': self.pk})

    @property
    def quantite_recoltee_kg(self) -> Decimal:
        agg = self.vendanges.aggregate(s=Sum('poids_kg'))
        val = agg.get('s') or Decimal('0')
        try:
            return Decimal(val)
        except Exception:
            return Decimal('0')

    @property
    def certifications(self) -> list:
        """
        Retourne la liste des certifications de la parcelle.
        Les certifications sont stockées dans le champ 'tags' avec des codes prédéfinis:
        BIO, HVE, TERRA_VITIS, BIODYNAMIE, NATURE_PROGRES, RSE
        """
        if not self.tags or not isinstance(self.tags, list):
            return []
        valid_codes = [code for code, label in self.CERTIFICATION_CHOICES]
        return [tag for tag in self.tags if tag in valid_codes]
    
    def add_certification(self, code: str):
        """Ajoute une certification à la parcelle"""
        valid_codes = [c[0] for c in self.CERTIFICATION_CHOICES]
        if code not in valid_codes:
            raise ValueError(f"Certification '{code}' non reconnue. Valeurs possibles: {valid_codes}")
        if not isinstance(self.tags, list):
            self.tags = []
        if code not in self.tags:
            self.tags.append(code)
            
    def remove_certification(self, code: str):
        """Retire une certification de la parcelle"""
        if isinstance(self.tags, list) and code in self.tags:
            self.tags.remove(code)
    
    def get_encepagement_total_percent(self):
        """Retourne le pourcentage total d'encépagement défini"""
        return self.encepagements.aggregate(total=Sum('pourcentage'))['total'] or Decimal('0')
    
    def get_surface_plantee(self):
        """Retourne la surface plantée en ha (selon encépagement)"""
        total_pct = self.get_encepagement_total_percent()
        if total_pct > 0:
            return (self.surface * total_pct / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0')
    
    def get_encepagement_blocks(self):
        """Retourne une liste de blocs d'encépagement prêts pour affichage."""
        blocs = []
        surface = getattr(self, 'surface', None)
        for enc in self.encepagements.select_related('cepage').all():
            pct = enc.pourcentage
            surface_bloc = None
            try:
                if surface and pct:
                    surface_bloc = (surface * pct / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except (InvalidOperation, TypeError):
                surface_bloc = None
            if enc.rang_debut and enc.rang_fin:
                meta = f"Rangs {enc.rang_debut}-{enc.rang_fin}"
            elif enc.rang_debut:
                meta = f"Rang {enc.rang_debut}+"
            elif enc.annee_plantation:
                meta = f"Planté en {enc.annee_plantation}"
            else:
                meta = None
            blocs.append({
                'cepage': enc.cepage.nom if enc.cepage else '',
                'pct': pct,
                'annee': enc.annee_plantation,
                'surface': surface_bloc,
                'meta': meta,
            })
        return blocs
    
    def get_encepagement_preview_json(self):
        """Retourne un JSON (str) prêt à être injecté côté client pour l'encépagement."""
        blocs = []
        for bloc in self.get_encepagement_blocks():
            blocs.append({
                'cepage': bloc.get('cepage', ''),
                'pct': float(bloc['pct']) if bloc.get('pct') is not None else None,
                'annee': bloc.get('annee'),
                'surface': float(bloc['surface']) if bloc.get('surface') is not None else None,
                'meta': bloc.get('meta'),
            })
        return json.dumps(blocs, ensure_ascii=False)


class ParcelleEncepagement(models.Model):
    """
    Encépagement d'une parcelle - représente un bloc/zone de cépages
    Permet de définir la composition en cépages avec rangs et pourcentages
    """
    parcelle = models.ForeignKey(
        Parcelle, 
        on_delete=models.CASCADE, 
        related_name='encepagements',
        verbose_name="Parcelle"
    )
    cepage = models.ForeignKey(
        Cepage, 
        on_delete=models.CASCADE, 
        related_name='encepagements',
        verbose_name="Cépage"
    )
    pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100'))],
        verbose_name="Pourcentage (%)"
    )
    rang_debut = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="Rang de début"
    )
    rang_fin = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="Rang de fin"
    )
    annee_plantation = models.PositiveIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        verbose_name="Année de plantation"
    )
    porte_greffe = models.CharField(
        max_length=100, blank=True,
        verbose_name="Porte-greffe"
    )
    densite_pieds_ha = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="Densité (pieds/ha)"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Encépagement"
        verbose_name_plural = "Encépagements"
        ordering = ['rang_debut', '-pourcentage']
    
    def __str__(self):
        rangs = ""
        if self.rang_debut and self.rang_fin:
            rangs = f" (rangs {self.rang_debut}-{self.rang_fin})"
        elif self.rang_debut:
            rangs = f" (rang {self.rang_debut}+)"
        return f"{self.cepage.nom} - {self.pourcentage}%{rangs}"
    
    @property
    def surface_ha(self):
        """Surface en hectares pour ce bloc"""
        return (self.parcelle.surface * self.pourcentage / Decimal('100')).quantize(Decimal('0.01'))
    
    @property
    def age_vignes(self):
        """Âge des vignes en années"""
        if self.annee_plantation:
            from datetime import date
            return date.today().year - self.annee_plantation
        return None


class Unite(models.Model):
    """
    Référentiel des unités de mesure
    Roadmap item 16: /ref/unites – Liste unités (bouteille, hl, L)
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='unites')
    nom = models.CharField(max_length=50, verbose_name="Nom de l'unité")
    symbole = models.CharField(max_length=10, verbose_name="Symbole")
    type_unite = models.CharField(
        max_length=20,
        choices=[
            ('volume', 'Volume'),
            ('poids', 'Poids'),
            ('surface', 'Surface'),
            ('quantite', 'Quantité'),
        ],
        default='volume',
        verbose_name="Type d'unité"
    )
    facteur_conversion = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0,
        help_text="Facteur de conversion vers l'unité de base (ex: 1 bouteille = 0.75 L)",
        verbose_name="Facteur de conversion"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unité"
        verbose_name_plural = "Unités"
        unique_together = ['organization', 'nom']
        ordering = ['type_unite', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.symbole})"

    def get_absolute_url(self):
        return reverse('referentiels:unite_detail', kwargs={'pk': self.pk})


class Cuvee(models.Model):
    """
    Référentiel des cuvées
    Roadmap item 17: /ref/cuvees – CRUD (nom, couleur, AOC/IGP)
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cuvees')
    nom = models.CharField(max_length=100, verbose_name="Nom de la cuvée")
    couleur = models.CharField(
        max_length=15,
        choices=[
            ('rouge', 'Rouge'),
            ('blanc', 'Blanc'),
            ('rose', 'Rosé'),
            ('effervescent', 'Effervescent'),
        ],
        verbose_name="Couleur"
    )
    classification = models.CharField(
        max_length=20,
        choices=[
            ('aoc', 'AOC'),
            ('igp', 'IGP'),
            ('vsig', 'VSIG'),
            ('vdf', 'Vin de France'),
        ],
        verbose_name="Classification"
    )
    appellation = models.CharField(max_length=100, blank=True, verbose_name="Appellation")
    degre_alcool = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Degré d'alcool (%)"
    )
    cepages = models.ManyToManyField(Cepage, blank=True, verbose_name="Cépages")
    description = models.TextField(blank=True, verbose_name="Description")
    notes_degustation = models.TextField(blank=True, verbose_name="Notes de dégustation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cuvée"
        verbose_name_plural = "Cuvées"
        unique_together = ['organization', 'nom']
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_couleur_display()})"

    def get_absolute_url(self):
        return reverse('referentiels:cuvee_detail', kwargs={'pk': self.pk})


class Entrepot(models.Model):
    """
    Référentiel des entrepôts
    Roadmap item 18: /ref/entrepots – CRUD (chai, dépôt, boutique)
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='entrepots')
    nom = models.CharField(max_length=100, verbose_name="Nom de l'entrepôt")
    type_entrepot = models.CharField(
        max_length=20,
        choices=[
            ('chai', 'Chai'),
            ('depot', 'Dépôt'),
            ('boutique', 'Boutique'),
            ('cave', 'Cave'),
            ('autre', 'Autre'),
        ],
        verbose_name="Type d'entrepôt"
    )
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    capacite = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Capacité en nombre de bouteilles",
        verbose_name="Capacité"
    )
    temperature_min = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Température min (°C)"
    )
    temperature_max = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Température max (°C)"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        unique_together = ['organization', 'nom']
        ordering = ['type_entrepot', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_entrepot_display()})"

    def get_absolute_url(self):
        return reverse('referentiels:entrepot_detail', kwargs={'pk': self.pk})


class ImportBatch(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='import_batches')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    file = models.FileField(upload_to='imports/quarantine/')
    status = models.CharField(max_length=20, default='quarantine')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ImportExecution(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='import_executions')
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name='executions')
    undo_token = models.CharField(max_length=64, unique=True)
    created_objects = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
