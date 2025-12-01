# Generated for Roadmap 19 - Cépages CRUD robuste

from django.db import migrations, models
import unicodedata

def normalize_existing_cepages(apps, schema_editor):
    """Normalise les noms des cépages existants"""
    Cepage = apps.get_model('referentiels', 'Cepage')
    
    def normalize_name(name):
        if not name:
            return ""
        normalized = unicodedata.normalize('NFD', name.lower())
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return ' '.join(normalized.split())
    
    for cepage in Cepage.objects.all():
        cepage.name_norm = normalize_name(cepage.nom)
        cepage.is_active = True
        cepage.row_version = 1
        cepage.save(update_fields=['name_norm', 'is_active', 'row_version'])

def reverse_normalize(apps, schema_editor):
    """Rollback - pas d'action nécessaire"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('referentiels', '0002_search_v2_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='cepage',
            name='name_norm',
            field=models.CharField(db_index=True, max_length=100, verbose_name='Nom normalisé', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cepage',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Actif'),
        ),
        migrations.AddField(
            model_name='cepage',
            name='row_version',
            field=models.PositiveIntegerField(default=1, verbose_name='Version'),
        ),
        migrations.RunPython(normalize_existing_cepages, reverse_normalize),
        migrations.AlterUniqueTogether(
            name='cepage',
            unique_together={('organization', 'name_norm'), ('organization', 'code')},
        ),
        migrations.AddIndex(
            model_name='cepage',
            index=models.Index(fields=['organization', 'name_norm'], name='referentiels_cepage_org_name_norm_idx'),
        ),
    ]
