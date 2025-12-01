# Generated manually for initial produits schema
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('viticulture', '0004_lotcontainer_lotdetail_lotdocument_lotintervention_and_more'),
        ('production', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mise',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('code_of', models.CharField(max_length=20, unique=True)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('campagne', models.CharField(max_length=9)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ('-date', '-created_at')},
        ),
        migrations.CreateModel(
            name='LotCommercial',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('code_lot', models.CharField(max_length=64, unique=True)),
                ('format_ml', models.PositiveIntegerField(default=750)),
                ('date_mise', models.DateField()),
                ('quantite_unites', models.PositiveIntegerField(default=0)),
                ('stock_disponible', models.PositiveIntegerField(default=0)),
                ('cuvee', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, to='viticulture.cuvee', related_name='lots_commerciaux')),
                ('mise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='produits.mise', related_name='lots')),
            ],
            options={'ordering': ('-date_mise', '-id')},
        ),
        migrations.CreateModel(
            name='MiseLigne',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('format_ml', models.PositiveIntegerField(default=750)),
                ('quantite_unites', models.PositiveIntegerField(default=0)),
                ('pertes_pct', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('lot_tech_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='production.lottechnique', related_name='utilisations_mise')),
                ('mise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='produits.mise', related_name='lignes')),
            ],
            options={'ordering': ('id',)},
        ),
    ]
