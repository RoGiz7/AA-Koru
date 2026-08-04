from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0023_moonfuelsnapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='moontaxconfig',
            name='period_desde',
            field=models.CharField(default='2026-07', help_text='Primer período que se cobra (YYYY-MM). El minado anterior NO genera deuda: aplicar las tasas de hoy a minado viejo produce cifras sin sentido. Arranca en 2026-07 porque la fractura #190 se repartio entre julio y agosto.', max_length=7),
        ),
    ]
