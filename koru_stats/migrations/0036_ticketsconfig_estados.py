from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0035_ticketsconfig_n8n"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticketsconfig",
            name="estados_por_tabla",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
