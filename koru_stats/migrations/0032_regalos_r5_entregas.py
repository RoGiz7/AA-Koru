from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0031_premio_type_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="GiftDelivery",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("estado", models.CharField(
                    choices=[("asignado", "Pendiente de enviar"),
                             ("detectado", "Contrato puesto"),
                             ("aceptado", "Contrato aceptado"),
                             ("cerrado", "Cerrado"),
                             ("a_mano", "Entregado a mano")],
                    db_index=True, default="asignado", max_length=12)),
                ("contract_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("contract_para", models.BigIntegerField(
                    blank=True, null=True,
                    help_text="A que personaje se puso el contrato: puede ser un alt del ganador")),
                ("emparejado_por", models.CharField(
                    blank=True, default="", max_length=16,
                    help_text="titulo | descarte | manual")),
                ("detectado_en", models.DateTimeField(blank=True, null=True)),
                ("aceptado_en", models.DateTimeField(blank=True, null=True)),
                ("cerrado_en", models.DateTimeField(blank=True, null=True)),
                ("nota", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("draw", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="delivery", to="koru_stats.raffledraw")),
                ("por_usuario", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Regalos — entrega",
                "verbose_name_plural": "Regalos — entregas",
                "ordering": ["draw"],
            },
        ),
    ]
