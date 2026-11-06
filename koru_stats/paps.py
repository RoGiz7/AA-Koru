"""
PAPs de la alianza — meter en Koru lo que vive en «A Dank Fleet Dashboard».

★ DOS FORMATOS, UN SOLO MODELO. La web (fleets.gnf.lt) deja sacar los datos de
dos maneras, y Koru come las dos:

  · JSON de su API (`/api/v1/corporation/participation/{año}/{mes}`) — EL BUENO.
  · CSV de su pantalla de Export — el de siempre, que se queda como respaldo.

★ POR QUÉ EL JSON ES EL BUENO, Y NO ES OPINIÓN. Se cruzaron los 29 meses que
había en CSV contra lo que la API devuelve hoy:

  · El CSV OMITE entre 16 y 43 personas por mes. Casi todas con 0 PAPs — o sea,
    justo a quien el filtro de 5/10 existe para encontrar. Con el CSV, el que no
    fue a nada no aparece, y no aparecer no es lo mismo que cumplir.
  · El CSV REBAJA números de los que sí salen: 24 personas en mayo de 2025, 15 en
    marzo de 2024. En un caso de julio de 2024, 18 en el CSV frente a 26 en la web.
  · Y nunca al revés: el CSV siempre va por debajo o igual, nunca por encima.
    Pinta a correcciones que los FC meten después de bajar el fichero.
  · El JSON trae además el ROL de flota (Combat, Logistics, Ewar, Cyno…), que el
    CSV no exporta, y el flag `isStrategic` de cada tag EN CADA MES, así que no
    hay que adivinar la clasificación hacia atrás.

★ LAS INVARIANTES QUE VALIDAN UNA IMPORTACIÓN (medidas, no supuestas):

  · JSON: `sum(roleTotals) == total` en las 3.075 filas de los 36 meses. Sin una
    excepción. Es LA comprobación de que se ha leído bien.
  · CSV: `sum(grupos de nave) == Total` en las 1.943 filas. Igual de limpio.
  · En los dos formatos, SUMAR LAS FLOTAS DA DE MÁS: una misma PAP se cuenta en
    dos tags a la vez (71 filas en el JSON, 70 en el CSV). Por eso
    `actividades = Total − estratégicas`, nunca la suma de las de paz.
  · Y las estratégicas también se solapan, aunque poquísimo: 5 filas de 3.075, con
    exceso máximo de 2. Se recorta al Total y la fila se marca, porque un +2
    puede colar a alguien por encima del listón sin haberlo pasado.

★ CATÁLOGO PRIMERO. Qué flota es estratégica lo dice `PapFleetType`, no este
fichero. El importador APRENDE: una flota desconocida entra SIN CLASIFICAR y
espera a que alguien decida. Nunca da por hecho que no cuenta — eso rebajaría el
cumplimiento de alguien en silencio. Y lo que declare la fuente (el `isStrategic`
del JSON, o el sufijo `:strategic` del CSV) MANDA sobre lo que haya a mano: la
alianza es la dueña de su propia clasificación.

⚠ EL DESGLOSE SE GUARDA (`PapMonthlyDetalle`), y no por adorno: clasificar una
flota cambia el cumplimiento de todos los meses donde aparece, y sin el desglose
habría que volver a importar los ficheros. `recalcular()` vive de él.
"""

import csv
import hashlib
import io
import json
import logging
import re

logger = logging.getLogger(__name__)

# SDE: Ship. El mismo número que `CATEGORIA_NAVE` en tasks.py; se repite aquí
# para no importar tasks (arrastra Celery) desde una vista.
CATEGORIA_NAVE_SDE = 6

CAT_ESTRATEGICA = "estrategica"
CAT_ACTIVIDAD = "actividad"
CAT_SIN = "sin"

DIM_FLOTA = "flota"
DIM_NAVE = "nave"
DIM_ROL = "rol"

ORIGEN_JSON = "json"
ORIGEN_CSV = "csv"

# --- Formato CSV ----------------------------------------------------------
COL_CUENTA = "Account"
COL_MES = "Month"
COL_TOTAL = "Total"
COL_TOTAL_EST = "Total Strategic"
COL_TOTAL_PAZ = "Total Peacetime"
CABECERAS_FIJAS = frozenset({COL_CUENTA, COL_MES, COL_TOTAL, COL_TOTAL_EST, COL_TOTAL_PAZ})

