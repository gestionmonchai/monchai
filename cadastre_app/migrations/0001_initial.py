from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='UserParcel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.CharField(blank=True, db_index=True, default='', max_length=64))
                ,('user_id', models.CharField(db_index=True, max_length=64)),
                ('parcelle_id', models.CharField(db_index=True, max_length=20)),
                ('insee', models.CharField(db_index=True, max_length=5)),
                ('section', models.CharField(max_length=3)),
                ('numero', models.CharField(max_length=4)),
                ('label', models.CharField(blank=True, default='', max_length=160)),
                ('harvested_pct', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('geojson', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('tenant_id', 'user_id', 'parcelle_id')},
            },
        )
    ]
