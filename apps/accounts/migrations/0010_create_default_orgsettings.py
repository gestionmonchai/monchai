from django.db import migrations


def create_default_settings(apps, schema_editor):
    """Crée les paramètres par défaut pour les organisations existantes"""
    Organization = apps.get_model('accounts', 'Organization')
    OrgSettings = apps.get_model('accounts', 'OrgSettings')
    
    for org in Organization.objects.all():
        OrgSettings.objects.get_or_create(
            organization=org,
            defaults={
                'currency': 'EUR',
                'date_format': 'DD/MM/YYYY',
                'number_format': 'FR',
            }
        )


def reverse_default_settings(apps, schema_editor):
    """Supprime les paramètres créés"""
    OrgSettings = apps.get_model('accounts', 'OrgSettings')
    OrgSettings.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0009_orgsettings'),
    ]
    
    operations = [
        migrations.RunPython(create_default_settings, reverse_default_settings),
    ]
