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
DIM_FC = "fc"
DIM_LOGI = "logi"

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
# `FleetCommand` (la 10) salió de la tabla «Fleet role» de febrero de 2025, el
# único mes visto donde no está a cero.
# ⚠ La 9 sigue sin nombre: está a cero en casi todos los meses y suma unas 40
# PAPs en tres años. El número se guarda igual; solo falta la etiqueta.
ROLES_GNF = [
    "Undefined", "Combat", "Logistics", "Ewar", "Booster", "Support",
    "Interdictors", "Cyno", "CommandDestroyers",
    "(rol sin identificar 9)", "FleetCommand",
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

# ⚠ `*LAWN` es la ÚNICA de la semilla que la alianza nunca declaró: desapareció
# antes de que empezaran a etiquetar. La ponemos como actividad porque está a
# cero en los 34 ficheros y la API no la lista como tag en ningún mes, pero esa
# es una decisión NUESTRA. La pantalla tiene una columna que dice de dónde sale
# cada categoría, y poner ahí «la alianza» sería mentir en el sitio exacto donde
# alguien va a mirar para saber de quién fiarse.
SEMILLA_NO_DECLARADAS = frozenset({"*LAWN"})

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
          sin_clasificar, cuadra, detalle, fc=0, logi=0):
    """Una fila ya calculada. `estrategicas` viene recortada al total."""
    return {
        "fc": fc,
        "logi": logi,
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

def _por_cuenta(bloque):
    """{cuenta: (total, [(tag, valor)])} de un bloque de mando o de anclaje.

    `/corporation/commander/` y `/corporation/logi-anchor/` devuelven la misma
    forma: `{"accounts": [{"name", "total", "series": [{"name","value"}]}]}`.
    Un bloque que no venga (un paquete viejo, o el mes sin datos) da {}, y las
    filas salen con 0 — que es la verdad, no un hueco.
    """
    fuera = {}
    if not isinstance(bloque, dict):
        return fuera
    for cuenta in bloque.get("accounts") or []:
        if not isinstance(cuenta, dict):
            continue
        nombre = _clave(cuenta.get("name"))
        if not nombre:
            continue
        series = [(_norm(s.get("name")), _entero(s.get("value")))
                  for s in (cuenta.get("series") or []) if isinstance(s, dict)]
        fuera[nombre] = (_entero(cuenta.get("total")), series)
    return fuera


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

    roles = list(ROLES_GNF)
    bloques = []
    if isinstance(datos, dict) and isinstance(datos.get("periodos"), list):
        if isinstance(datos.get("roles"), list) and datos["roles"]:
            # El fichero manda sobre el código: él sabe con qué mapeo se bajó.
            # ⚠ Salvo cuando trae un hueco. Un paquete bajado antes de que
            # supiéramos el nombre de un rol lleva dentro «(rol sin identificar
            # N)», y esa etiqueta vacía no debe pisar a una que sí sabemos.
            del_fichero = [str(r) for r in datos["roles"]]
            roles = [ROLES_GNF[i] if (r.startswith("(rol sin identificar")
                                      and i < len(ROLES_GNF)
                                      and not ROLES_GNF[i].startswith("(rol sin"))
                     else r
                     for i, r in enumerate(del_fichero)]
        for p in datos["periodos"]:
            if isinstance(p, dict) and isinstance(p.get("datos"), dict):
                # `fc` y `logi` son opcionales: un paquete bajado antes de que
                # el recolector los trajera sigue entrando, con 0 en esas dos.
                bloques.append((p["datos"], p.get("fc"), p.get("logi")))
    elif isinstance(datos, list):
        bloques = [(b, None, None) for b in datos if isinstance(b, dict)]
    elif isinstance(datos, dict):
        bloques = [(datos, datos.get("fc"), datos.get("logi"))]

    if not bloques:
        out.avisos.append("El JSON no trae ningún mes reconocible.")
        return out

    for d, bloque_fc, bloque_logi in bloques:
        mando = _por_cuenta(bloque_fc)
        anclaje = _por_cuenta(bloque_logi)
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

            fc_total, fc_series = mando.get(_clave(cuenta), (0, []))
            logi_total, logi_series = anclaje.get(_clave(cuenta), (0, []))
            detalle += [(DIM_FC, n, v) for n, v in fc_series if v]
            detalle += [(DIM_LOGI, n, v) for n, v in logi_series if v]

            out.filas.append(_fila(
                periodo, cuenta, total,
                estrategicas=estrategicas,
                declaradas=estrategicas,
                corp=sum(v for n, v in zip(nombres_tag, tt) if _clave(n) in corps),
                sin_clasificar=0,
                cuadra=cuadra,
                detalle=detalle,
                fc=fc_total,
                logi=logi_total))

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
                      "declarada_por_alianza": nombre not in SEMILLA_NO_DECLARADAS})
        creadas += bool(nuevo)
    return creadas


