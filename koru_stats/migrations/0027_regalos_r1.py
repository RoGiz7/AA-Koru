# Regalos de la fiesta — R1: aportaciones, valoracion y rangos.
# Generada y verificada antes de subirla; vive en el repo a proposito
# (ver la 0020, que existia solo en la BD y reventaba cada reinstalacion).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0026_moonalliancefee'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftCampaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, unique=True)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('abierta', 'Abierta'), ('cerrada', 'Cerrada')], db_index=True, default='borrador', max_length=20)),
                ('ventana_desde', models.DateTimeField(help_text='Las aportaciones anteriores a esta fecha no se detectan')),
                ('ventana_hasta', models.DateTimeField(help_text='Ni las posteriores')),
                ('fecha_evento', models.DateField(blank=True, help_text='El dia de la fiesta', null=True)),
                ('precio_modo', models.CharField(choices=[('jita_sell', 'Jita sell (lo que costaria comprarlo)'), ('jita_buy', 'Jita buy (lo que te darian por el)')], default='jita_sell', max_length=20)),
                ('usar_percentil', models.BooleanField(default=True, help_text='Usar el percentil 5% en vez del minimo pelado')),
                ('spread_max_pct', models.DecimalField(decimal_places=2, default=60.0, help_text='Spread buy/sell por encima del cual se marca para valorar a mano', max_digits=6)),
                ('desviacion_max_pct', models.DecimalField(decimal_places=2, default=200.0, help_text='Desviacion frente a average_price por encima de la cual se marca', max_digits=6)),
                ('notes', models.CharField(blank=True, default='', max_length=250)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Regalos — campaña',
                'verbose_name_plural': 'Regalos — campañas',
                'ordering': ['-ventana_desde'],
            },
        ),
        migrations.AlterModelOptions(
            name='general',
            options={'default_permissions': (), 'managed': False, 'permissions': (('basic_access', 'Puede ver Estadísticas y Mi Dashboard'), ('corp_finance_access', 'Puede ver Finanzas Corp'), ('moon_tax_access', 'Puede ver Tax Lunas'), ('moon_tax_admin', 'Puede gestionar tax de lunas'), ('pvp_access', 'Puede ver estadísticas PvP detalladas'), ('fc_access', 'Puede ver panel FC/Director'), ('auditor_access', 'Puede ver el panel Auditor (seguridad)'), ('auditor_admin', 'Puede configurar el Auditor y revisar/descartar alertas'), ('auditor_corp_health', 'Puede ver el panel de Salud de Corp (Directores/CEO)'), ('tickets_reclutamiento', 'Tickets: ve Reclutamiento'), ('tickets_directores', 'Tickets: ve A Directores'), ('tickets_asuntos_internos', 'Tickets: ve Asuntos Internos'), ('tickets_it', 'Tickets: ve IT y Soporte'), ('tickets_admin', 'Tickets: ve todos los tipos'), ('gift_access', 'Regalos: ve lo suyo (Mi aportación)'), ('gift_manage', 'Regalos: gestiona aportaciones, sorteos y entregas'), ('gift_ceo', 'Regalos: monta los sorteos especiales del CEO'))},
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_buy_max',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Mejor orden de compra en Jita: lo que te darian por el', max_digits=22, null=True),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_consultado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_fuente',
            field=models.CharField(blank=True, default='', help_text='fuzzwork / esi', max_length=30),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_ordenes',
            field=models.IntegerField(blank=True, help_text='Numero de ordenes de venta detras del precio', null=True),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_percentil',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Percentil 5% de venta. Se usa en vez del minimo pelado: una sola orden troll de 1 ISK no debe decidir un rango', max_digits=22, null=True),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_sell_min',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Orden de venta mas barata en Jita: lo que costaria comprarlo', max_digits=22, null=True),
        ),
        migrations.AddField(
            model_name='korumarketprice',
            name='jita_volumen',
            field=models.BigIntegerField(blank=True, help_text='Unidades a la venta. Si es menor que lo regalado, el precio no aguanta', null=True),
        ),
        migrations.CreateModel(
            name='GiftContribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origen', models.CharField(choices=[('contrato', 'Contrato de ítems'), ('isk', 'Donación de ISK')], db_index=True, max_length=15)),
                ('fuente_key', models.CharField(db_index=True, help_text='"c:<contract_id>" para contratos, "w:<entry_id>" para donaciones', max_length=40)),
                ('donante_id', models.BigIntegerField(db_index=True, help_text='Personaje que aporto (puede ser un alt)')),
                ('donante_name', models.CharField(blank=True, default='', max_length=100)),
                ('main_char_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('main_name', models.CharField(blank=True, default='', max_length=100)),
                ('contract_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('assignee_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('acceptor_id', models.BigIntegerField(blank=True, null=True)),
                ('acceptor_name', models.CharField(blank=True, default='', max_length=100)),
                ('contract_type', models.CharField(blank=True, default='', max_length=20)),
                ('esi_status', models.CharField(blank=True, default='', max_length=25)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('reward', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('start_location_id', models.BigIntegerField(blank=True, null=True)),
                ('start_location_name', models.CharField(blank=True, default='', max_length=150)),
                ('entry_id', models.BigIntegerField(blank=True, db_index=True, help_text='entry_id del journal: clave para no contar dos veces', null=True)),
                ('wallet_division', models.IntegerField(blank=True, null=True)),
                ('reason', models.CharField(blank=True, default='', help_text='Lo que escribio el donante. Se enseña, no filtra: medio mundo lo deja vacio', max_length=500)),
                ('fecha', models.DateTimeField(blank=True, db_index=True, help_text='date_issued o date del journal', null=True)),
                ('valor_estimado', models.DecimalField(decimal_places=2, default=0, max_digits=22)),
                ('valor_ajustado', models.DecimalField(blank=True, decimal_places=2, max_digits=22, null=True)),
                ('valor_fuente', models.CharField(blank=True, default='', help_text='jita_sell / jita_buy / percentil / isk / manual', max_length=40)),
                ('valor_consultado_en', models.DateTimeField(blank=True, help_text='Cuando se pregunto el precio. NO se recalcula: el precio justo es el del momento en que se aporto', null=True)),
                ('estado', models.CharField(choices=[('detectada', 'Detectada'), ('validada', 'Validada'), ('revisar', 'Revisar'), ('descartada', 'Descartada')], db_index=True, default='detectada', max_length=20)),
                ('requiere_valoracion', models.BooleanField(default=False, help_text='Algo no cuadra con el precio de mercado')),
                ('ubicacion_rara', models.BooleanField(default=False)),
                ('cobra_isk', models.BooleanField(default=False, help_text='price o reward distintos de cero')),
                ('sin_main', models.BooleanField(default=False, help_text='El donante no resuelve a ningun main')),
                ('aviso', models.CharField(blank=True, default='', max_length=250)),
                ('validado_en', models.DateTimeField(blank=True, null=True)),
                ('nota', models.TextField(blank=True, default='', help_text='Por que se ajusto el valor o se valido asi')),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributions', to='koru_stats.giftcampaign')),
                ('validado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gift_contributions_validadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Regalos — aportación',
                'verbose_name_plural': 'Regalos — aportaciones',
                'ordering': ['-fecha'],
            },
        ),
        migrations.CreateModel(
            name='GiftContributionItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_id', models.BigIntegerField(db_index=True)),
                ('type_name', models.CharField(blank=True, default='', max_length=150)),
                ('quantity', models.BigIntegerField(default=0)),
                ('group_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('category_id', models.IntegerField(blank=True, db_index=True, help_text='9 = Blueprints', null=True)),
                ('es_bpc', models.BooleanField(default=False, help_text='raw_quantity negativo = copia de blueprint')),
                ('precio_unitario', models.DecimalField(blank=True, decimal_places=2, max_digits=22, null=True)),
                ('valor_linea', models.DecimalField(decimal_places=2, default=0, max_digits=22)),
                ('precio_fuente', models.CharField(blank=True, default='', max_length=40)),
                ('requiere_valoracion', models.BooleanField(default=False)),
                ('motivo', models.CharField(blank=True, default='', help_text='sin_ordenes / volumen_corto / spread / desviacion / bpc / categoria', max_length=150)),
                ('contribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='koru_stats.giftcontribution')),
            ],
            options={
                'verbose_name': 'Regalos — ítem aportado',
                'verbose_name_plural': 'Regalos — ítems aportados',
                'ordering': ['-valor_linea'],
            },
        ),
        migrations.CreateModel(
            name='GiftRecipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_id', models.BigIntegerField(db_index=True, help_text='ID de la corp o personaje que recibe')),
                ('entity_name', models.CharField(blank=True, default='', max_length=100)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('acepta_contratos', models.BooleanField(default=True)),
                ('acepta_isk', models.BooleanField(default=True)),
                ('wallet_division', models.IntegerField(blank=True, help_text='Division de la cartera de corp donde cuentan las donaciones. Vacio = cualquiera', null=True)),
                ('expected_location_id', models.BigIntegerField(blank=True, help_text='Donde se espera el contrato. Vacio = no se comprueba', null=True)),
                ('expected_location_name', models.CharField(blank=True, default='', max_length=150)),
                ('notes', models.CharField(blank=True, default='', max_length=200)),
                ('campaign', models.ForeignKey(blank=True, help_text='Vacio = vale para todas las campañas', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipients', to='koru_stats.giftcampaign')),
            ],
            options={
                'verbose_name': 'Regalos — destinatario válido',
                'verbose_name_plural': 'Regalos — destinatarios válidos',
                'ordering': ['entity_name'],
            },
        ),
        migrations.CreateModel(
            name='GiftTier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=60)),
                ('umbral_min', models.DecimalField(decimal_places=2, default=0, help_text='Valor minimo aportado (ISK) para entrar en este rango', max_digits=22)),
                ('papeletas', models.PositiveIntegerField(default=1)),
                ('orden', models.PositiveIntegerField(default=0, help_text='De menor a mayor')),
                ('color', models.CharField(blank=True, default='', help_text='Clase o hex para la UI', max_length=20)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tiers', to='koru_stats.giftcampaign')),
            ],
            options={
                'verbose_name': 'Regalos — rango',
                'verbose_name_plural': 'Regalos — rangos',
                'ordering': ['campaign', 'orden'],
            },
        ),
        migrations.AddIndex(
            model_name='giftcontribution',
            index=models.Index(fields=['campaign', 'main_char_id'], name='koru_gift_camp_main'),
        ),
        migrations.AddIndex(
            model_name='giftcontribution',
            index=models.Index(fields=['campaign', 'estado'], name='koru_gift_camp_estado'),
        ),
        migrations.AddConstraint(
            model_name='giftcontribution',
            constraint=models.UniqueConstraint(fields=('campaign', 'fuente_key'), name='uniq_gift_fuente'),
        ),
        migrations.AddConstraint(
            model_name='giftcontributionitem',
            constraint=models.UniqueConstraint(fields=('contribution', 'type_id'), name='uniq_gift_item'),
        ),
        migrations.AddConstraint(
            model_name='giftrecipient',
            constraint=models.UniqueConstraint(fields=('campaign', 'entity_id'), name='uniq_gift_recipient'),
        ),
        migrations.AddConstraint(
            model_name='gifttier',
            constraint=models.UniqueConstraint(fields=('campaign', 'orden'), name='uniq_gift_tier_orden'),
        ),
        migrations.AddConstraint(
            model_name='gifttier',
            constraint=models.UniqueConstraint(fields=('campaign', 'nombre'), name='uniq_gift_tier_nombre'),
        ),
    ]
