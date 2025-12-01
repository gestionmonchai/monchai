from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0002_catalog_core'),
    ]

    operations = [
        migrations.AddField(
            model_name='miseligne',
            name='volume_l',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