def dueno_en(periodo):
    """{character_id: (main_id, main_nombre)} tal como era al final de ESE mes.

    ★ Sale de `CharacterOwnershipSnapshot`, la foto diaria que ya guarda Koru.
    Se coge la foto más reciente que NO pase del último día del mes: así una PAP
    de agosto de 2025 se ata a quien tenía el personaje entonces, no a quien lo
    tenga hoy.

    ⚠ Las fotos empiezan en junio de 2026. Para los meses anteriores esto
    devuelve {} y se resuelve contra el Auth de hoy, que es lo único que hay.
    No se inventa nada: simplemente no se puede saber.
    """
    from django.db import connection

    anio, mes = periodo
    fin = f"{anio + (mes == 12):04d}-{(mes % 12) + 1:02d}-01"
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT s.character_id, s.main_character_id "
                "FROM koru_stats_characterownershipsnapshot s "
                "JOIN (SELECT character_id, MAX(snapshot_date) AS d "
                "      FROM koru_stats_characterownershipsnapshot "
                "      WHERE snapshot_date < %s GROUP BY character_id) u "
                "  ON u.character_id = s.character_id AND u.d = s.snapshot_date",
                [fin])
            return {int(c): int(m or 0) for c, m in cur.fetchall() if m}
    except Exception as exc:
        logger.warning("koru paps: no hay foto de ownership para %s (%s)", periodo, exc)
        return {}


