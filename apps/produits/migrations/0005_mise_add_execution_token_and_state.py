from django.db import migrations, models
import uuid


def set_exec_tokens(apps, schema_editor):
    Mise = apps.get_model('produits', 'Mise')
    for m in Mise.objects.filter(execution_token__isnull=True):
        m.execution_token = uuid.uuid4()
        try:
            m.save(update_fields=['execution_token'])
        except Exception:
            # If unique collisions ever happen (unlikely), retry once
            m.execution_token = uuid.uuid4()
            m.save(update_fields=['execution_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0004_rename_prod_inv_org_sku_idx_produits_in_organiz_9e83aa_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mise',
            name='execution_token',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='mise',
            name='state',
            field=models.CharField(max_length=16, default='brouillon'),
        ),
        migrations.RunPython(set_exec_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mise',
            name='execution_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
