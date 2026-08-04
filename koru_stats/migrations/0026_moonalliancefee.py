from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0025_moontaxcontract_acceptor'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoonAllianceFee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('structure_id', models.BigIntegerField(blank=True, db_index=True, help_text='Vacio = tarifa por defecto para todas las lunas', null=True)),
                ('structure_name', models.CharField(blank=True, default='', max_length=150)),
                ('isk_por_fractura', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('valid_from', models.DateField(help_text='Desde cuando aplica. Las fracturas anteriores usan la tarifa vigente entonces.')),
                ('notes', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Luna — tarifa de alianza',
                'verbose_name_plural': 'Luna — tarifas de alianza',
                'ordering': ['-valid_from', 'structure_name'],
                'constraints': [models.UniqueConstraint(fields=('structure_id', 'valid_from'), name='uniq_moon_fee_desde')],
            },
        ),
    ]
