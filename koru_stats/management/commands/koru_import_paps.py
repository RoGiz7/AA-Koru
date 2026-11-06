"""
Carga de PAPs desde la línea de comandos.

Para la primera carga (los 36 meses de golpe) y para cuando haya que rehacer
algo sin pasar por el navegador.

    python manage.py koru_import_paps ~/paps-gnf-historico.json
    python manage.py koru_import_paps "C:/.../Papas/*.csv"
    python manage.py koru_import_paps fichero.csv --periodo 2024-01

⚠ Un CSV no pisa un mes que ya vino del JSON de la API: está medido que el CSV
se deja gente fuera y rebaja números. Con `--forzar` se salta esa protección.
"""

import glob
import os

from django.core.management.base import BaseCommand, CommandError

from koru_stats import paps


class Command(BaseCommand):
    help = "Importa PAPs de la alianza desde ficheros JSON (API) o CSV (Export)."

    def add_arguments(self, parser):
        parser.add_argument(
            "rutas", nargs="+",
            help="Ficheros, carpetas o patrones. Una carpeta coge sus .json y .csv.")
        parser.add_argument(
            "--periodo", default="",
            help="AAAA-MM para un CSV que no traiga columna «Month».")
        parser.add_argument(
            "--forzar", action="store_true",
            help="Reimporta aunque el fichero ya esté y deja que un CSV pise a un JSON.")
        parser.add_argument(
            "--probar", action="store_true",
            help="Lee y cuenta, pero no escribe nada en la base de datos.")

    def handle(self, *args, **opts):
        ficheros = []
        for ruta in opts["rutas"]:
            ruta = os.path.expanduser(ruta)
            if os.path.isdir(ruta):
                for patron in ("*.json", "*.csv"):
                    ficheros.extend(sorted(glob.glob(os.path.join(ruta, patron))))
            elif any(c in ruta for c in "*?["):
                ficheros.extend(sorted(glob.glob(ruta)))
            elif os.path.isfile(ruta):
                ficheros.append(ruta)
            else:
                raise CommandError(f"No existe: {ruta}")

        if not ficheros:
            raise CommandError("No hay ningún fichero que importar.")

        forzado = None
        if opts["periodo"]:
            forzado = paps.parse_mes(opts["periodo"])
            if not forzado:
                raise CommandError(f"No entiendo el período «{opts['periodo']}». Usa 2026-10.")

        # ★ Los JSON primero, SIEMPRE. Así, cuando luego entren los CSV, la
        # protección de «un CSV no pisa un JSON» tiene algo que proteger. Al
        # revés, los CSV entrarían antes y el JSON los corregiría igual, pero
        # se escribiría dos veces y el log contaría una historia confusa.
        ficheros.sort(key=lambda f: (0 if f.lower().endswith(".json") else 1, f))

        total_filas = total_paps = 0
        for ruta in ficheros:
            nombre = os.path.basename(ruta)
            with open(ruta, "rb") as fh:
                contenido = fh.read()

            if opts["probar"]:
                an = paps.analizar(contenido, periodo_forzado=forzado)
                self.stdout.write(
                    f"{nombre:34s} [{an.origen or '?':4s}] "
                    f"{len(an.periodos):2d} mes(es) · {len(an.filas):4d} filas · "
                    f"{an.total_paps:6d} PAPs"
                    + (f" · {len(an.descuadres)} descuadres" if an.descuadres else ""))
                for aviso in an.avisos[:3]:
                    self.stdout.write(self.style.WARNING(f"    · {aviso}"))
                continue

            inf = paps.importar(contenido, nombre, None, forzado, forzar=opts["forzar"])

            if inf.ya_estaba:
                self.stdout.write(f"{nombre:34s} ya estaba, se salta")
                continue
            if not inf.ok:
                self.stdout.write(self.style.ERROR(f"{nombre:34s} NO ha entrado"))
                for aviso in inf.avisos[:4]:
                    self.stdout.write(self.style.ERROR(f"    · {aviso}"))
                continue

            total_filas += inf.filas
            total_paps += inf.total_paps
            meses = ", ".join(p for p, _ in inf.periodos)
            self.stdout.write(self.style.SUCCESS(
                f"{nombre:34s} [{inf.origen:4s}] {inf.filas:4d} filas · {meses}"))
            if inf.flotas_nuevas:
                self.stdout.write(self.style.WARNING(
                    f"    flotas nuevas: {', '.join(inf.flotas_nuevas)}"))
            if inf.flotas_corregidas:
                self.stdout.write(f"    clasificación corregida: {', '.join(inf.flotas_corregidas)}")
            if inf.saltados:
                self.stdout.write(self.style.WARNING(
                    f"    meses NO pisados (ya venían del JSON): {', '.join(inf.saltados)}"))
            if inf.sin_casar:
                self.stdout.write(self.style.WARNING(
                    f"    {len(inf.sin_casar)} nombre(s) sin casar con el Auth"))
            if inf.descuadres:
                self.stdout.write(self.style.WARNING(
                    f"    {len(inf.descuadres)} línea(s) donde el desglose no suma"))

        if not opts["probar"]:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(
                f"TOTAL: {total_filas} filas, {total_paps} PAPs, {len(ficheros)} fichero(s)."))
            self.stdout.write(
                "Repasa las flotas sin clasificar en Koru → PAPs → Flotas y nombres.")