# Los roles del JSON vienen como lista de números SIN nombres. El orden se sacó
# emparejando `roleTotals` de octubre de 2026 con la tabla «Fleet role» de la
# web, donde los nueve valores eran distintos y no admitían duda.
# ⚠ Las dos últimas no se pudieron identificar: estaban a cero ese mes y mueven
# 3-4 PAPs al mes como mucho. Se guarda el número igual; solo falta el nombre.
ROLES_GNF = [
    "Undefined", "Combat", "Logistics", "Ewar", "Booster", "Support",
    "Interdictors", "Cyno", "CommandDestroyers",
    "(rol sin identificar 9)", "(rol sin identificar 10)",
]

# Semilla del catálogo: la clasificación que declara la propia alianza.
SEMILLA_FLOTAS = {
    "Beehive": CAT_ESTRATEGICA,
    "GSOL": CAT_ESTRATEGICA,
    "Locust": CAT_ESTRATEGICA,
    "SCOUTS": CAT_ESTRATEGICA,
    "SIG/SQUAD Strategic": CAT_ESTRATEGICA,
    "STRATEGIC": CAT_ESTRATEGICA,
    "Survey": CAT_ESTRATEGICA,
    "*IGC": CAT_ACTIVIDAD,
    "*TNT": CAT_ACTIVIDAD,
    "Corp": CAT_ACTIVIDAD,
    "Cricket": CAT_ACTIVIDAD,
    "Incursion-HQ": CAT_ACTIVIDAD,
    "Incursion-VG": CAT_ACTIVIDAD,
    "PEACETIME": CAT_ACTIVIDAD,
    "SIG/SQUAD": CAT_ACTIVIDAD,
    # `*LAWN` sale como columna en 25 ficheros y está a CERO en todas sus filas,
    # y la API no la lista como tag en ningún mes. Nunca tuvo una sola PAP.
    "*LAWN": CAT_ACTIVIDAD,
}

# Flotas que cuentan como «de la corp». Es un dato del catálogo
# (`PapFleetType.es_corp`); esto es solo con qué arranca.
SEMILLA_CORP = frozenset({"Corp"})

# ⚠ RED DE SEGURIDAD, no la fuente: los grupos de nave buenos salen del SDE.
# Son los 45 que aparecen en los ficheros reales, y solo se usan si el SDE no
# contesta — sin ellos, un SDE caído convertiría 45 columnas de nave en 45
# «flotas nuevas» y ensuciaría el catálogo de golpe.
SEMILLA_GRUPOS_NAVE = frozenset({
    "Assault Frigate", "Attack Battlecruiser", "Battleship", "Black Ops",
    "Blockade Runner", "Capital Industrial Ship", "Capsule", "Carrier",
    "Combat Battlecruiser", "Combat Recon Ship", "Command Destroyer",
    "Command Ship", "Corvette", "Covert Ops", "Cruiser",
    "Deep Space Transport", "Destroyer", "Dreadnought",
    "Electronic Attack Ship", "Exhumer", "Expedition Command Ship",
    "Expedition Frigate", "Flag Cruiser", "Force Auxiliary",
    "Force Recon Ship", "Freighter", "Frigate", "Hauler",
    "Heavy Assault Cruiser", "Heavy Interdiction Cruiser",
    "Industrial Command Ship", "Interceptor", "Interdictor", "Jump Freighter",
    "Lancer Dreadnought", "Logistics", "Logistics Frigate", "Marauder",
    "Mining Barge", "Shuttle", "Stealth Bomber", "Strategic Cruiser",
    "Supercarrier", "Tactical Destroyer", "Titan",
})

MESES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


# ---------------------------------------------------------------------------
# Nada de aquí abajo importa Django hasta la sección marcada: así se puede
# probar contra los ficheros de verdad sin levantar el Auth, que es como se
# validó todo lo de arriba.
# ---------------------------------------------------------------------------

def _norm(s):
    """Espacios colapsados y recortados. Ojo: el tag se llama `Cricket ` CON
    espacio al final, en el CSV y en la API. Sin esto habría dos flotas."""
    return " ".join(str(s or "").split())


def _clave(s):
    return _norm(s).casefold()


def _entero(v):
    """Vacío, `-` o separador de miles no deben tumbar 60 filas por una celda."""
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    t = _norm(v).replace(",", "").replace(".", "")
    if not t or t in ("-", "None", "null"):
        return 0
    try:
        return int(t)
    except ValueError:
        return 0


