"""
Las preguntas del formulario, editables desde el admin.

Crea la tabla y la siembra con las seis preguntas acordadas. A partir de aquí
manda el admin: tocar `PREGUNTAS_INICIALES` en el código ya no cambia nada de
lo que haya en producción.
"""

from django.db import migrations, models


SEMILLA = [
    # (clave, etiqueta, tipo, obligatoria, ayuda, opciones)
    ("conociste", "¿Dónde nos conociste?", "texto", True,
     "Un amigo, in-game, YouTube, un anuncio…", []),
    ("pais", "¿De qué país eres?", "texto", True,
     "Para saber a qué hora sueles coincidir con las flotas", []),
    ("actividades", "¿Qué te gusta hacer en EVE?", "larga", True,
     "PvP, minería, industria, exploración… lo que de verdad disfrutes", []),
    ("horario", "¿Cuándo sueles jugar?", "texto", True,
     "Por ejemplo: entre semana de 20 a 23, fines de semana por la tarde", []),
    ("estuviste", "¿Ya estuviste en Rekium antes?", "opcion", True, "",
     ["No", "Sí, en Rekium", "Sí, en la Academia", "No estoy seguro"]),
    ("motivo", "¿Por qué quieres entrar en Rekium?", "larga", True,
     "Tómate un momento: esto es lo que más leerá el reclutador", []),
]


def sembrar(apps, schema_editor):
    Pregunta = apps.get_model("koru_stats", "RecruitQuestion")
    for i, (clave, etiqueta, tipo, oblig, ayuda, opciones) in enumerate(SEMILLA, start=10):
        # get_or_create y no create: si la migración se reaplica en otro entorno
        # no debe duplicar ni reventar por la clave única.
        Pregunta.objects.get_or_create(
            clave=clave,
            defaults=dict(etiqueta=etiqueta, tipo=tipo, obligatoria=oblig,
                          ayuda=ayuda, opciones=opciones, orden=i, activa=True),
        )


def quitar(apps, schema_editor):
    Pregunta = apps.get_model("koru_stats", "RecruitQuestion")
    Pregunta.objects.filter(clave__in=[s[0] for s in SEMILLA]).delete()


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0037_reclutamiento")]

    operations = [
        migrations.CreateModel(
            name="RecruitQuestion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("clave", models.SlugField(
                    max_length=40, unique=True,
                    help_text="Identificador interno. No lo cambies si ya hay respuestas")),
                ("etiqueta", models.CharField(
                    max_length=200, help_text="La pregunta tal como la lee el piloto")),
                ("ayuda", models.CharField(
                    blank=True, default="", max_length=250,
                    help_text="Texto pequeño debajo. Opcional")),
                ("tipo", models.CharField(
                    choices=[("texto", "Una línea"), ("larga", "Varias líneas"),
                             ("opcion", "Elegir de una lista")],
                    default="texto", max_length=10)),
                ("opciones", models.JSONField(
                    blank=True, default=list,
                    help_text='Solo para "Elegir de una lista". Ej: ["Sí", "No"]')),
                ("obligatoria", models.BooleanField(default=True)),
                ("orden", models.IntegerField(default=0, help_text="De menor a mayor")),
                ("activa", models.BooleanField(
                    default=True,
                    help_text="Desactívala en vez de borrarla: las fichas antiguas la siguen necesitando")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Reclutamiento — pregunta",
                "verbose_name_plural": "Reclutamiento — preguntas del formulario",
                "ordering": ["orden", "id"],
            },
        ),
        migrations.RunPython(sembrar, quitar),
    ]
