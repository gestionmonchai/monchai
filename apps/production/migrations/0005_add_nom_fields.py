from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0004_lottechnique_cuvee_lottechnique_external_lot_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendangereception',
            name='nom',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='lottechnique',
            name='nom',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='assemblage',
            name='nom',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
