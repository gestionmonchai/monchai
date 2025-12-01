# Generated for product catalog core models
from django.db import migrations, models
import django.db.models.deletion
import uuid
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('referentiels', '0001_initial'),
        ('viticulture', '0001_initial'),
        ('produits', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('row_version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type_code', models.CharField(max_length=10, choices=[('wine', 'Vin'), ('food', 'Alimentaire'), ('merch', 'Merch'), ('other', 'Autre')])),
                ('name', models.CharField(max_length=150)),
                ('brand', models.CharField(max_length=100, blank=True)),
                ('slug', models.SlugField(max_length=180, unique=True)),
                ('tax_class', models.CharField(max_length=30, blank=True)),
                ('attrs', models.JSONField(default=dict, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.organization')),
                ('cuvee', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, to='viticulture.cuvee')),
            ],
            options={
                'ordering': ['name'],
                'indexes': [
                    models.Index(fields=['organization', 'type_code', 'is_active'], name='prod_prod_org_type_active_idx'),
                    models.Index(fields=['organization', 'slug'], name='prod_prod_org_slug_idx'),
                ],
                'unique_together': [['organization', 'name']],
            },
        ),
        migrations.CreateModel(
            name='SKU',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('row_version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('pack_of', models.PositiveIntegerField(null=True, blank=True)),
                ('barcode', models.CharField(max_length=64, blank=True)),
                ('internal_ref', models.CharField(max_length=64, blank=True)),
                ('default_price_ht', models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.organization')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skus', to='produits.product')),
                ('unite', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='referentiels.unite')),
            ],
            options={
                'ordering': ['name'],
                'indexes': [
                    models.Index(fields=['organization', 'product', 'is_active'], name='prod_sku_org_prod_active_idx'),
                ],
                'unique_together': [['organization', 'product', 'unite', 'name']],
            },
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('row_version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('qty', models.PositiveIntegerField(default=0)),
                ('warehouse', models.CharField(max_length=100, blank=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.organization')),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='produits.sku')),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [
                    models.Index(fields=['organization', 'sku'], name='prod_inv_org_sku_idx'),
                ],
            },
        ),
    ]
