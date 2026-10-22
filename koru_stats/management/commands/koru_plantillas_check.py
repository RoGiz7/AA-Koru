"""
Revisa las plantillas del plugin buscando los errores que NO dan error.

Existe por un motivo concreto: el 22/10/2026 se descubrió que dos comentarios
de Django llevaban tiempo imprimiéndose en pantalla —uno en la ficha de un
ticket y otro en el tax lunar de cada piloto, ese desde hacía meses— y nadie lo
había visto. Django no se queja de ninguno de los dos casos que mira esto:

1. **Comentario corto de varias líneas.** `{# … #}` es de UNA sola línea.
   Escrito en dos, Django no lo reconoce como comentario y lo imprime tal cual
   en la página. No falla, no avisa: sale.
2. **Etiquetas de bloque descuadradas.** Un `{% if %}` sin su `{% endif %}`
   revienta al renderizar, pero solo cuando alguien entra en esa pantalla, que
   puede ser semanas después de subirlo.

No sustituye a abrir la página y mirarla. Lo que hace es que estos dos no haya
que buscarlos a ojo.

    python manage.py koru_plantillas_check

Devuelve 1 si encuentra algo, así que sirve para un hook o para CI el día que lo
haya.
"""

import os
import re

from django.core.management.base import BaseCommand

# Los que abren y cierran. `comment` entra a propósito: un `{% comment %}` sin
# cerrar se come el resto de la plantilla EN SILENCIO, que es de los peores.
BLOQUES = ("if", "for", "block", "comment", "with", "spaceless", "autoescape")


class Command(BaseCommand):
    help = "Busca comentarios de Django mal escritos y etiquetas descuadradas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ruta", default=None,
            help="Carpeta a revisar (por defecto, las plantillas del plugin)")

    def handle(self, *args, **opts):
        base = opts["ruta"] or os.path.join(os.path.dirname(__file__),
                                            "..", "..", "templates")
        base = os.path.normpath(base)
        if not os.path.isdir(base):
            self.stderr.write(self.style.ERROR(f"No existe la carpeta: {base}"))
            return

        problemas, revisadas = [], 0
        for raiz, _dirs, ficheros in os.walk(base):
            for f in sorted(ficheros):
                if not f.endswith(".html"):
                    continue
                ruta = os.path.join(raiz, f)
                corta = os.path.relpath(ruta, base)
                revisadas += 1
                with open(ruta, encoding="utf-8") as fh:
                    s = fh.read()

                # 1. {# … #} que se derrama a la siguiente linea
                for m in re.finditer(r"\{#", s):
                    trozo = s[m.start():m.start() + 800]
                    fin, salto = trozo.find("#}"), trozo.find("\n")
                    if fin < 0 or (0 <= salto < fin):
                        linea = s.count("\n", 0, m.start()) + 1
                        problemas.append(
                            (corta, linea,
                             "comentario corto de varias lineas: SE IMPRIME en la pagina. "
                             "Usa {% comment %}"))

                # 2. Bloques sin cerrar (o cerrados de mas)
                for tag in BLOQUES:
                    abre = len(re.findall(r"\{%%\s*%s[\s%%]" % tag, s))
                    cierra = len(re.findall(r"\{%%\s*end%s\s*%%\}" % tag, s))
                    if abre != cierra:
                        problemas.append(
                            (corta, 0,
                             f"{tag}: {abre} abiertos y {cierra} cerrados"))

        for corta, linea, que in problemas:
            donde = f"{corta}:{linea}" if linea else corta
            self.stdout.write(self.style.ERROR(f"  {donde}  {que}"))

        if problemas:
            self.stdout.write(self.style.ERROR(
                f"\n{len(problemas)} problema(s) en {revisadas} plantillas."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(
            f"{revisadas} plantillas revisadas, nada que decir."))
