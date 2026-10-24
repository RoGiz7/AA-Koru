"""
Reclutamiento dentro del Auth.

★ LAS PREGUNTAS SE EDITAN EN EL ADMIN (modelo `RecruitQuestion`), no aquí. La
lista de abajo es solo la semilla con la que nacieron: la migración 0038 las
crea y a partir de ahí mandan las de la base.

⚠ Y POR ESO LA ETIQUETA SE CONGELA CON LA RESPUESTA. Si una ficha solo guardara
la clave, el día que alguien reescriba o borre una pregunta, las solicitudes
viejas se quedarían con respuestas huérfanas: un texto sin saber a qué
contestaba. Se guarda {clave: {etiqueta, valor}} para que una ficha de hace seis
meses siga diciendo qué se le preguntó ENTONCES.

⚠ CADA PREGUNTA CUESTA. El criterio para añadir una es doble: que no se pueda
saber sin preguntar, y que la respuesta cambie una decisión. Por eso no se
pregunta «¿cuánto llevas en EVE?» —la fecha de creación del personaje la
tenemos exacta— pero sí «¿ya estuviste en Rekium?», que también la sabemos: ahí
el valor no está en el dato, está en ver si lo que dice cuadra con el ESI.
"""

import logging

logger = logging.getLogger(__name__)


# La semilla: con esto nacen las preguntas en la migración 0038. Después manda
# el admin, y tocar esta lista ya no cambia nada de lo que hay en producción.
# (clave, etiqueta, tipo, obligatoria, ayuda[, opciones])
PREGUNTAS_INICIALES = [
    ("conociste", "¿Dónde nos conociste?", "texto", True,
     "Un amigo, in-game, YouTube, un anuncio…"),
    ("pais", "¿De qué país eres?", "texto", True,
     "Para saber a qué hora sueles coincidir con las flotas"),
    ("actividades", "¿Qué te gusta hacer en EVE?", "larga", True,
     "PvP, minería, industria, exploración… lo que de verdad disfrutes"),
    ("horario", "¿Cuándo sueles jugar?", "texto", True,
     "Por ejemplo: entre semana de 20 a 23, fines de semana por la tarde"),
    ("estuviste", "¿Ya estuviste en Rekium antes?", "opcion", True,
     "", ["No", "Sí, en Rekium", "Sí, en la Academia", "No estoy seguro"]),
    ("motivo", "¿Por qué quieres entrar en Rekium?", "larga", True,
     "Tómate un momento: esto es lo que más leerá el reclutador"),
]

LARGO_MAX = 2000        # por respuesta; mas que esto no lo lee nadie


def preguntas_activas():
    """Las que hay que enseñar hoy, en su orden."""
    from .models import RecruitQuestion

    return list(RecruitQuestion.objects.filter(activa=True).order_by("orden", "id"))


def limpiar_respuestas(post):
    """
    Saca del POST lo que preguntamos, y solo eso.

    Devuelve (respuestas, errores). Cada respuesta se guarda como
    {clave: {"etiqueta": …, "valor": …}}.

    ⚠ No se guarda ningún campo que no sea una pregunta activa: si alguien añade
    un input al HTML por su cuenta, no entra.
    """
    respuestas, errores = {}, []
    for p in preguntas_activas():
        valor = " ".join(str(post.get(p.clave, "")).split())[:LARGO_MAX]

        if not valor:
            if p.obligatoria:
                errores.append(f"Falta: {p.etiqueta}")
            continue

        if p.tipo == RecruitQuestionTipos.OPCION and valor not in (p.opciones or []):
            # Alguien ha tocado el HTML. No se guarda un valor inventado.
            errores.append(f"«{p.etiqueta}» tiene un valor que no es de la lista")
            continue

        # ★ La etiqueta viaja con la respuesta. Ver el comentario de arriba.
        respuestas[p.clave] = {"etiqueta": p.etiqueta, "valor": valor}

    return respuestas, errores


def para_leer(respuestas):
    """
    Las respuestas en orden y listas para pintar, vengan del formato que vengan.

    ⚠ Aguanta el formato viejo (clave -> texto suelto) por si alguna solicitud
    se guardó antes de congelar las etiquetas. Una ficha que no se puede leer
    porque cambió el formato es una ficha perdida.
    """
    fuera = []
    orden = {p.clave: i for i, p in enumerate(preguntas_activas())}
    for clave, v in (respuestas or {}).items():
        if isinstance(v, dict):
            fuera.append({"clave": clave, "etiqueta": v.get("etiqueta") or clave,
                          "valor": v.get("valor", "")})
        else:
            fuera.append({"clave": clave, "etiqueta": clave, "valor": v})
    fuera.sort(key=lambda x: orden.get(x["clave"], 999))
    return fuera


class RecruitQuestionTipos:
    """Los tipos, aquí para no importar el modelo en todas partes."""
    TEXTO  = "texto"
    LARGA  = "larga"
    OPCION = "opcion"


