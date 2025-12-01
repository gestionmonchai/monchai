# Generated manually to bootstrap initial schema
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Parcelle',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('nom', models.CharField(max_length=200)),
                ('cepage', models.CharField(max_length=120, blank=True)),
                ('surface_ha', models.DecimalField(max_digits=6, decimal_places=2, default=0)),
            ],
            options={'ordering': ('nom',)},
        ),
        migrations.CreateModel(
            name='VendangeReception',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('poids_kg', models.DecimalField(max_digits=10, decimal_places=2)),
                ('degre_potentiel', models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('campagne', models.CharField(max_length=9, help_text='AAAA-AAAA', blank=True)),
                ('auto_create_lot', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parcelle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='production.parcelle', related_name='vendanges')),
            ],
            options={'ordering': ('-date', '-created_at')},
        ),
        migrations.CreateModel(
            name='LotTechnique',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('code', models.CharField(max_length=32, unique=True)),
                ('campagne', models.CharField(max_length=9)),
                ('contenant', models.CharField(max_length=64, blank=True)),
                ('volume_l', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('statut', models.CharField(max_length=16, choices=[('draft', 'Brouillon'), ('available', 'Disponible'), ('consumed', 'Consommé')], default='available')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='production.vendangereception', related_name='lots_crees')),
            ],
            options={'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='Assemblage',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('code', models.CharField(max_length=32, unique=True)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('campagne', models.CharField(max_length=9)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ('-date',)},
        ),
        migrations.CreateModel(
            name='AssemblageLigne',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('volume_l', models.DecimalField(max_digits=12, decimal_places=2)),
                ('assemblage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.assemblage', related_name='lignes')),
                ('lot_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='production.lottechnique', related_name='utilisations_assemblage')),
            ],
            options={'ordering': ('id',)},
        ),
    ]
