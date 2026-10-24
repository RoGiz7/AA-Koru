"""
Dónde nacen los canales de reclutamiento y quién los ve.

⚠ Nace APAGADA (`activo=False`) y sin categoría. Hasta que alguien la rellene,
las solicitudes se guardan igual y la pantalla del reclutador las enseña
marcadas como «sin canal». Es mejor eso que crear canales sueltos en la raíz
del Discord porque una migración se inventó una categoría.
"""

from django.db import migrations, models


def crear(apps, schema_editor):
    Config = apps.get_model("koru_stats", "RecruitConfig")
    Config.objects.get_or_create(tag="default")


def quitar(apps, schema_editor):
    Config = apps.get_model("koru_stats", "RecruitConfig")
    Config.objects.filter(tag="default").delete()


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0038_recruit_preguntas")]

    operations = [
        migrations.CreateModel(
            name="RecruitConfig",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("tag", models.CharField(default="default", max_length=20, unique=True)),
                ("activo", models.BooleanField(
                    default=False,
                    help_text="Mientras esté apagado, la solicitud se guarda pero no se crea canal")),
                ("categoria_id", models.CharField(
                    blank=True, default="", max_length=30,
                    help_text="Id de la categoría de Discord donde van los canales de reclutamiento")),
                ("prefijo_canal", models.CharField(
                    default="reclutamiento-", max_length=30,
                    help_text="Delante del nombre del piloto")),
                ("roles_ver", models.JSONField(
                    blank=True, default=list,
                    help_text='Ids de los roles que ven el canal. Ej: ["954100891844231238"]')),
                ("avisar_en", models.CharField(
                    blank=True, default="", max_length=30,
                    help_text="Canal donde avisar de que hay solicitud nueva. Opcional")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Reclutamiento — configuración",
                "verbose_name_plural": "Reclutamiento — configuración",
            },
        ),
        migrations.RunPython(crear, quitar),
    ]
