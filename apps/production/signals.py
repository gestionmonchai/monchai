from __future__ import annotations
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import VendangeReception, LotTechnique, generate_lot_tech_code
from decimal import Decimal


@receiver(post_save, sender=VendangeReception)
def auto_create_lot_tech_from_vendange(sender, instance: VendangeReception, created: bool, **kwargs):
    if not created:
        return
    if not instance.auto_create_lot:
        return
    # Ne pas dupliquer si déjà créé
    if LotTechnique.objects.filter(source=instance).exists():
        return
    code = generate_lot_tech_code(instance.campagne)
    LotTechnique.objects.create(
        code=code,
        campagne=instance.campagne,
        contenant='Cuve initiale',
        volume_l=(instance.poids_kg / Decimal('1.2')) if instance.poids_kg else Decimal('0'),  # approx rendement litres
        statut='en_cours',
        source=instance,
    )