def parse_mes(txt):
    """`January 2024`, `2026 April`, `2024-01`, `2024-01-01T00:00:00Z` → (2024, 1).

    ⚠ Los dos primeros son formatos REALES del mismo exportador: cambió el orden
    en algún momento de 2025. No hay que elegir uno.
    """
    t = _norm(txt)
    if not t:
        return None
    m = re.match(r"^(\d{4})-(\d{2})(?:-\d{2}|$)", t)
    if m:
        anio, mes = int(m.group(1)), int(m.group(2))
        return (anio, mes) if 1 <= mes <= 12 else None
    anio = mes = None
    for pieza in t.replace(",", " ").split():
        if re.fullmatch(r"\d{4}", pieza):
            anio = int(pieza)
            continue
        nombre = pieza.strip(".").casefold()
        if nombre in MESES:
            mes = MESES[nombre]
    return (anio, mes) if anio and mes else None


def periodo_txt(anio, mes):
    return f"{anio:04d}-{mes:02d}"


def _texto(contenido):
    if isinstance(contenido, bytes):
        # utf-8-sig: el exportador mete BOM y sin esto la primera columna se
        # llamaría '﻿Account' y no la encontraría nadie.
        contenido = contenido.decode("utf-8-sig", errors="replace")
    return str(contenido).lstrip("﻿")


class Analisis:
    """Lo que se ha entendido de un fichero, antes de escribir nada."""

    def __init__(self, origen=""):
        self.origen = origen
        self.filas = []        # una por (período, cuenta)
        self.periodos = []     # [(anio, mes)] en orden de aparición
        self.flotas = {}       # nombre -> categoría declarada por la fuente, o None
        self.avisos = []
        self.sin_mes = False

    @property
    def total_paps(self):
        return sum(f["total"] for f in self.filas)

    @property
    def descuadres(self):
        return [f for f in self.filas if not f["cuadra"]]


def _fila(periodo, cuenta, total, estrategicas, declaradas, corp,
          sin_clasificar, cuadra, detalle):
    """Una fila ya calculada. `estrategicas` viene recortada al total."""
    return {
        "periodo": periodo,
        "cuenta": cuenta,
        "total": total,
        "estrategicas": estrategicas,
        "estrategicas_declaradas": declaradas,
        "actividades": max(total - estrategicas, 0),
        "corp": corp,
        "sin_clasificar": sin_clasificar,
        "cuadra": cuadra,
        "detalle": detalle,   # [(dimension, nombre, paps)]
    }


# ---------------------------------------------------------------------------
# JSON de la API — el camino bueno
# ---------------------------------------------------------------------------

