"""
Modèles pour le catalogue et la gestion des lots
Roadmap Cut #4 : Catalogue & lots
"""

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from apps.accounts.models import Organization
from apps.referentiels.models import Cuvee, Entrepot, Unite


class Lot(models.Model):
    """
    Modèle pour les lots de production
    Roadmap items 21, 22, 23: /lots – Liste, création, détail lots
    """
    
    STATUT_CHOICES = [
        ('production', 'En production'),
        ('fermentation', 'En fermentation'),
        ('elevage', 'En élevage'),
        ('assemblage', 'En assemblage'),
        ('conditionnement', 'En conditionnement'),
        ('stock', 'En stock'),
        ('vendu', 'Vendu'),
        ('perdu', 'Perdu/Détruit'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='lots')
    cuvee = models.ForeignKey(Cuvee, on_delete=models.CASCADE, related_name='lots')
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='lots')
    
    # Identification
    numero_lot = models.CharField(max_length=50, verbose_name="Numéro de lot")
    millesime = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        verbose_name="Millésime"
    )
    
    # Volumes et quantités
    volume_initial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Volume initial"
    )
    unite_volume = models.ForeignKey(
        Unite,
        on_delete=models.PROTECT,
        related_name='lots_volume',
        limit_choices_to={'type_unite': 'volume'},
        verbose_name="Unité de volume"
    )
    volume_actuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume actuel"
    )
    
    # Caractéristiques techniques
    degre_alcool = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Degré d'alcool (%)"
    )
    densite = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.8), MaxValueValidator(1.2)],
        verbose_name="Densité"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='production',
        verbose_name="Statut"
    )
    date_creation = models.DateField(verbose_name="Date de création du lot")
    date_fin_prevue = models.DateField(blank=True, null=True, verbose_name="Date de fin prévue")
    
    # Informations complémentaires
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lot"
        verbose_name_plural = "Lots"
        unique_together = ['organization', 'numero_lot', 'millesime']
        ordering = ['-millesime', 'numero_lot']
    
    def __str__(self):
        return f"{self.numero_lot} - {self.cuvee.nom} {self.millesime}"
    
    def get_absolute_url(self):
        return reverse('catalogue:lot_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Initialiser volume_actuel avec volume_initial si nouveau lot
        if not self.pk and not self.volume_actuel:
            self.volume_actuel = self.volume_initial
        super().save(*args, **kwargs)
    
    @property
    def volume_consomme(self):
        """Volume consommé (initial - actuel)"""
        return self.volume_initial - self.volume_actuel
    
    @property
    def pourcentage_restant(self):
        """Pourcentage de volume restant"""
        if self.volume_initial > 0:
            return (self.volume_actuel / self.volume_initial) * 100
        return 0
    
    @property
    def est_epuise(self):
        """True si le lot est épuisé (volume actuel = 0)"""
        return self.volume_actuel <= 0


class MouvementLot(models.Model):
    """
    Modèle pour l'historique des mouvements de lots
    Roadmap item 23: /lots/:id – Détail lot (historique mouvements)
    """
    
    TYPE_MOUVEMENT_CHOICES = [
        ('creation', 'Création du lot'),
        ('transfert_entrepot', 'Transfert d\'entrepôt'),
        ('assemblage', 'Assemblage'),
        ('soutirage', 'Soutirage'),
        ('filtration', 'Filtration'),
        ('conditionnement', 'Conditionnement'),
        ('vente', 'Vente'),
        ('perte', 'Perte/Casse'),
        ('correction', 'Correction manuelle'),
        ('autre', 'Autre'),
    ]
    
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='mouvements')
    
    # Type et description
    type_mouvement = models.CharField(
        max_length=20,
        choices=TYPE_MOUVEMENT_CHOICES,
        verbose_name="Type de mouvement"
    )
    description = models.CharField(max_length=200, verbose_name="Description")
    
    # Volumes
    volume_avant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume avant"
    )
    volume_mouvement = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Volume du mouvement"
    )
    volume_apres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Volume après"
    )
    
    # Entrepôts (pour les transferts)
    entrepot_source = models.ForeignKey(
        Entrepot,
        on_delete=models.PROTECT,
        related_name='mouvements_sortie',
        blank=True,
        null=True,
        verbose_name="Entrepôt source"
    )
    entrepot_destination = models.ForeignKey(
        Entrepot,
        on_delete=models.PROTECT,
        related_name='mouvements_entree',
        blank=True,
        null=True,
        verbose_name="Entrepôt destination"
    )
    
    # Métadonnées
    date_mouvement = models.DateTimeField(verbose_name="Date du mouvement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mouvement de lot"
        verbose_name_plural = "Mouvements de lots"
        ordering = ['-date_mouvement']
    
    def __str__(self):
        return f"{self.lot.numero_lot} - {self.get_type_mouvement_display()} ({self.date_mouvement.strftime('%d/%m/%Y')})"


# --- NOUVEAUX MODÈLES CATALOGUE GÉNÉRIQUE (ARTICLES) ---

class ArticleCategory(models.Model):
    """Catégorie d'articles (Vin, Miel, Oenotourisme...)"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='article_categories')
    name = models.CharField("Nom", max_length=100)
    description = models.TextField("Description", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catégorie d'article"
        verbose_name_plural = "Catégories d'articles"
        ordering = ['name']
        unique_together = ['organization', 'name']

    def __str__(self):
        return self.name


class ArticleTag(models.Model):
    """Tags pour filtrer et organiser les produits"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='article_tags')
    name = models.CharField("Nom", max_length=50)
    
    class Meta:
        verbose_name = "Tag produit"
        verbose_name_plural = "Tags produits"
        ordering = ['name']
        unique_together = ['organization', 'name']

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Concept unique d'Article commercialisable.
    Le 'type' détermine le comportement métier.
    """
    TYPE_PRODUCT = 'product'     # Stock simple (Miel, Verres)
    TYPE_TRACEABLE = 'traceable' # Stock par Batch (Vin)
    TYPE_SERVICE = 'service'     # Non stocké (Prestation)
    TYPE_STAY = 'stay'           # Capacité/Calendrier (Nuitée)
    TYPE_PACK = 'pack'           # Composition (Coffret)
    
    TYPE_CHOICES = [
        (TYPE_PRODUCT, 'Produit stockable'),
        (TYPE_TRACEABLE, 'Produit traçable (Vin/Lot)'),
        (TYPE_SERVICE, 'Service / Prestation'),
        (TYPE_STAY, 'Nuitée / Hébergement'),
        (TYPE_PACK, 'Pack / Bundle'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles', verbose_name="Catégorie")
    tags = models.ManyToManyField(ArticleTag, blank=True, related_name='articles', verbose_name="Tags")
    
    # Identification
    article_type = models.CharField("Type d'article", max_length=20, choices=TYPE_CHOICES, default=TYPE_PRODUCT)
    name = models.CharField("Désignation", max_length=200)
    sku = models.CharField("Code article (SKU)", max_length=50, blank=True, help_text="Référence unique interne")
    description = models.TextField("Description courte", blank=True, help_text="Pour devis/factures")
    
    # Commercial
    price_ht = models.DecimalField("Prix de vente HT", max_digits=10, decimal_places=2, default=0)
    purchase_price = models.DecimalField("Prix d'achat HT", max_digits=10, decimal_places=2, default=0, help_text="Prix d'achat de référence (PA HT)")
    vat_rate = models.DecimalField("Taux de TVA (%)", max_digits=5, decimal_places=2, default=20.0)
    unit = models.CharField("Unité de vente", max_length=20, default="PCE", help_text="PCE, L, KG, NUIT, PERS...")
    
    # Comportement
    is_stock_managed = models.BooleanField("Gestion de stock", default=True, help_text="Si actif, le système suit les quantités.")
    is_buyable = models.BooleanField("Achetable", default=True, help_text="Peut être acheté (Fournisseurs)")
    is_sellable = models.BooleanField("Vendable", default=True, help_text="Peut être vendu (Clients)")
    is_active = models.BooleanField("Actif", default=True)
    
    # Douane & Régie
    hs_code = models.CharField("Code Douanier (HS)", max_length=20, blank=True, help_text="Code nomenclature pour export")
    origin_country = models.CharField("Pays d'origine", max_length=100, blank=True, default="France")
    alcohol_degree = models.DecimalField("Degré d'alcool (%)", max_digits=4, decimal_places=2, null=True, blank=True)
    net_volume = models.DecimalField("Volume net (L)", max_digits=10, decimal_places=4, null=True, blank=True, help_text="Volume en litres pour la régie")
    customs_notes = models.TextField("Notes douanières", blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Médias & Dégustation
    image = models.ImageField("Photo produit", upload_to='products/', blank=True, null=True)
    tasting_notes = models.TextField("Notes de dégustation", blank=True, help_text="Fiche de dégustation, arômes, accords mets-vins...")

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['category', 'name']
        unique_together = ['organization', 'sku'] # SKU unique par org

    def __str__(self):
        return f"[{self.sku}] {self.name}" if self.sku else self.name

    @property
    def price_ttc(self):
        return self.price_ht * (1 + self.vat_rate / 100)


class ArticleStock(models.Model):
    """
    État du stock actuel pour un article à un endroit donné.
    Si article traçable, on sépare par numéro de lot (batch).
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='stocks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='stock_lines')
    location = models.ForeignKey(Entrepot, on_delete=models.PROTECT, related_name='article_stocks', verbose_name="Emplacement")
    
    # Traçabilité optionnelle
    batch_number = models.CharField("Numéro de lot/batch", max_length=50, blank=True, default="", help_text="Vide pour produits non traçables")
    
    # Quantité
    quantity = models.DecimalField("Quantité en stock", max_digits=12, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ligne de stock"
        verbose_name_plural = "Stock"
        unique_together = ['article', 'location', 'batch_number']
        ordering = ['article', 'batch_number']

    def __str__(self):
        if self.batch_number:
            return f"{self.article.name} [{self.batch_number}] : {self.quantity} {self.article.unit}"
        return f"{self.article.name} : {self.quantity} {self.article.unit}"


class StockMovement(models.Model):
    """
    Journal des mouvements de stock (Grand Livre).
    """
    MOVE_IN = 'in'         # Achat, Production
    MOVE_OUT = 'out'       # Vente, Perte, Don
    MOVE_ADJUST = 'adjust' # Inventaire
    
    MOVE_CHOICES = [
        (MOVE_IN, 'Entrée'),
        (MOVE_OUT, 'Sortie'),
        (MOVE_ADJUST, 'Ajustement'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='stock_movements')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='movements')
    location = models.ForeignKey(Entrepot, on_delete=models.PROTECT, related_name='movements', verbose_name="Emplacement")
    
    movement_type = models.CharField("Type", max_length=10, choices=MOVE_CHOICES)
    quantity = models.DecimalField("Quantité", max_digits=12, decimal_places=2, help_text="Positif pour entrée, Négatif pour sortie (géré par logique métier)")
    
    batch_number = models.CharField("Lot/Batch", max_length=50, blank=True, default="")
    
    date = models.DateTimeField("Date", auto_now_add=True) # Ou editable=True si on veut antidater
    reference = models.CharField("Référence", max_length=100, blank=True, help_text="Ex: Facture #123, Prod #456")
    notes = models.TextField("Notes", blank=True)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.article.name}"
