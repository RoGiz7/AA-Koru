"""
Notas reservadas a Asuntos Internos y Dirección.

⚠ Todo lo ya escrito se queda como «todo el staff»: es lo que era cuando se
escribió. Convertirlo en reservado a posteriori ocultaría notas que su autor
puso a la vista de todos.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0040_recruit_grupos")]

    operations = [
        migrations.AddField(
            model_name="recruitnote",
            name="visibilidad",
            field=models.CharField(
                choices=[("staff", "Todo el staff de reclutamiento"),
                         ("reservada", "Solo Asuntos Internos y Dirección")],
                db_index=True, default="staff", max_length=10),
        ),
    ]