# ---------------------------------------------------------------------------
# El retrato del piloto
# ---------------------------------------------------------------------------
#
# ★ Todo esto sale de la base del Auth, sin tocar el ESI: corptools ya trae los
# SP y el historial de corps de cada personaje registrado (2354 de 2354 los
# tienen). Asi que el reclutador no espera a nada.
#
# ⚠ PERO corptools rellena en SU ciclo, no cuando alguien se registra. Un
# personaje de hace diez minutos puede no tener SP todavia. Por eso `sp` puede
# venir None y la ficha tiene que decir «aun sin datos de ESI» — enseñar un 0
# se leeria como «cuenta vacia», que es justo lo contrario.
#
# ⚠⚠ OJO CON LOS IDs DE CORPTOOLS, QUE NO SON TODOS IGUALES. Comprobado
# contra produccion el 24/10/2026:
#
#   corptools_characteraudit.character_id   -> PK de EveCharacter  (ec.id)
#   corptools_skilltotals.character_id      -> PK del AUDIT        (characteraudit.id)
#   corptools_corporationhistory.character_id -> PK del AUDIT      (characteraudit.id)
#
# La primera version de este fichero cruzaba skilltotals e historial contra
# ec.id. No fallaba: devolvia los datos DE OTRA PERSONA cuando los numeros
# coincidian. A RoGiz7 le salian 16,4 M de SP y 7 corps que eran de otro
# personaje; los suyos son 657.755 y 4.
#
# ★ Y LA COMPROBACION TIENE QUE SER LA BUENA: que una consulta devuelva filas
# no prueba nada. Hay que mirar que el numero de SieteHierros sea el de
# SieteHierros.

SQL_PERSONAJES = """
SELECT ec.id                AS pk,
       ec.character_id      AS eve_id,
       ec.character_name    AS nombre,
       ec.corporation_id    AS corp_id,
       ec.corporation_name  AS corp,
       ec.alliance_name     AS alianza,
       ec.birthday          AS nacimiento,
       ec.security_status   AS seguridad,
       st.total_sp          AS sp,
       st.unallocated_sp    AS sp_libres,
       cau.last_known_login AS ultimo_login
FROM authentication_characterownership co
JOIN eveonline_evecharacter ec        ON ec.id = co.character_id
LEFT JOIN corptools_characteraudit cau ON cau.character_id = ec.id
LEFT JOIN corptools_skilltotals st     ON st.character_id = cau.id
WHERE co.user_id = %s
ORDER BY ec.character_name
"""

SQL_HISTORIAL = """
SELECT ca.character_id   AS pk,
       ch.corporation_id AS corp_id,
       ch.start_date     AS desde,
       en.name           AS corp
FROM corptools_corporationhistory ch
JOIN corptools_characteraudit ca ON ca.id = ch.character_id
LEFT JOIN corptools_evename en ON en.eve_id = ch.corporation_name_id
WHERE ca.character_id IN %s
ORDER BY ca.character_id, ch.start_date DESC
"""

CUENTA_NUEVA_DIAS = 90      # por debajo de esto, la cuenta es reciente
SALTOS_UN_ANYO    = 4       # corps distintas en 12 meses que ya llaman la atencion


def retrato(user, main_id=0):
    """
    Lo que se ve del piloto en el momento de solicitar.

    Devuelve un dict que se guarda tal cual en `instantanea`: es la foto de lo
    que vimos cuando le aceptamos, y dentro de un año nadie podra sacarla de
    corptools porque corptools refleja el AHORA.
    """
    from datetime import date, timedelta

    from django.db import connection
    from django.utils import timezone

    with connection.cursor() as cur:
        cur.execute(SQL_PERSONAJES, [user.id])
        cols = [c[0] for c in cur.description]
        chars = [dict(zip(cols, f)) for f in cur.fetchall()]

    historial = {}
    if chars:
        pks = tuple(c["pk"] for c in chars)
        with connection.cursor() as cur:
            cur.execute(SQL_HISTORIAL, [pks])
            cols = [c[0] for c in cur.description]
            for fila in cur.fetchall():
                d = dict(zip(cols, fila))
                historial.setdefault(d["pk"], []).append(d)

    hoy = date.today()
    hace_un_anyo = hoy - timedelta(days=365)
    señales = []

    for c in chars:
        c["es_main"] = (c["eve_id"] == main_id)
        c["sin_datos_esi"] = c["sp"] is None
        c["edad_dias"] = (hoy - c["nacimiento"]).days if c["nacimiento"] else None

        corps = historial.get(c["pk"], [])
        c["corps_total"] = len(corps)
        c["corps_12m"] = len({h["corp_id"] for h in corps
                              if h["desde"] and h["desde"].date() >= hace_un_anyo})
        # Solo las cinco ultimas: el reclutador filtra, no audita.
        c["corps_recientes"] = [
            {"corp": h["corp"] or f"#{h['corp_id']}",
             "desde": h["desde"].date().isoformat() if h["desde"] else None}
            for h in corps[:5]]

        if c["edad_dias"] is not None and c["edad_dias"] < CUENTA_NUEVA_DIAS:
            señales.append(f"{c['nombre']}: cuenta creada hace {c['edad_dias']} días")
        if c["corps_12m"] >= SALTOS_UN_ANYO:
            señales.append(f"{c['nombre']}: {c['corps_12m']} corps distintas en 12 meses")
        if c["sin_datos_esi"]:
            señales.append(f"{c['nombre']}: todavía sin datos de ESI")

    # El Discord se congela aqui a proposito: si el usuario desaparece del Auth,
    # esto es lo unico que quedara para cruzar con una conversacion antigua.
    discord = ""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT uid, username FROM discord_discorduser WHERE user_id = %s",
                        [user.id])
            fila = cur.fetchone()
        if fila:
            discord = f"{fila[1]} ({fila[0]})"
    except Exception:
        discord = ""

    return {
        "tomado_en": timezone.now().isoformat(),
        "discord": discord,
        "personajes": [
            {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in c.items()}
            for c in chars],
        "total_personajes": len(chars),
        "sp_total": sum((c["sp"] or 0) for c in chars),
        # ⚠ Son SEÑALES, no un veredicto. El reclutador filtra; si algo huele,
        # para eso esta el boton de abrir auditoria y Asuntos Internos detras.
        "señales": señales,
    }


