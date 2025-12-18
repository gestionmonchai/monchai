"""
Modèle Analyse œnologique pour les lots en élevage.
Représente un compte-rendu de laboratoire complet avec workflow et alertes.
"""

from __future__ import annotations
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

from apps.accounts.models import Organization
from apps.core.tenancy import TenantManager


class Analyse(models.Model):
    """
    Analyse œnologique complète sur un lot en élevage.
    Regroupe plusieurs paramètres analytiques, un statut de workflow,
    et un système d'alertes métier.
    """

    # === TYPES & CHOIX ===
    TYPE_ANALYSE_CHOICES = [
        ('complete', 'Analyse complète'),
        ('so2', 'Contrôle SO₂'),
        ('pre_mise', 'Pré-mise'),
        ('microbiologique', 'Analyse microbiologique'),
        ('autre', 'Autre'),
    ]

    ORIGINE_CHOICES = [
        ('interne', 'Labo interne'),
        ('externe', 'Labo externe'),
    ]

    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('prelevement', 'Prélèvement effectué'),
        ('attente_resultats', 'En attente résultats'),
        ('resultats_saisis', 'Résultats saisis'),
        ('validee', 'Validée'),
    ]

    NIVEAU_ALERTE_CHOICES = [
        ('ok', 'OK'),
        ('surveillance', 'À surveiller'),
        ('alerte', 'Alerte'),
    ]

    ALERTE_TYPE_CHOICES = [
        ('so2_bas', 'SO₂ libre bas'),
        ('volatile_elevee', 'Acidité volatile élevée'),
        ('ph_eleve', 'pH élevé'),
        ('ph_bas', 'pH bas'),
        ('suspicion_microbio', 'Suspicion microbiologique'),
        ('autre', 'Autre'),
    ]

    # === IDENTIFICATION ===
    # id auto-généré par Django (BigAutoField)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='analyses'
    )
    lot = models.ForeignKey(
        'production.LotTechnique',
        on_delete=models.CASCADE,
        related_name='analyses',
        verbose_name="Lot en élevage"
    )
    
    # === CONTEXTE ===
    date = models.DateField(
        default=timezone.now,
        verbose_name="Date d'analyse"
    )
    type_analyse = models.CharField(
        max_length=20,
        choices=TYPE_ANALYSE_CHOICES,
        default='complete',
        verbose_name="Type d'analyse"
    )
    origine = models.CharField(
        max_length=10,
        choices=ORIGINE_CHOICES,
        default='interne',
        verbose_name="Origine des résultats"
    )
    labo_externe_nom = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom du laboratoire externe"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='resultats_saisis',
        verbose_name="Statut"
    )

    # === STRUCTURE & ACIDITÉ ===
    densite = models.DecimalField(
        max_digits=6, decimal_places=4,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.900')), MaxValueValidator(Decimal('1.200'))],
        verbose_name="Densité à 20°C"
    )
    tav = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('20'))],
        verbose_name="TAV (% vol)"
    )
    sucres_residuels = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Sucres résiduels (g/L)"
    )
    ph = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('2.0')), MaxValueValidator(Decimal('5.0'))],
        verbose_name="pH"
    )
    acidite_totale = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Acidité totale (g/L H₂SO₄)"
    )
    acidite_volatile = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Acidité volatile (g/L H₂SO₄)"
    )
    acide_malique = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Acide malique (g/L)"
    )
    acide_lactique = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Acide lactique (g/L)"
    )

    # === SO₂ & OXYDATION ===
    so2_libre = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="SO₂ libre (mg/L)"
    )
    so2_total = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="SO₂ total (mg/L)"
    )
    potentiel_redox = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        verbose_name="Potentiel redox (mV)"
    )
    so2_commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire SO₂"
    )

    # === AUTRES PARAMÈTRES ===
    azote_assimilable = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Azote assimilable (mg/L)"
    )
    turbidite = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Turbidité (NTU)"
    )
    couleur_do420 = models.DecimalField(
        max_digits=5, decimal_places=3,
        null=True, blank=True,
        verbose_name="DO 420nm"
    )
    couleur_do520 = models.DecimalField(
        max_digits=5, decimal_places=3,
        null=True, blank=True,
        verbose_name="DO 520nm"
    )
    couleur_do620 = models.DecimalField(
        max_digits=5, decimal_places=3,
        null=True, blank=True,
        verbose_name="DO 620nm"
    )
    ipt = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="IPT (Indice Polyphénols)"
    )
    parametres_extra = models.JSONField(
        default=dict, blank=True,
        verbose_name="Paramètres supplémentaires"
    )

    # === APPRÉCIATION INTERNE ===
    note_globale = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note globale (1-5)"
    )
    notes_degustation = models.TextField(
        blank=True,
        verbose_name="Notes de dégustation"
    )
    commentaires_internes = models.TextField(
        blank=True,
        verbose_name="Commentaires internes"
    )

    # === ALERTES ===
    alerte_declenchee = models.BooleanField(
        default=False,
        verbose_name="Alerte déclenchée manuellement"
    )
    alerte_type = models.CharField(
        max_length=20,
        choices=ALERTE_TYPE_CHOICES,
        blank=True,
        verbose_name="Type d'alerte"
    )
    alerte_description = models.TextField(
        blank=True,
        verbose_name="Description de l'alerte"
    )
    alerte_recommandation = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Recommandation de suivi"
    )
    prochaine_analyse_date = models.DateField(
        null=True, blank=True,
        verbose_name="Date prochaine analyse recommandée"
    )
    niveau_alerte = models.CharField(
        max_length=15,
        choices=NIVEAU_ALERTE_CHOICES,
        default='ok',
        verbose_name="Niveau d'alerte"
    )

    # === MÉTADONNÉES ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tenant management
    TENANT_ORG_LOOKUPS = (
        'organization',
        'lot__cuvee__organization',
    )
    objects = TenantManager()

    class Meta:
        verbose_name = "Analyse œnologique"
        verbose_name_plural = "Analyses œnologiques"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['lot', 'date']),
            models.Index(fields=['niveau_alerte']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Analyse {self.get_type_analyse_display()} - {self.lot.code} - {self.date}"

    def save(self, *args, **kwargs):
        # Calculer le niveau d'alerte avant sauvegarde
        self.niveau_alerte = self.calculer_niveau_alerte()
        # Hériter l'organisation du lot si non définie
        if not self.organization_id and self.lot_id:
            try:
                self.organization = self.lot.cuvee.organization
            except Exception:
                pass
        super().save(*args, **kwargs)

    def calculer_niveau_alerte(self) -> str:
        """
        Calcule le niveau d'alerte basé sur les seuils automatiques
        et l'alerte manuelle.
        
        LOGIQUE:
        - L'alerte manuelle (checkbox) prévaut toujours → 'alerte'
        - Les seuils automatiques ne s'appliquent que si une valeur
          est réellement saisie (non nulle et significative)
        - SO₂ libre : alerte si < 15 mg/L, surveillance si < 20 mg/L
          (seulement si une valeur > 0 est saisie, car 0 n'est pas réaliste)
        - Acidité volatile : alerte si > 0.7, surveillance si > 0.5
        - pH : alerte si < 2.9 ou > 3.8, surveillance si < 3.1 ou > 3.6
        """
        # L'alerte manuelle prévaut
        if self.alerte_declenchee:
            return 'alerte'

        niveau = 'ok'

        # Vérification SO₂ libre
        # Note: on ne déclenche que si SO₂ > 0 (une valeur de 0 n'est pas une vraie mesure)
        if self.so2_libre is not None and self.so2_libre > 0:
            if self.so2_libre < 15:
                self.alerte_type = self.alerte_type or 'so2_bas'
                return 'alerte'
            elif self.so2_libre < 20:
                niveau = 'surveillance'

        # Vérification acidité volatile
        if self.acidite_volatile is not None and self.acidite_volatile > Decimal('0'):
            if self.acidite_volatile > Decimal('0.7'):
                self.alerte_type = self.alerte_type or 'volatile_elevee'
                return 'alerte'
            elif self.acidite_volatile > Decimal('0.5'):
                niveau = 'surveillance'

        # Vérification pH
        if self.ph is not None and self.ph > Decimal('0'):
            if self.ph > Decimal('3.8'):
                self.alerte_type = self.alerte_type or 'ph_eleve'
                return 'alerte'
            elif self.ph < Decimal('2.9'):
                self.alerte_type = self.alerte_type or 'ph_bas'
                return 'alerte'
            elif self.ph > Decimal('3.6') or self.ph < Decimal('3.1'):
                niveau = 'surveillance'

        return niveau

    @property
    def resume_resultats(self) -> str:
        """Retourne un résumé des valeurs clés pour l'affichage en liste."""
        parts = []
        if self.ph is not None:
            parts.append(f"pH {self.ph}")
        if self.so2_libre is not None:
            parts.append(f"SO₂L {self.so2_libre}")
        if self.acidite_volatile is not None:
            parts.append(f"AV {self.acidite_volatile}")
        if self.tav is not None:
            parts.append(f"TAV {self.tav}%")
        return " • ".join(parts[:4]) if parts else "—"

    @property
    def contenant_display(self) -> str:
        """Retourne le code du contenant du lot si disponible."""
        try:
            return self.lot.contenant or "—"
        except Exception:
            return "—"

    @property
    def cuvee_nom(self) -> str:
        """Retourne le nom de la cuvée du lot."""
        try:
            return self.lot.cuvee.nom if self.lot.cuvee else "—"
        except Exception:
            return "—"