def analizar_json(contenido, corps=None):
    """Lee el JSON de la API. Admite tres envoltorios, porque hay tres maneras
    razonables de que llegue aquí:

      · `{"periodos": [{"anio":…, "mes":…, "datos": {…}}, …]}` — el paquete
        completo que suelta el recolector.
      · `[{…}, {…}]` — una lista de respuestas sueltas de la API.
      · `{"startDate": …, "members": […], "tags": […]}` — UNA respuesta tal cual
        la devuelve la API. El período sale de `startDate`, así que no hay que
        decirle de qué mes es.
    """
    corps = {_clave(c) for c in (corps or SEMILLA_CORP)}
    out = Analisis(ORIGEN_JSON)

    try:
        datos = json.loads(_texto(contenido))
    except ValueError as exc:
        out.avisos.append(f"El JSON no se puede leer: {exc}")
        return out

    roles = ROLES_GNF
    bloques = []
    if isinstance(datos, dict) and isinstance(datos.get("periodos"), list):
        if isinstance(datos.get("roles"), list) and datos["roles"]:
            roles = [str(r) for r in datos["roles"]]
        for p in datos["periodos"]:
            if isinstance(p, dict) and isinstance(p.get("datos"), dict):
                bloques.append(p["datos"])
    elif isinstance(datos, list):
        bloques = [b for b in datos if isinstance(b, dict)]
    elif isinstance(datos, dict):
        bloques = [datos]

    if not bloques:
        out.avisos.append("El JSON no trae ningún mes reconocible.")
        return out

    for d in bloques:
        miembros = d.get("members")
        tags = d.get("tags")
        if not isinstance(miembros, list) or not isinstance(tags, list):
            out.avisos.append("Un bloque del JSON no tiene `members` y `tags`; se salta.")
            continue

        periodo = parse_mes(d.get("startDate") or "")
        if not periodo:
            out.sin_mes = True
            out.avisos.append("Un bloque del JSON no trae `startDate` legible; se salta.")
            continue
        if periodo not in out.periodos:
            out.periodos.append(periodo)

        nombres_tag = [_norm(t.get("name")) for t in tags]
        # ★ `isStrategic` lo dice la alianza, mes a mes. Es la clasificación
        # oficial y por eso se guarda como «declarada».
        estrat = [bool(t.get("isStrategic")) for t in tags]
        for n, es in zip(nombres_tag, estrat):
            out.flotas[n] = CAT_ESTRATEGICA if es else CAT_ACTIVIDAD

        for m in miembros:
            cuenta = _norm(m.get("name"))
            if not cuenta:
                continue
            total = _entero(m.get("total"))
            tt = [_entero(x) for x in (m.get("tagTotals") or [])]
            rt = [_entero(x) for x in (m.get("roleTotals") or [])]

            if len(tt) != len(nombres_tag):
                out.avisos.append(
                    f"{cuenta} ({periodo_txt(*periodo)}): tiene {len(tt)} tags y el mes "
                    f"declara {len(nombres_tag)}. Fila saltada para no inventar.")
                continue

            bruto = sum(v for v, es in zip(tt, estrat) if es)
            # ⚠ Recorte: una misma PAP puede llevar dos tags estratégicos. Pasa
            # en 5 filas de 3.075, con exceso máximo de 2, pero un +2 colaría a
            # alguien por encima del listón sin haberlo pasado.
            estrategicas = min(bruto, total)
            if bruto > total:
                out.avisos.append(
                    f"{cuenta} ({periodo_txt(*periodo)}): los tags estratégicos suman "
                    f"{bruto} y el total es {total}; una PAP lleva dos tags. Se recorta a {total}.")

            # La suma de roles cuadra con el total en las 3.075 filas medidas:
            # si aquí falla, el fichero no es lo que creemos.
            cuadra = (sum(rt) == total) if rt else True
            if not cuadra:
                out.avisos.append(
                    f"{cuenta} ({periodo_txt(*periodo)}): los roles suman {sum(rt)} "
                    f"y el total dice {total}.")

            detalle = [(DIM_FLOTA, n, v) for n, v in zip(nombres_tag, tt)]
            detalle += [(DIM_ROL, roles[i] if i < len(roles) else f"rol {i}", v)
                        for i, v in enumerate(rt) if v]

            out.filas.append(_fila(
                periodo, cuenta, total,
                estrategicas=estrategicas,
                declaradas=estrategicas,
                corp=sum(v for n, v in zip(nombres_tag, tt) if _clave(n) in corps),
                sin_clasificar=0,
                cuadra=cuadra,
                detalle=detalle))

    return out


# ---------------------------------------------------------------------------
# CSV de la pantalla de Export — el respaldo
# ---------------------------------------------------------------------------

def plan_cabecera(cabecera, categorias, grupos_nave):
    """Decide, columna por columna, qué es cada una.

    ⚠ NO HAY CABECERA FIJA: los 34 ficheros que había bajados tenían 34
    cabeceras distintas. Las flotas entran y salen y los grupos de nave también.

    El orden de las comprobaciones ES la regla:
      1. Sufijo `:strategic`/`:peacetime` → flota, y el sufijo MANDA.
      2. Está en el catálogo → flota, con su categoría.
      3. Es un grupo de nave del SDE → nave.
      4. Nada de lo anterior → flota NUEVA, sin clasificar.

    El paso 4 es el que importa: una columna desconocida se trata como flota y
    no como nave, porque una flota ignorada son PAPs perdidas y un cumplimiento
    que miente. Y si se equivoca (una nave que el SDE aún no tiene), la suma de
    naves deja de cuadrar y la fila sale marcada: el error se ve, no se traga.
    """
    plan, flotas, naves = [], {}, []
    for bruto in cabecera:
        nombre = _norm(bruto)
        # Todos los ficheros acaban en coma, así que la última columna es vacía.
        if not nombre or nombre in CABECERAS_FIJAS:
            continue
        base, _, sufijo = nombre.partition(":")
        base, sufijo = _norm(base), sufijo.strip().casefold()
        if not base:
            continue
        if sufijo in ("strategic", "peacetime"):
            cat = CAT_ESTRATEGICA if sufijo == "strategic" else CAT_ACTIVIDAD
            plan.append((bruto, DIM_FLOTA, base, cat))
            flotas[base] = cat
        elif base in categorias:
            plan.append((bruto, DIM_FLOTA, base, None))
            flotas.setdefault(base, None)
        elif base in grupos_nave:
            plan.append((bruto, DIM_NAVE, base, None))
            naves.append(base)
        else:
            plan.append((bruto, DIM_FLOTA, base, None))
            flotas.setdefault(base, None)
    return plan, flotas, naves


