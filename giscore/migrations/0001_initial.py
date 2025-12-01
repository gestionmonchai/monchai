from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Parcelle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.CharField(db_index=True, max_length=64)),
                ('name', models.CharField(max_length=120)),
                ('geojson', models.JSONField()),
                ('area_m2', models.FloatField(blank=True, null=True)),
                ('perimeter_m', models.FloatField(blank=True, null=True)),
                ('lod1', models.JSONField(blank=True, null=True)),
                ('lod2', models.JSONField(blank=True, null=True)),
                ('lod3', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-id']},
        ),
        migrations.AddIndex(
            model_name='parcelle',
            index=models.Index(fields=['tenant_id'], name='giscore_par_tenant__idx'),
        ),
    ]
