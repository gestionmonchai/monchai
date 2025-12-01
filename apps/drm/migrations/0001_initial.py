# Generated manually for DRM initial schema
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DRMLine',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('type', models.CharField(max_length=16, choices=[('entree', 'Entrée'), ('mise', 'Mise'), ('sortie', 'Sortie'), ('perte', 'Perte'), ('vrac', 'Vrac')])),
                ('volume_l', models.DecimalField(max_digits=12, decimal_places=2)),
                ('ref_kind', models.CharField(max_length=32)),
                ('ref_id', models.UUIDField(null=True, blank=True)),
                ('campagne', models.CharField(max_length=9)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ('-date', '-created_at')},
        ),
    ]