def analizar_csv(contenido, categorias=None, grupos_nave=None, corps=None,
                 periodo_forzado=None):
    """Lee el CSV de Export. `periodo_forzado` para un fichero sin `Month`."""
    categorias = dict(categorias or SEMILLA_FLOTAS)
    grupos_nave = set(grupos_nave or SEMILLA_GRUPOS_NAVE)
    corps = {_clave(c) for c in (corps or SEMILLA_CORP)}

    out = Analisis(ORIGEN_CSV)
    lector = csv.DictReader(io.StringIO(_texto(contenido)))
    if not lector.fieldnames:
        out.avisos.append("El fichero está vacío o no tiene cabecera.")
        return out

    cabecera = [c for c in lector.fieldnames if c is not None]
    col = {_norm(c): c for c in cabecera}
    if COL_CUENTA not in col or COL_TOTAL not in col:
        out.avisos.append(
            "No hay columna «Account» y «Total»: esto no parece una exportación de PAPs.")
        return out

    trae_mes = COL_MES in col
    trae_total_est = COL_TOTAL_EST in col
    plan, flotas, naves = plan_cabecera(cabecera, categorias, grupos_nave)
    out.flotas = flotas

    if not naves:
        out.avisos.append(
            "No se ha reconocido ni una columna de nave. La cabecera no es la de "
            "siempre: revísalo antes de dar los números por buenos.")

    def cat_de(nombre, declarada):
        return declarada or categorias.get(nombre, CAT_SIN)

    vistos = set()
    for cruda in lector:
        cuenta = _norm(cruda.get(col[COL_CUENTA]))
        if not cuenta:
            continue

        if periodo_forzado:
            periodo = tuple(periodo_forzado)
        elif trae_mes:
            periodo = parse_mes(cruda.get(col[COL_MES]))
        else:
            periodo = None
        if not periodo:
            out.sin_mes = True
            continue
        if periodo not in out.periodos:
            out.periodos.append(periodo)

        por_flota, por_nave = {}, {}
        estrategicas = sin_clasificar = 0
        for bruto, dim, nombre, declarada in plan:
            valor = _entero(cruda.get(bruto))
            if dim == DIM_NAVE:
                if valor:
                    por_nave[nombre] = por_nave.get(nombre, 0) + valor
                continue
            # Las flotas se guardan aunque vengan a cero: el desglose es lo que
            # permite recalcular más adelante.
            por_flota[nombre] = por_flota.get(nombre, 0) + valor
            cat = cat_de(nombre, declarada)
            if cat == CAT_ESTRATEGICA:
                estrategicas += valor
            elif cat == CAT_SIN:
                sin_clasificar += valor

        total = _entero(cruda.get(col[COL_TOTAL]))
        suma_naves = sum(por_nave.values())
        declarado = _entero(cruda.get(col[COL_TOTAL_EST])) if trae_total_est else None

        clave = (periodo, _clave(cuenta))
        if clave in vistos:
            out.avisos.append(
                f"{cuenta} sale dos veces en {periodo_txt(*periodo)}; se queda la última.")
        vistos.add(clave)

        # ⚠ Si la alianza da su `Total Strategic`, ESE manda: viene deduplicado
        # de su base de datos.
        if declarado is not None and declarado != estrategicas:
            out.avisos.append(
                f"{cuenta} ({periodo_txt(*periodo)}): la alianza dice {declarado} "
                f"estratégicas y sumando columnas salen {estrategicas}. Manda la suya.")
        efectivas = min(declarado if declarado is not None else estrategicas, total)

        cuadra = (suma_naves == total)
        if not cuadra:
            out.avisos.append(
                f"{cuenta} ({periodo_txt(*periodo)}): Total={total} pero las naves suman "
                f"{suma_naves}. Puede haber una columna nueva sin reconocer.")

        detalle = [(DIM_FLOTA, n, v) for n, v in sorted(por_flota.items())]
        detalle += [(DIM_NAVE, n, v) for n, v in sorted(por_nave.items()) if v]

        out.filas.append(_fila(
            periodo, cuenta, total,
            estrategicas=efectivas,
            declaradas=declarado,
            corp=sum(v for n, v in por_flota.items() if _clave(n) in corps),
            sin_clasificar=sin_clasificar,
            cuadra=cuadra,
            detalle=detalle))

    if out.sin_mes and not out.filas:
        out.avisos.append(
            "El fichero no trae columna «Month» y no se le ha dicho de qué mes es, "
            "así que no se puede importar: dime el período y lo repito.")
    elif out.sin_mes:
        out.avisos.append("Algunas filas no traían mes legible y se han dejado fuera.")

    nuevas = sorted(n for n in flotas if n not in categorias)
    if nuevas:
        out.avisos.append(
            "Flotas que Koru no conocía, entran SIN CLASIFICAR y NO cuentan para el "
            "filtro hasta que las clasifiques: " + ", ".join(nuevas))

    return out


