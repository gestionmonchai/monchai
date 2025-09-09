from django.db import models
from django.core.validators import MinValueValidator
from monchai.apps.accounts.models import Domaine
from monchai.apps.core.models import BouteilleLot


class Produit(models.Model):
    """Modèle pour les produits (mapping commercial des lots de bouteilles)"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="produits")
    bouteille_lot = models.ForeignKey(BouteilleLot, on_delete=models.PROTECT, related_name="produits")
    nom = models.CharField("Nom", max_length=200)
    sku = models.CharField("SKU", max_length=50)
    prix_ttc_eur = models.DecimalField(
        "Prix TTC (EUR)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    tva_pct = models.DecimalField(
        "TVA (%)",
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        unique_together = [("domaine", "sku")]
    
    def __str__(self):
        return f"{self.nom} ({self.sku})"
    
    @property
    def prix_ht_eur(self):
        """Calcule le prix HT à partir du prix TTC et du taux de TVA"""
        return self.prix_ttc_eur / (1 + (self.tva_pct / 100))


class Client(models.Model):
    """Modèle pour les clients"""
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="clients")
    nom = models.CharField("Nom", max_length=200)
    email = models.EmailField("Email", blank=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    adresse = models.TextField("Adresse", blank=True)
    code_postal = models.CharField("Code postal", max_length=10, blank=True)
    ville = models.CharField("Ville", max_length=100, blank=True)
    pays = models.CharField("Pays", max_length=100, default="France")
    siret = models.CharField("SIRET", max_length=14, blank=True)
    tva_intra = models.CharField("TVA intracommunautaire", max_length=20, blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return self.nom


class Commande(models.Model):
    """Modèle pour les commandes"""
    
    STATUS_CHOICES = [
        ("brouillon", "Brouillon"),
        ("confirmee", "Confirmée"),
        ("expediee", "Expédiée"),
        ("livree", "Livrée"),
        ("annulee", "Annulée")
    ]
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="commandes")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="commandes")
    date = models.DateField("Date de la commande")
    status = models.CharField("Statut", max_length=15, choices=STATUS_CHOICES, default="brouillon")
    commentaire = models.TextField("Commentaire", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
    
    def __str__(self):
        return f"{self.client.nom} - {self.date}"
    
    @property
    def total_ttc_eur(self):
        """Calcule le total TTC de la commande"""
        return sum(ligne.total_ttc_eur for ligne in self.lignes.all())


class LigneCommande(models.Model):
    """Modèle pour les lignes de commande"""
    
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="lignes_commande")
    quantite = models.PositiveIntegerField("Quantité", validators=[MinValueValidator(1)])
    prix_unitaire_ttc_eur = models.DecimalField(
        "Prix unitaire TTC (EUR)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    tva_pct = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=20.00)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
    
    @property
    def total_ttc_eur(self):
        """Calcule le total TTC pour cette ligne"""
        return self.prix_unitaire_ttc_eur * self.quantite
    
    @property
    def prix_unitaire_ht_eur(self):
        """Calcule le prix unitaire HT"""
        return self.prix_unitaire_ttc_eur / (1 + (self.tva_pct / 100))
    
    @property
    def total_ht_eur(self):
        """Calcule le total HT pour cette ligne"""
        return self.prix_unitaire_ht_eur * self.quantite


class Facture(models.Model):
    """Modèle pour les factures"""
    
    STATUS_CHOICES = [
        ("brouillon", "Brouillon"),
        ("emise", "Émise"),
        ("payee", "Payée"),
        ("annulee", "Annulée")
    ]
    
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="factures")
    commande = models.OneToOneField(Commande, on_delete=models.PROTECT, related_name="facture")
    numero = models.CharField("Numéro", max_length=50)
    date_emission = models.DateField("Date d'émission")
    date_echeance = models.DateField("Date d'échéance", null=True, blank=True)
    status = models.CharField("Statut", max_length=10, choices=STATUS_CHOICES, default="brouillon")
    pdf_path = models.CharField("Chemin du PDF", max_length=255, blank=True)
    total_ttc = models.DecimalField("Total TTC", max_digits=10, decimal_places=2)
    tva = models.JSONField("Détails TVA", default=dict)
    commentaire = models.TextField("Commentaire", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        unique_together = [("domaine", "numero")]
    
    def __str__(self):
        return f"Facture {self.numero} - {self.commande.client.nom}"


class Paiement(models.Model):
    """Modèle pour les paiements"""
    
    MODE_CHOICES = [
        ("virement", "Virement"),
        ("cheque", "Chèque"),
        ("carte", "Carte bancaire"),
        ("especes", "Espèces"),
        ("autre", "Autre")
    ]
    
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name="paiements")
    date = models.DateField("Date du paiement")
    montant = models.DecimalField(
        "Montant",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    mode = models.CharField("Mode de paiement", max_length=10, choices=MODE_CHOICES)
    reference = models.CharField("Référence", max_length=100, blank=True)
    commentaire = models.TextField("Commentaire", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
    
    def __str__(self):
        return f"{self.get_mode_display()} - {self.date} - {self.montant} €"
