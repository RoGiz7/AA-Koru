# Regalos — R3: sorteos (roster congelado, bolsa de premios, resultados).
# Generada y verificada con makemigrations --check antes de subirla.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0027_regalos_r1'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RaffleRosterFilter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('spec', models.JSONField(default=dict)),
                ('notes', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Regalos — filtro de roster',
                'verbose_name_plural': 'Regalos — filtros de roster',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Raffle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('tipo', models.CharField(choices=[('comunitario', 'Comunitario'), ('especial', 'Especial del CEO')], db_index=True, default='comunitario', max_length=20)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('cerrado', 'Cerrado (semilla publicada)'), ('sorteado', 'Sorteado'), ('anulado', 'Anulado')], db_index=True, default='borrador', max_length=20)),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden en el que se celebran')),
                ('ponderar_por_rango', models.BooleanField(default=True, help_text='Mas aportacion = mas papeletas. Desactivado: una por cabeza')),
                ('excluir_propio_regalo', models.BooleanField(default=True, help_text='Que no te toque lo que tu aportaste (solo aplica a los comunitarios)')),
                ('permitir_repetir_ganador', models.BooleanField(default=False, help_text='Si una persona puede llevarse mas de un premio del mismo sorteo')),
                ('semilla', models.CharField(blank=True, default='', help_text='En claro solo despues de sortear', max_length=64)),
                ('semilla_hash', models.CharField(blank=True, default='', help_text='SHA-256 de la semilla, publicado AL CERRAR', max_length=64)),
                ('cerrado_en', models.DateTimeField(blank=True, null=True)),
                ('sorteado_en', models.DateTimeField(blank=True, null=True)),
                ('anulado_en', models.DateTimeField(blank=True, null=True)),
                ('motivo_anulacion', models.CharField(blank=True, default='', max_length=250)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('anulado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='raffles_anulados', to=settings.AUTH_USER_MODEL)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='raffles', to='koru_stats.giftcampaign')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='raffles_creados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Regalos — sorteo',
                'verbose_name_plural': 'Regalos — sorteos',
                'ordering': ['campaign', 'orden', 'id'],
            },
        ),
        migrations.CreateModel(
            name='RaffleEntrant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main_char_id', models.BigIntegerField(db_index=True)),
                ('main_name', models.CharField(blank=True, default='', max_length=100)),
                ('origen', models.CharField(choices=[('filtro', 'Por filtro'), ('manual', 'A mano (méritos)')], default='filtro', max_length=10)),
                ('motivo', models.CharField(blank=True, default='', help_text='Obligatorio si entra a mano: por que esta aqui', max_length=200)),
                ('papeletas', models.PositiveIntegerField(default=1)),
                ('rango_nombre', models.CharField(blank=True, default='', help_text='Rango congelado al fijar el roster', max_length=60)),
                ('valor_aportado', models.DecimalField(decimal_places=2, default=0, max_digits=22)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('anadido_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='raffle_entrants_anadidos', to=settings.AUTH_USER_MODEL)),
                ('raffle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entrants', to='koru_stats.raffle')),
            ],
            options={
                'verbose_name': 'Regalos — participante',
                'verbose_name_plural': 'Regalos — participantes',
                'ordering': ['main_name'],
            },
        ),
        migrations.CreateModel(
            name='RafflePrize',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origen', models.CharField(choices=[('aportacion', 'De una aportación'), ('exclusivo', 'Exclusivo (del CEO)')], default='aportacion', max_length=15)),
                ('descripcion', models.CharField(blank=True, default='', max_length=200)),
                ('valor', models.DecimalField(blank=True, decimal_places=2, help_text='Opcional en los exclusivos: enseñarlo invita a comparar', max_digits=22, null=True)),
                ('donante_name', models.CharField(blank=True, default='', max_length=100)),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden en que se sortea')),
                ('contribution', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prize', to='koru_stats.giftcontribution')),
                ('raffle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prizes', to='koru_stats.raffle')),
            ],
            options={
                'verbose_name': 'Regalos — premio',
                'verbose_name_plural': 'Regalos — premios',
                'ordering': ['raffle', 'orden', 'id'],
            },
        ),
        migrations.CreateModel(
            name='RaffleDraw',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveIntegerField(default=0)),
                ('hash_usado', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('raffle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='draws', to='koru_stats.raffle')),
                ('entrant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='draws', to='koru_stats.raffleentrant')),
                ('prize', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='draw', to='koru_stats.raffleprize')),
            ],
            options={
                'verbose_name': 'Regalos — resultado de sorteo',
                'verbose_name_plural': 'Regalos — resultados de sorteo',
                'ordering': ['raffle', 'orden'],
            },
        ),
        migrations.AddConstraint(
            model_name='raffle',
            constraint=models.UniqueConstraint(fields=('campaign', 'nombre'), name='uniq_raffle_nombre'),
        ),
        migrations.AddConstraint(
            model_name='raffleentrant',
            constraint=models.UniqueConstraint(fields=('raffle', 'main_char_id'), name='uniq_raffle_entrant'),
        ),
    ]