def es_json(contenido):
    t = _texto(contenido).lstrip()
    return t.startswith("{") or t.startswith("[")


def analizar(contenido, categorias=None, grupos_nave=None, corps=None,
             periodo_forzado=None):
    """Mira qué formato es y llama al lector que toca."""
    if es_json(contenido):
        return analizar_json(contenido, corps)
    return analizar_csv(contenido, categorias, grupos_nave, corps, periodo_forzado)


def huella(contenido):
    """sha256 del fichero, para no importar dos veces lo mismo sin querer. De
    los 34 CSV que había bajados, dos eran copia byte a byte de otros dos."""
    if isinstance(contenido, str):
        contenido = contenido.encode("utf-8")
    return hashlib.sha256(contenido).hexdigest()


# ---------------------------------------------------------------------------
# De aquí abajo ya hace falta Django. Los imports van DENTRO de cada función:
# este módulo lo acaba cargando `paneles` durante el arranque del Auth y no
# debe arrastrar modelos consigo.
# ---------------------------------------------------------------------------

def grupos_nave_sde():
    """Los nombres de grupo de nave, del SDE. La semilla si el SDE no contesta.

    ★ Catálogo primero: qué es una nave lo dice el SDE, no una lista escrita a
    mano que habría que tocar cada vez que FC saque un casco nuevo.
    """
    from django.db import connection
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT name FROM eve_sde_itemgroup WHERE category_id = %s",
                        [CATEGORIA_NAVE_SDE])
            nombres = {_norm(r[0]) for r in cur.fetchall() if r[0]}
        if nombres:
            # La semilla se SUMA, no sustituye: `Flag Cruiser` y
            # `Expedition Command Ship` salen en ficheros de 2026 y un SDE sin
            # actualizar puede no tenerlos todavía.
            return nombres | set(SEMILLA_GRUPOS_NAVE)
    except Exception as exc:
        logger.warning("koru paps: el SDE no da los grupos de nave (%s); se usa la semilla", exc)
    return set(SEMILLA_GRUPOS_NAVE)


def catalogo():
    """({flota: categoría}, {flotas que son de corp})."""
    from .models import PapFleetType
    cats, corps = {}, set()
    for ft in PapFleetType.objects.all():
        cats[ft.nombre] = ft.categoria
        if ft.es_corp:
            corps.add(ft.nombre)
    if not cats:
        return dict(SEMILLA_FLOTAS), set(SEMILLA_CORP)
    return cats, corps


def sembrar_catalogo():
    """Deja en la tabla las flotas que ya conocemos. Idempotente."""
    from .models import PapFleetType
    creadas = 0
    for nombre, cat in SEMILLA_FLOTAS.items():
        _, nuevo = PapFleetType.objects.get_or_create(
            nombre=nombre,
            defaults={"categoria": cat,
                      "es_corp": nombre in SEMILLA_CORP,
                      "declarada_por_alianza": True})
        creadas += bool(nuevo)
    return creadas


def resolver_cuentas(nombres):
    """{nombre del fichero: (main_character_id, nombre del main)}.

    Tres pasos, en este orden:
      1. `PapAccountAlias` — lo atado a mano manda sobre todo.
      2. El nombre es un personaje del Auth → se sube a su main.
      3. Nada: se queda a 0 y sale en el informe para atarlo a mano.

    ⚠ Un nombre que no casa NO se descarta. La fila entra igual con
    `main_character_id = 0`: tirarla haría que el total del mes mintiera, y el
    nombre es justo el dato que hace falta para arreglarlo.
    """
    from django.db import connection
    from .models import PapAccountAlias

    nombres = [n for n in {_norm(n) for n in nombres} if n]
    if not nombres:
        return {}

    fuera = {}
    for al in PapAccountAlias.objects.all():
        k = _clave(al.account_name)
        if k:
            fuera[k] = (al.main_character_id, al.main_character_name or al.account_name)

    pendientes = [n for n in nombres if _clave(n) not in fuera]
    if pendientes:
        ph = ",".join(["%s"] * len(pendientes))
        with connection.cursor() as cur:
            cur.execute(
                "SELECT ec.character_name, "
                "       COALESCE(main_ec.character_id, ec.character_id), "
                "       COALESCE(main_ec.character_name, ec.character_name) "
                "FROM eveonline_evecharacter ec "
                "LEFT JOIN authentication_characterownership co ON co.character_id = ec.id "
                "LEFT JOIN authentication_userprofile        up ON up.user_id      = co.user_id "
                "LEFT JOIN eveonline_evecharacter       main_ec ON main_ec.id      = up.main_character_id "
                "WHERE ec.character_name IN (" + ph + ")", pendientes)
            for nombre, main_id, main_nombre in cur.fetchall():
                fuera.setdefault(_clave(nombre), (int(main_id or 0), main_nombre or ""))

    return {n: fuera.get(_clave(n), (0, "")) for n in nombres}


