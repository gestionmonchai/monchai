from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0002_assemblage_result_lot'),
        ('referentiels', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendangereception',
            name='parcelle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vendanges', to='referentiels.parcelle'),
        ),
    ]
