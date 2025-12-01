from django.db import models


class MSFamily(models.TextChoices):
    BOUTEILLE = "bouteille", "Bouteille"
    BOUCHON = "bouchon", "Bouchon"
    CAPSULE = "capsule", "Capsule"
    ETIQUETTE = "etiquette", "Étiquette"
    CARTON = "carton", "Carton"
    AUTRE = "autre", "Autre"


class MSItem(models.Model):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    family = models.CharField(max_length=30, choices=MSFamily.choices)
    uom = models.CharField(max_length=20, default="u")
    pack_qty = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    stock_min = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    cmp_eur_u = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"{self.code} — {self.name}"


class MSEmplacement(models.Model):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return self.name


class MSMoveNature(models.TextChoices):
    MS_IN = "ms_in", "Entrée (achat)"
    TRANSFER_IN = "transfer_in", "Transfert +"
    TRANSFER_OUT = "transfer_out", "Transfert −"
    MS_OUT = "ms_out", "Consommation (mise)"
    ADJUST_POS = "adjust_pos", "Inventaire +"
    ADJUST_NEG = "adjust_neg", "Inventaire −"
    SCRAP_OUT = "scrap_out", "Rebut"


class MSMove(models.Model):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
    item = models.ForeignKey(MSItem, on_delete=models.PROTECT)
    from_location = models.ForeignKey(MSEmplacement, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    to_location = models.ForeignKey(MSEmplacement, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    qty = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price_eur = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    nature = models.CharField(max_length=20, choices=MSMoveNature.choices)
    ref = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MSReservation(models.Model):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
    item = models.ForeignKey(MSItem, on_delete=models.CASCADE)
    mise = models.ForeignKey("produits.Mise", on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=14, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