# ---------------------------------------------------------------------------
# El canal de Discord de la solicitud
# ---------------------------------------------------------------------------

def _miles(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def ficha_discord(solicitud, retrato):
    """
    El texto que se publica en el canal: lo que el reclutador necesita para la
    entrevista, y nada más.

    ⚠ Es un RESUMEN, no una auditoría. Si se llena de datos, el reclutador deja
    de leerlos todos y el filtro empeora. Lo que no está aquí está en la ficha
    de AA, y lo que huele se manda a Asuntos Internos con su botón.
    """
    r = retrato or {}
    lineas = [f"## 🪪 {solicitud.main_character_name}"]

    if r.get("discord"):
        lineas.append(f"**Discord:** {r['discord']}")
    lineas.append(f"**Personajes:** {r.get('total_personajes', 0)} · "
                  f"**SP totales:** {_miles(r.get('sp_total'))}")
    lineas.append("")

    for c in r.get("personajes", []):
        marca = "★ " if c.get("es_main") else "• "
        sp = "sin datos de ESI aún" if c.get("sin_datos_esi") else _miles(c.get("sp")) + " SP"
        edad = f"{c['edad_dias']} días" if c.get("edad_dias") is not None else "edad ?"
        lineas.append(f"{marca}**{c.get('nombre')}** — {sp} · cuenta de {edad} · "
                      f"{c.get('corp') or '?'} · {c.get('corps_total', 0)} corps")

    if r.get("señales"):
        lineas.append("")
        lineas.append("**⚠ A tener en cuenta**")
        for s in r["señales"]:
            lineas.append(f"- {s}")

    lineas.append("")
    lineas.append("**📝 Lo que nos ha contado**")
    for item in para_leer(solicitud.respuestas):
        lineas.append(f"**{item['etiqueta']}**")
        lineas.append(item["valor"] or "—")
        lineas.append("")

    return "\n".join(lineas)


def crear_canal(solicitud, retrato):
    """
    Abre el canal privado del solicitante y publica su ficha.

    Devuelve el id del canal. Lanza ValueError con un motivo legible si falta
    configuración: quien llama lo guarda en `discord_error` y la solicitud sigue
    viva — el reclutador la ve igual, solo que marcada como «sin canal».
    """
    from .models import RecruitConfig
    from . import discordapi

    cfg = RecruitConfig.objects.filter(tag="default").first()
    if not cfg or not cfg.activo:
        raise ValueError("El reclutamiento por Discord está apagado en la configuración")
    if not cfg.categoria_id:
        raise ValueError("Falta la categoría de Discord en la configuración de reclutamiento")

    nombre = discordapi.nombre_canal(cfg.prefijo_canal, solicitud.main_character_name)

    # El uid del solicitante sale del retrato, que lo guardó como «nombre (uid)».
    uid = ""
    bruto = (retrato or {}).get("discord") or ""
    if "(" in bruto and bruto.rstrip().endswith(")"):
        uid = bruto.rsplit("(", 1)[1].rstrip(")").strip()

    canal = discordapi.crear_canal(
        nombre, cfg.categoria_id, roles_ver=cfg.roles_ver or [], uid_invitado=uid)

    # ★ Si el canal se crea pero el mensaje falla, el canal NO se pierde: se
    # devuelve igual y el fallo se anota. Un canal vacío es recuperable; uno
    # que no sabemos que existe, no.
    try:
        discordapi.publicar(canal, ficha_discord(solicitud, retrato))
    except Exception as exc:
        logger.error("koru recruit: canal %s creado pero sin ficha: %s", canal, exc)

    return canal
