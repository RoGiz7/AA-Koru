from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('koru_stats', '0020_recruitmentlink_socialedge'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoonTaxRecipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_id', models.BigIntegerField(help_text='ID de la corp o personaje que recibe los contratos', unique=True)),
                ('entity_name', models.CharField(blank=True, default='', max_length=100)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('notes', models.CharField(blank=True, default='', max_length=200)),
            ],
            options={
                'verbose_name': 'Tax lunar — destinatario válido',
                'verbose_name_plural': 'Tax lunar — destinatarios válidos',
                'ordering': ['entity_name'],
            },
        ),
        migrations.CreateModel(
            name='MoonTaxContract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_id', models.BigIntegerField(db_index=True, unique=True)),
                ('issuer_id', models.BigIntegerField(db_index=True, help_text='De issuer_name_id; issuer_id viene a 0 siempre')),
                ('issuer_name', models.CharField(blank=True, default='', max_length=100)),
                ('main_char_id', models.BigIntegerField(blank=True, db_index=True, help_text='Main al que se imputa; el emisor puede ser un alt', null=True)),
                ('main_name', models.CharField(blank=True, default='', max_length=100)),
                ('assignee_id', models.BigIntegerField(db_index=True)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('reward', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('contract_type', models.CharField(blank=True, default='', max_length=20)),
                ('esi_status', models.CharField(blank=True, default='', help_text='status de la ESI: outstanding / finished / deleted...', max_length=25)),
                ('start_location_id', models.BigIntegerField(blank=True, null=True)),
                ('start_location_name', models.CharField(blank=True, default='', max_length=150)),
                ('date_issued', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('date_accepted', models.DateTimeField(blank=True, null=True)),
                ('date_completed', models.DateTimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('detectado', 'Detectado'), ('revisar', 'Revisar'), ('descartado', 'Descartado')], db_index=True, default='detectado', max_length=20)),
                ('tiene_bruto', models.BooleanField(default=False, help_text='Trae mineral sin comprimir (no se acepta: transporte inviable)')),
                ('ubicacion_rara', models.BooleanField(default=False, help_text='Entregado fuera de la ubicacion esperada')),
                ('cobra_isk', models.BooleanField(default=False, help_text='price o reward distintos de cero')),
                ('items_ajenos', models.BooleanField(default=False, help_text='Trae cosas que no son mineral lunar')),
                ('aviso', models.CharField(blank=True, default='', max_length=250)),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Tax lunar — contrato',
                'verbose_name_plural': 'Tax lunar — contratos',
                'ordering': ['-date_issued'],
                'indexes': [
                    models.Index(fields=['main_char_id', 'date_issued'], name='koru_mtc_main_fecha'),
                    models.Index(fields=['estado', 'date_issued'], name='koru_mtc_estado_fecha'),
                ],
            },
        ),
        migrations.CreateModel(
            name='MoonTaxContractItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_id', models.BigIntegerField(db_index=True)),
                ('type_name', models.CharField(blank=True, default='', max_length=150)),
                ('quantity', models.BigIntegerField(default=0)),
                ('group_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('is_compressed', models.BooleanField(default=False)),
                ('base_type_id', models.BigIntegerField(blank=True, db_index=True, help_text='Mineral base al que corresponde (comprime 1:1)', null=True)),
                ('base_name', models.CharField(blank=True, default='', max_length=150)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='koru_stats.moontaxcontract')),
            ],
            options={
                'verbose_name': 'Tax lunar — ítem de contrato',
                'verbose_name_plural': 'Tax lunar — ítems de contrato',
                'ordering': ['-quantity'],
                'constraints': [
                    models.UniqueConstraint(fields=('contract', 'type_id'), name='uniq_mtc_item'),
                ],
            },
        ),
        migrations.CreateModel(
            name='MoonTaxLedger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main_char_id', models.BigIntegerField(db_index=True)),
                ('main_name', models.CharField(blank=True, default='', max_length=100)),
                ('period', models.CharField(db_index=True, help_text='YYYY-MM', max_length=7)),
                ('base_type_id', models.BigIntegerField(db_index=True)),
                ('base_name', models.CharField(blank=True, default='', max_length=150)),
                ('group_id', models.IntegerField(blank=True, null=True)),
                ('unidades_minadas', models.BigIntegerField(default=0)),
                ('tasa', models.DecimalField(decimal_places=2, default=0, help_text='% aplicado', max_digits=5)),
                ('debe', models.BigIntegerField(default=0, help_text='Comprimidos adeudados (el mineral lunar comprime 1:1)')),
                ('entregado', models.BigIntegerField(default=0, help_text='Comprimidos detectados en contratos')),
                ('validado', models.BooleanField(db_index=True, default=False)),
                ('validado_at', models.DateTimeField(blank=True, null=True)),
                ('saldo_cerrado', models.BigIntegerField(default=0, help_text='Lo que el director dejo pendiente al validar; es esto lo que arrastra')),
                ('notes', models.TextField(blank=True, default='', help_text='Por que se acepto o no una compensacion entre minerales')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moon_tax_ledger_validado', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tax lunar — saldo',
                'verbose_name_plural': 'Tax lunar — saldos',
                'ordering': ['-period', 'main_name', 'base_name'],
                'constraints': [
                    models.UniqueConstraint(fields=('main_char_id', 'period', 'base_type_id'), name='uniq_mtl_saldo'),
                ],
                'indexes': [
                    models.Index(fields=['period', 'validado'], name='koru_mtl_periodo_val'),
                ],
            },
        ),
    ]
