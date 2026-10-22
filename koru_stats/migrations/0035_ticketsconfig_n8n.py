from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0034_ticket_claim_main_y_cierre"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticketsconfig",
            name="n8n_webhook_url",
            field=models.CharField(
                blank=True, default="", max_length=300,
                help_text="Webhook de n8n que recibe las acciones desde la web (vacío = la web no escribe)"),
        ),
        migrations.AddField(
            model_name="ticketsconfig",
            name="n8n_webhook_secret",
            field=models.CharField(
                blank=True, default="", max_length=200,
                help_text="Se manda en la cabecera X-Koru-Token; el webhook lo comprueba"),
        ),
    ]
