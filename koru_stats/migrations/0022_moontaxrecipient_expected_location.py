from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0021_moon_tax_contratos'),
    ]

    operations = [
        migrations.AddField(
            model_name='moontaxrecipient',
            name='expected_location_id',
            field=models.BigIntegerField(blank=True, help_text='Ubicacion donde se espera la entrega. Si el contrato viene de otro sitio se marca para revisar. Vacio = no se comprueba.', null=True),
        ),
        migrations.AddField(
            model_name='moontaxrecipient',
            name='expected_location_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]