class Informe:
    """Lo que se le enseña a quien acaba de subir un fichero."""

    def __init__(self, fichero=""):
        self.fichero = fichero
        self.origen = ""
        self.periodos = []           # [(texto, filas)]
        self.filas = 0
        self.total_paps = 0
        self.sin_casar = []
        self.flotas_nuevas = []
        self.flotas_corregidas = []
        self.descuadres = []
        self.saltados = []           # períodos que ya venían de una fuente mejor
        self.avisos = []
        self.ya_estaba = False
        self.ok = False


def importar(contenido, fichero="", usuario=None, periodo_forzado=None, forzar=False):
    """Mete un fichero (JSON o CSV) en la base de datos.

    Idempotente: el mismo mes se reescribe entero. `forzar` salta tanto la
    comprobación de huella como la protección de no pisar JSON con CSV.
    """
    from django.db import transaction
    from .models import (PapFleetType, PapMonthly, PapMonthlyDetalle, PapPeriod)

    inf = Informe(fichero)
    crudo = contenido.encode("utf-8") if isinstance(contenido, str) else contenido
    hash_fichero = huella(crudo)

    if not forzar:
        otro = PapPeriod.objects.filter(fichero_hash=hash_fichero).first()
        if otro:
            inf.ya_estaba = True
            inf.avisos.append(
                f"Este fichero exacto ya se importó ({otro.fichero or 'sin nombre'}, "
                f"{otro.periodo}). No se ha tocado nada.")
            return inf

    sembrar_catalogo()
    cats, corps = catalogo()
    naves = grupos_nave_sde()

    # PRIMERA PASADA: enterarse de qué flotas trae y qué declara la fuente.
    previo = analizar(crudo, cats, naves, corps, periodo_forzado)
    inf.origen = previo.origen
    if not previo.filas:
        inf.avisos.extend(previo.avisos or ["No se ha podido leer ninguna fila."])
        return inf

    for nombre, declarada in sorted(previo.flotas.items()):
        ft = PapFleetType.objects.filter(nombre=nombre).first()
        if ft is None:
            etiqueta = ("estratégica" if declarada == CAT_ESTRATEGICA
                        else "actividad" if declarada else "SIN CLASIFICAR")
            PapFleetType.objects.create(
                nombre=nombre, categoria=declarada or CAT_SIN,
                es_corp=nombre in corps, declarada_por_alianza=bool(declarada))
            inf.flotas_nuevas.append(f"{nombre} ({etiqueta})")
        elif declarada and ft.categoria != declarada:
            # ★ Lo que declare la fuente manda sobre lo puesto a mano: la
            # alianza es la dueña de su propia clasificación.
            antes = ft.categoria
            ft.categoria = declarada
            ft.declarada_por_alianza = True
            ft.save(update_fields=["categoria", "declarada_por_alianza"])
            inf.flotas_corregidas.append(f"{nombre}: {antes} → {declarada}")
        elif declarada and not ft.declarada_por_alianza:
            ft.declarada_por_alianza = True
            ft.save(update_fields=["declarada_por_alianza"])

    # SEGUNDA PASADA, con el catálogo ya corregido por el propio fichero.
    cats, corps = catalogo()
    an = analizar(crudo, cats, naves, corps, periodo_forzado)
    inf.avisos.extend(an.avisos)
    inf.flotas_nuevas = sorted(set(inf.flotas_nuevas))
    inf.descuadres = [f"{f['cuenta']} ({periodo_txt(*f['periodo'])})" for f in an.descuadres]

    resueltos = resolver_cuentas({f["cuenta"] for f in an.filas})

    por_periodo = {}
    for f in an.filas:
        por_periodo.setdefault(f["periodo"], []).append(f)

    with transaction.atomic():
        for (anio, mes), filas in sorted(por_periodo.items()):
            per, nuevo = PapPeriod.objects.get_or_create(anio=anio, mes=mes)

            # ⚠ Un CSV NO pisa un mes que ya vino del JSON. Está medido que el
            # CSV se deja gente fuera y rebaja números; dejarle sobrescribir al
            # bueno sería empeorar los datos sin avisar.
            if (not forzar and not nuevo and per.origen == ORIGEN_JSON
                    and an.origen == ORIGEN_CSV):
                inf.saltados.append(periodo_txt(anio, mes))
                continue

            per.origen = an.origen
            per.fichero = (fichero or "")[:160]
            per.fichero_hash = hash_fichero
            per.filas = len(filas)
            per.importado_por = usuario if getattr(usuario, "pk", None) else None
            sin_casar = [f["cuenta"] for f in filas
                         if not resueltos.get(f["cuenta"], (0, ""))[0]]
            per.sin_casar = len(sin_casar)
            per.avisos = "\n".join(an.avisos)[:4000]
            per.save()

            # Las cuentas que ya no salen se van: si la alianza rehace la
            # exportación, manda la última.
            vivas = {f["cuenta"] for f in filas}
            PapMonthly.objects.filter(periodo=per).exclude(account_name__in=vivas).delete()

            for f in filas:
                main_id, main_nombre = resueltos.get(f["cuenta"], (0, ""))
                fila, _ = PapMonthly.objects.update_or_create(
                    periodo=per, account_name=f["cuenta"][:100],
                    defaults=dict(
                        main_character_id=main_id,
                        main_character_name=(main_nombre or "")[:100],
                        total=f["total"], estrategicas=f["estrategicas"],
                        estrategicas_declaradas=f["estrategicas_declaradas"],
                        actividades=f["actividades"], corp=f["corp"],
                        sin_clasificar=f["sin_clasificar"], cuadra=f["cuadra"]))
                # El desglose se borra y se reescribe: es la foto del fichero,
                # no un histórico que haya que conservar.
                PapMonthlyDetalle.objects.filter(fila=fila).delete()
                PapMonthlyDetalle.objects.bulk_create([
                    PapMonthlyDetalle(fila=fila, dimension=d, nombre=n[:80], paps=v)
                    for d, n, v in f["detalle"]])

            inf.periodos.append((periodo_txt(anio, mes), len(filas)))
            inf.sin_casar.extend(sin_casar)

    if inf.saltados:
        inf.avisos.append(
            "Meses que ya venían del JSON de la API y NO se han pisado con el CSV "
            "(el CSV trae menos gente y números más bajos): " + ", ".join(inf.saltados))

    inf.filas = sum(n for _, n in inf.periodos)
    inf.total_paps = an.total_paps
    inf.sin_casar = sorted(set(inf.sin_casar))
    inf.ok = bool(inf.periodos)
    return inf