def resolver_cuentas(nombres, periodo=None):
    """{nombre del fichero: (main_character_id, nombre del main)}.

    Cuatro pasos, en este orden:
      1. `PapAccountAlias` — lo atado a mano manda sobre todo.
      2. El nombre es un personaje del Auth → se sube a su main.
      3. Si hay foto de ownership de ese mes, se corrige con ella: manda de
         quién ERA el personaje entonces, no de quién es hoy.
      4. Nada: se queda a 0 y sale en el informe para atarlo a mano.

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

    historico = dueno_en(periodo) if periodo else {}
    nombres_main = {}

    pendientes = [n for n in nombres if _clave(n) not in fuera]
    if pendientes:
        ph = ",".join(["%s"] * len(pendientes))
        with connection.cursor() as cur:
            cur.execute(
                "SELECT ec.character_name, ec.character_id, "
                "       COALESCE(main_ec.character_id, ec.character_id), "
                "       COALESCE(main_ec.character_name, ec.character_name) "
                "FROM eveonline_evecharacter ec "
                "LEFT JOIN authentication_characterownership co ON co.character_id = ec.id "
                "LEFT JOIN authentication_userprofile        up ON up.user_id      = co.user_id "
                "LEFT JOIN eveonline_evecharacter       main_ec ON main_ec.id      = up.main_character_id "
                "WHERE ec.character_name IN (" + ph + ")", pendientes)
            for nombre, char_id, main_id, main_nombre in cur.fetchall():
                # ★ Si hay foto de ese mes, manda la foto.
                de_entonces = historico.get(int(char_id or 0))
                if de_entonces:
                    main_id = de_entonces
                    main_nombre = ""
                fuera.setdefault(_clave(nombre), (int(main_id or 0), main_nombre or ""))
                nombres_main[int(main_id or 0)] = main_nombre or ""

    # El nombre del main que salió de la foto hay que buscarlo aparte.
    faltan = sorted({mid for mid, nom in fuera.values() if mid and not nom})
    if faltan:
        ph = ",".join(["%s"] * len(faltan))
        with connection.cursor() as cur:
            cur.execute("SELECT character_id, character_name FROM eveonline_evecharacter "
                        "WHERE character_id IN (" + ph + ")", faltan)
            por_id = {int(c): n or "" for c, n in cur.fetchall()}
        fuera = {k: (mid, nom or por_id.get(mid, "")) for k, (mid, nom) in fuera.items()}

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
        self.enriquecidos = []       # [(período, filas)] a los que el CSV puso naves
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


    por_periodo = {}
    for f in an.filas:
        por_periodo.setdefault(f["periodo"], []).append(f)

    with transaction.atomic():
        for (anio, mes), filas in sorted(por_periodo.items()):
            per, nuevo = PapPeriod.objects.get_or_create(anio=anio, mes=mes)

            # ⚠ Un CSV NO pisa un mes que ya vino del JSON: está medido que el
            # CSV se deja gente fuera y rebaja números. Pero TAMPOCO se tira,
            # porque trae una cosa que el JSON no tiene — el desglose por GRUPO
            # DE NAVE. Así que aporta solo eso y no toca ni un número.
            if (not forzar and not nuevo and per.origen == ORIGEN_JSON
                    and an.origen == ORIGEN_CSV):
                tocadas = _enriquecer_naves(per, filas)
                if tocadas:
                    inf.enriquecidos.append((periodo_txt(anio, mes), tocadas))
                else:
                    inf.saltados.append(periodo_txt(anio, mes))
                continue

            # ★ Se resuelve POR MES, con la foto de ownership de su momento.
            # Antes se resolvía todo contra el Auth de hoy, y eso mudaba en
            # silencio las PAPs de un personaje que hubiera cambiado de dueño.
            resueltos = resolver_cuentas({f["cuenta"] for f in filas}, (anio, mes))
            # ⚠ Lo ya atado NO se vuelve a tocar: la historia se congela según
            # se escribe. Los que siguen a 0 sí se reintentan, para recoger a
            # quien se registre en el Auth más adelante.
            ya_atados = {_clave(x.account_name): (x.main_character_id, x.main_character_name)
                         for x in PapMonthly.objects.filter(periodo=per)
                         if x.main_character_id}

            def _atar(cuenta):
                return ya_atados.get(_clave(cuenta), resueltos.get(cuenta, (0, "")))

            per.origen = an.origen
            per.fichero = (fichero or "")[:160]
            per.fichero_hash = hash_fichero
            per.filas = len(filas)
            per.importado_por = usuario if getattr(usuario, "pk", None) else None
            sin_casar = [f["cuenta"] for f in filas if not _atar(f["cuenta"])[0]]
            per.sin_casar = len(sin_casar)
            per.avisos = "\n".join(an.avisos)[:4000]
            per.save()

            # Las cuentas que ya no salen se van: si la alianza rehace la
            # exportación, manda la última.
            vivas = {f["cuenta"] for f in filas}
            PapMonthly.objects.filter(periodo=per).exclude(account_name__in=vivas).delete()

            for f in filas:
                main_id, main_nombre = _atar(f["cuenta"])
                fila, _ = PapMonthly.objects.update_or_create(
                    periodo=per, account_name=f["cuenta"][:100],
                    defaults=dict(
                        main_character_id=main_id,
                        main_character_name=(main_nombre or "")[:100],
                        total=f["total"], estrategicas=f["estrategicas"],
                        estrategicas_declaradas=f["estrategicas_declaradas"],
                        actividades=f["actividades"], corp=f["corp"],
                        fc=f.get("fc", 0), logi=f.get("logi", 0),
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
    if inf.enriquecidos:
        inf.avisos.append(
            "Meses a los que el CSV ha puesto el desglose por nave sin tocar los "
            "números: " + ", ".join(f"{p} ({n})" for p, n in inf.enriquecidos))

    inf.filas = sum(n for _, n in inf.periodos)
    inf.total_paps = an.total_paps
    inf.sin_casar = sorted(set(inf.sin_casar))
    inf.ok = bool(inf.periodos)
    return inf


def _enriquecer_naves(periodo, filas):
    """Le pone a un mes ya importado el desglose por nave que trae un CSV.

    ★ Es la razón de que el CSV siga sirviendo para algo. El JSON de la API es
    mejor en todo MENOS en una cosa: no dice en qué nave fue cada PAP, y el CSV
    sí (por grupo: Battleship, Logistics, Interceptor…). Medido sobre los 29
    meses con CSV, cubre el 98% de sus PAPs.

    ⚠ No toca NI UN número. Solo reemplaza las filas de dimensión `nave`. Si
    mezclara los totales estaríamos volviendo a meter los números bajos del CSV
    por la puerta de atrás, que es justo lo que se decidió no hacer.
    """
    from .models import PapMonthly, PapMonthlyDetalle

    por_cuenta = {_clave(f.account_name): f
                  for f in PapMonthly.objects.filter(periodo=periodo)}
    tocadas = 0
    for f in filas:
        fila = por_cuenta.get(_clave(f["cuenta"]))
        if not fila:
            continue
        naves = [(n, v) for d, n, v in f["detalle"] if d == DIM_NAVE and v]
        if not naves:
            continue
        PapMonthlyDetalle.objects.filter(fila=fila, dimension=DIM_NAVE).delete()
        PapMonthlyDetalle.objects.bulk_create([
            PapMonthlyDetalle(fila=fila, dimension=DIM_NAVE, nombre=n[:80], paps=v)
            for n, v in naves])
        tocadas += 1
    return tocadas


def matriz(periodo, dimension=DIM_FLOTA):
    """La tabla de toda la vida: cada piloto contra cada columna.

    Es lo que enseñaba el CSV y lo que se pierde al resumir en «estratégicas y
    actividades». `dimension` elige si las columnas son tipos de flota o grupos
    de nave.
    """
    from django.db.models import Sum

    from .models import PapMonthly, PapMonthlyDetalle, PapPeriod

    try:
        anio, mes = str(periodo).split("-")[:2]
        per = PapPeriod.objects.filter(anio=int(anio), mes=int(mes)).first()
    except (ValueError, TypeError):
        per = None
    if not per:
        return None

    detalles = (PapMonthlyDetalle.objects
                .filter(fila__periodo=per, dimension=dimension)
                .values("fila_id", "nombre", "paps"))
    celdas, totales = {}, {}
    for d in detalles:
        if not d["paps"]:
            continue
        celdas.setdefault(d["fila_id"], {})[d["nombre"]] = d["paps"]
        totales[d["nombre"]] = totales.get(d["nombre"], 0) + d["paps"]
    if not celdas:
        return None

    # Columnas ordenadas por volumen: lo que más se vuela, primero.
    columnas = [n for n, _ in sorted(totales.items(), key=lambda x: (-x[1], x[0]))]
    filas = []
    for fila in (PapMonthly.objects.filter(periodo=per)
                 .select_related("periodo").order_by("-total", "account_name")):
        valores = celdas.get(fila.id)
        if not valores:
            continue
        filas.append({
            "linea": fila,
            "celdas": [valores.get(c, 0) for c in columnas],
            "suma": sum(valores.values()),
        })
    return {"periodo": per, "columnas": columnas, "filas": filas,
            "totales": [totales[c] for c in columnas],
            "gran_total": sum(totales.values()), "dimension": dimension}


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


# ---------------------------------------------------------------------------
# Consultas para las pantallas. Viven aquí y no en views.py porque son del
# dominio de las PAPs, y views.py ya tiene 7.600 líneas.
# ---------------------------------------------------------------------------

def meses_pendientes(hoy=None):
    """Los meses cerrados que faltan por importar. Lista vacía si está al día.

    ★ Que Koru se dé cuenta solo es mejor que acordarse. Un aviso que sale
    cuando falta algo y desaparece cuando dejas de deber nada no genera ruido;
    un recordatorio mensual fijo, sí, y la gente aprende a ignorarlo.

    ⚠ Busca HUECOS, no solo el final. Si faltara un mes de en medio —porque una
    importación se quedó a medias— también lo canta. El mes en curso no cuenta:
    todavía no ha cerrado.
    """
    from datetime import date

    from .models import PapPeriod

    tengo = {(a, m) for a, m in PapPeriod.objects.values_list("anio", "mes")}
    if not tengo:
        return []

    hoy = hoy or date.today()
    ultimo_cerrado = (hoy.year, hoy.month - 1) if hoy.month > 1 else (hoy.year - 1, 12)

    faltan = []
    anio, mes = min(tengo)
    while (anio, mes) <= ultimo_cerrado:
        if (anio, mes) not in tengo:
            faltan.append(periodo_txt(anio, mes))
        mes += 1
        if mes > 12:
            mes, anio = 1, anio + 1
    return faltan


def top_estrategicas(periodo, n=10):
    """Los `n` que más estratégicas hicieron en ese mes. None si no está importado.

    Devolver None y no una lista vacía está hecho a propósito: la pantalla de
    Estadísticas cubre meses que pueden no tener PAPs, y una tarjeta vacía
    haría pensar que ese mes nadie voló.
    """
    from .models import PapMonthly, PapPeriod
    try:
        anio, mes = str(periodo).split("-")[:2]
        per = PapPeriod.objects.filter(anio=int(anio), mes=int(mes)).first()
    except (ValueError, TypeError):
        per = None
    if not per:
        return None
    filas = list(PapMonthly.objects
                 .filter(periodo=per)
                 .select_related("periodo")
                 .order_by("-estrategicas", "-total", "account_name")[:n])
    if not filas:
        return None
    return {"periodo": per, "filas": filas, "tope": filas[0].estrategicas or 1}


def historial_piloto(main_character_id, meses=24):
    """Lo de una persona: sus últimos meses y en qué ha volado.

    El desglose por ROL (Combat, Logistics, Ewar, Cyno…) es lo que no enseña ni
    la web de la alianza por persona, y es lo que de verdad dice a qué juega
    alguien dentro de una flota.
    """
    from django.db.models import Sum

    from .models import PapMonthly, PapMonthlyDetalle

    if not main_character_id:
        return None
    filas = list(PapMonthly.objects
                 .filter(main_character_id=main_character_id)
                 .select_related("periodo")
                 .order_by("-periodo__anio", "-periodo__mes")[:meses])
    if not filas:
        return None

    agregado = (PapMonthlyDetalle.objects
                .filter(fila_id__in=[f.id for f in filas])
                .values("dimension", "nombre")
                .annotate(n=Sum("paps"))
                .order_by("-n"))
    por_dim = {}
    for r in agregado:
        if r["n"]:
            por_dim.setdefault(r["dimension"], []).append({"nombre": r["nombre"], "paps": r["n"]})

    return {
        "filas": filas,
        "flotas": por_dim.get(DIM_FLOTA, [])[:12],
        "roles": por_dim.get(DIM_ROL, [])[:12],
        "mando": por_dim.get(DIM_FC, [])[:8],
        "total": sum(f.total for f in filas),
        "estrategicas": sum(f.estrategicas for f in filas),
        "corp": sum(f.corp for f in filas),
        "fc": sum(f.fc for f in filas),
        "cumplidos": sum(1 for f in filas if f.cumple),
        "meses": len(filas),
    }


def reincidentes(minimo=3):
    """Quién lleva `minimo` meses SEGUIDOS por debajo del listón.

    ★ TRES COSAS QUE NO SON LA MISMA, Y POR ESO NO VAN JUNTAS:

      · DEJÓ DE CUMPLIR — iba bien y lleva meses sin ir. Es la alarma de verdad
        y por eso va arriba. Que alguien pase de cumplir a no cumplir dice
        algo; que alguien no haya cumplido nunca, no dice nada nuevo.
      · NUNCA HA CUMPLIDO — tres años sin llegar al listón. Suelen ser alts o
        gente que no vuela. Es un censo, no una conversación.
      · YA NO ESTÁ — su racha no llega al último mes importado: desapareció de
        la lista de la alianza. Esos NO salen, solo se cuentan. Perseguir a
        quien se fue hace cuatro meses no es seguimiento, es ruido.

    ⚠ La primera versión de esto mezclaba las tres y ordenaba por longitud de
    racha, así que lo primero que se veía eran rachas de 36 meses de gente que
    nunca ha volado — justo lo menos accionable de todo.

    ★ LAS DOS REGLAS DE LA RACHA:

      · SEGUIDOS, no sueltos, contados hacia atrás desde el último mes en que
        la persona aparece. Lo que importa es si SIGUE pasando.
      · UN MES EN EL QUE NO APARECE CORTA LA RACHA, no la continúa. No sabemos
        si estaba en la corp, y contar un hueco como fallo es acusar sin dato.

    «En duda» tampoco cuenta como fallo: si la duda es nuestra —flotas sin
    clasificar— no se le carga a él.
    """
    from .models import PapMonthly, PapPeriod

    ultimo = PapPeriod.objects.order_by("-anio", "-mes").first()
    if not ultimo:
        return {"minimo": minimo, "activos": [], "inactivos": [], "idos": 0, "ultimo": ""}
    tope = (ultimo.anio, ultimo.mes)

    filas = (PapMonthly.objects
             .select_related("periodo")
             .order_by("-periodo__anio", "-periodo__mes"))

    por_persona = {}
    for f in filas:
        clave = f.main_character_id or ("?" + _clave(f.account_name))
        por_persona.setdefault(clave, []).append(f)

    fuera, idos = [], 0
    for lineas in por_persona.values():
        racha, anterior = [], None
        for f in lineas:
            if anterior is not None:
                hueco = (anterior.periodo.anio * 12 + anterior.periodo.mes) - 1
                if (f.periodo.anio * 12 + f.periodo.mes) != hueco:
                    break
            if f.cumple or f.dudoso:
                break
            racha.append(f)
            anterior = f
        if len(racha) < minimo:
            continue

        # ⚠ Si la racha no llega al último mes importado, esa persona ya no
        # aparece en la lista de la alianza: se fue. Se cuenta y no se enseña.
        if (racha[0].periodo.anio, racha[0].periodo.mes) != tope:
            idos += 1
            continue

        # ¿Llegó a cumplir alguna vez ANTES de la racha? Eso es lo que separa
        # un deterioro de alguien que nunca ha ido.
        desde = racha[-1].periodo.anio * 12 + racha[-1].periodo.mes
        cumplio_antes = any(
            f.cumple and (f.periodo.anio * 12 + f.periodo.mes) < desde
            for f in lineas)

        paps = sum(x.total for x in racha)
        fuera.append({
            "piloto": racha[0].main_character_name or racha[0].account_name,
            "cuenta": racha[0].account_name,
            "main_character_id": racha[0].main_character_id,
            "meses": len(racha),
            "desde": racha[-1].periodo.periodo,
            "hasta": racha[0].periodo.periodo,
            "paps": paps,
            "estrategicas": sum(x.estrategicas for x in racha),
            "corp": sum(x.corp for x in racha),
            "cumplio_antes": cumplio_antes,
            # Tres meses a cero es alguien que se ha ido o está AFK; tres meses
            # volando mucho sin tocar lo obligatorio es alguien que está y
            # decide no ir. Dos conversaciones distintas, dos tablas distintas.
            "activo": paps > 0,
            "lineas": racha,
        })

    # ★ El deterioro primero, y dentro de cada grupo el que más vuela arriba:
    # alguien con 134 PAPs y 5 estratégicas importa más que alguien con 4.
    fuera.sort(key=lambda r: (not r["cumplio_antes"], -r["paps"], -r["meses"]))
    return {
        "minimo": minimo,
        "ultimo": ultimo.periodo,
        "idos": idos,
        "activos": [r for r in fuera if r["activo"]],
        "inactivos": [r for r in fuera if not r["activo"]],
    }
