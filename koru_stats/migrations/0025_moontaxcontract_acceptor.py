from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0024_moontaxconfig_period_desde'),
    ]

    operations = [
        migrations.AddField(
            model_name='moontaxcontract',
            name='acceptor_id',
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='moontaxcontract',
            name='acceptor_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
