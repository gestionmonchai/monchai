# Migration to clear cuvee references before FK change
from django.db import migrations


def clear_cuvee_references(apps, schema_editor):
    """Clear cuvee references temporarily to allow FK change from viticulture to referentiels"""
    VendangeReception = apps.get_model('production', 'VendangeReception')
    LotTechnique = apps.get_model('production', 'LotTechnique')
    
    # Count for logging
    vendange_count = VendangeReception.objects.exclude(cuvee__isnull=True).count()
    lot_count = LotTechnique.objects.exclude(cuvee__isnull=True).count()
    
    # Clear all cuvee references
    VendangeReception.objects.all().update(cuvee=None)
    LotTechnique.objects.all().update(cuvee=None)
    
    if vendange_count > 0 or lot_count > 0:
        print(f"\nWARNING: Cleared {vendange_count} vendange and {lot_count} lot technique cuvee references")
        print("WARNING: You will need to reassign cuvees manually from the referentiels after migration\n")


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0012_lottechnique_location_kind_lottechnique_volume_hl20_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_cuvee_references, migrations.RunPython.noop),
    ]
