from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0022_moontaxrecipient_expected_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoonFuelSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('structure_id', models.BigIntegerField(db_index=True)),
                ('structure_name', models.CharField(blank=True, default='', max_length=150)),
                ('corporation_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('fecha', models.DateField(db_index=True)),
                ('fuel_type_id', models.IntegerField(blank=True, null=True)),
                ('fuel_type_name', models.CharField(blank=True, default='', max_length=100)),
                ('bloques', models.BigIntegerField(default=0)),
                ('fuel_expires', models.DateTimeField(blank=True, null=True)),
                ('horas_restantes', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('consumo_hora', models.DecimalField(decimal_places=3, default=0, help_text='Bloques/hora derivados', max_digits=10)),
                ('precio_bloque', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('coste_hora', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('coste_dia', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('servicios', models.CharField(blank=True, default='', help_text='Servicios online; explican el consumo', max_length=255)),
                ('state', models.CharField(blank=True, default='', max_length=25)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Luna — foto de combustible',
                'verbose_name_plural': 'Luna — fotos de combustible',
                'ordering': ['-fecha', 'structure_name'],
                'indexes': [models.Index(fields=['fecha', 'structure_id'], name='koru_mfs_fecha_str')],
                'constraints': [models.UniqueConstraint(fields=('structure_id', 'fecha'), name='uniq_moon_fuel_dia')],
            },
        ),
    ]