def recalcular(periodos=None):
    """Recalcula estratégicas/actividades/corp desde el desglose guardado.

    ★ ESTA ES LA FUNCIÓN QUE JUSTIFICA GUARDAR EL DESGLOSE: clasificar una
    flota cambia el cumplimiento de todos los meses donde aparece, y sin esto
    habría que volver a importar los ficheros — y encima habría que tenerlos.

    ⚠ Las filas con `estrategicas_declaradas` NO se tocan: ahí la alianza ya
    dijo su cifra (todo el JSON, y los CSV desde agosto de 2026), y reclasificar
    una flota a mano no mejora un dato que viene de la fuente.
    """
    from .models import PapMonthly

    cats, corps = catalogo()
    estrategicas = {_clave(n) for n, c in cats.items() if c == CAT_ESTRATEGICA}
    sin = {_clave(n) for n, c in cats.items() if c == CAT_SIN}
    corps = {_clave(n) for n in corps}

    filas = PapMonthly.objects.prefetch_related("detalles")
    if periodos:
        filas = filas.filter(periodo__in=list(periodos))

    tocadas = 0
    for fila in filas:
        desglose = {_clave(d.nombre): d.paps for d in fila.detalles.all()
                    if d.dimension == DIM_FLOTA}
        if not desglose:
            continue
        nueva_est = fila.estrategicas_declaradas
        if nueva_est is None:
            nueva_est = sum(v for n, v in desglose.items() if n in estrategicas)
        nueva_est = min(nueva_est, fila.total)
        cambios = dict(
            estrategicas=nueva_est,
            actividades=max(fila.total - nueva_est, 0),
            corp=sum(v for n, v in desglose.items() if n in corps),
            sin_clasificar=sum(v for n, v in desglose.items() if n in sin),
        )
        if any(getattr(fila, k) != v for k, v in cambios.items()):
            for k, v in cambios.items():
                setattr(fila, k, v)
            fila.save(update_fields=list(cambios))
            tocadas += 1
    return tocadas
