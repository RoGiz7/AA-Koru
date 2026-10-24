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
    # ★ Los comandos, en el propio mensaje. Un comando que nadie sabe que
    # existe es un comando que no existe.
    lineas.append("*Desde aquí: `/recluta estado` · `/recluta entrevista` · "
                  "`/recluta ok` · `/recluta invitacion`*")
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
    bruto = (retrato or {}).get("discord") or ""
    uid = bruto.rsplit("(", 1)[1].rstrip(")").strip() if (
        "(" in bruto and bruto.rstrip().endswith(")")) else ""

    canal = discordapi.crear_canal(
        nombre, cfg.categoria_id, roles_ver=cfg.roles_ver or [], uid_invitado=uid)

    # ⚠ LA MENCIÓN ES LO QUE HACE QUE ESTO EXISTA PARA ALGUIEN. Un canal
    # privado recién creado aparece en la lista de Discord y ya está: ni al
    # piloto ni a los reclutadores les salta nada. Sin ping, el canal se queda
    # ahí sin que nadie lo abra.
    saludo = ""
    if cfg.rol_avisar:
        saludo += f"<@&{cfg.rol_avisar}> "
    if uid:
        saludo += f"<@{uid}> "
    if saludo:
        saludo = saludo.strip() + "\n\n"

    # ★ Si el canal se crea pero el mensaje falla, el canal NO se pierde: se
    # devuelve igual y el fallo se anota. Un canal vacío es recuperable; uno
    # que no sabemos que existe, no.
    try:
        discordapi.publicar(canal, saludo + ficha_discord(solicitud, retrato))
    except Exception as exc:
        logger.error("koru recruit: canal %s creado pero sin ficha: %s", canal, exc)

    # Y un aviso en el canal general, si está configurado: el que no tenga el
    # canal privado a la vista se entera igual de que ha entrado alguien.
    if cfg.avisar_en:
        try:
            discordapi.publicar(
                cfg.avisar_en,
                (f"<@&{cfg.rol_avisar}> " if cfg.rol_avisar else "")
                + f"📥 **Solicitud nueva** de **{solicitud.main_character_name}** "
                  f"— <#{canal}>")
        except Exception as exc:
            logger.warning("koru recruit: no se pudo avisar en %s: %s", cfg.avisar_en, exc)

    return canal


# ---------------------------------------------------------------------------
# Quién puede dar cada paso
# ---------------------------------------------------------------------------

PASOS = {
    "reclutadores": ("grupos_reclutadores", "el OK de reclutadores"),
    "asuntos":      ("grupos_asuntos",      "el OK de Asuntos Internos"),
    "directores":   ("grupos_directores",   "el OK de Dirección"),
    "invitacion":   ("grupos_invitacion",   "marcar la invitación como enviada"),
    "rechazo":      ("grupos_rechazo",      "rechazar o cerrar una solicitud"),
}

# A quién se avisa cuando se completa cada paso: le toca al siguiente.
# ⚠ Dar un OK y que nadie se entere de que ahora le toca a otro es como no
# darlo: la solicitud se queda esperando a alguien que no sabe que la espera.
SIGUIENTE_ROL = {
    "reclutadores": "rol_asuntos",
    "asuntos":      "rol_directores",
    "directores":   "rol_invitacion",
}


def quien_puede(paso):
    """Los nombres de los grupos que pueden dar ese paso. Vacío = sin configurar."""
    from .models import RecruitConfig

    campo = PASOS.get(paso, (None, None))[0]
    if not campo:
        return []
    cfg = RecruitConfig.objects.filter(tag="default").first()
    if not cfg:
        return []
    return list(getattr(cfg, campo).values_list("name", flat=True))


def puede(user, paso):
    """
    (sí/no, motivo). El motivo se enseña tal cual cuando es que no.

    ⚠ Lista vacía = SIN CONFIGURAR, y entonces solo un superusuario. No
    significa «todos»: un paso sin definir que pueda darlo cualquiera es
    exactamente el descuido que no se nota hasta que alguien aprueba algo que
    no le tocaba.
    """
    if not user.is_authenticated:
        return False, "Hay que entrar primero."
    if user.is_superuser:
        return True, ""

    # ★ La invitacion tiene DOS caminos: el rol in-game o el grupo de AA.
    # El primero es el que manda de verdad; el segundo es el respaldo para
    # cuando el dato de corptools no esta.
    if paso == "invitacion" and tiene_rol_invitar(user):
        return True, ""

    grupos = quien_puede(paso)
    if not grupos:
        _, que = PASOS.get(paso, ("", "este paso"))
        if paso == "invitacion":
            return False, ("Para marcar la invitación hace falta el rol de "
                           "Personnel Manager o Director en una corp de Rekium.")
        return False, (f"Todavía no está configurado quién puede dar {que}. "
                       "Dilo en la configuración de reclutamiento del admin.")

    mios = set(user.groups.values_list("name", flat=True))
    if mios & set(grupos):
        return True, ""

    _, que = PASOS[paso]
    if paso == "invitacion":
        return False, ("Para marcar la invitación hace falta el rol de "
                       "Personnel Manager o Director en una corp de Rekium, "
                       "o estar en: " + " o ".join(grupos) + ".")
    return False, (f"No puedes dar {que}: eso lo hace "
                   + " o ".join(grupos) + ". Avísales y lo darán ellos.")


def lee_reservadas(user):
    """
    ¿Puede leer —y escribir— notas reservadas?

    Quien da el paso de Asuntos Internos o el de Dirección. Se deriva de la
    misma configuración que la cadena: un sitio donde decidirlo, no dos.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    mios = set(user.groups.values_list("name", flat=True))
    permitidos = set(quien_puede("asuntos")) | set(quien_puede("directores"))
    return bool(mios & permitidos)


# ---------------------------------------------------------------------------
# Guardar la conversación antes de que desaparezca
# ---------------------------------------------------------------------------

def transcribir(canal_id):
    """
    La conversación de un canal, en el MISMO formato que guardaba el bot viejo:

        [24/10/2026, 12:47:31] Fulano: lo que dijo

    ★ Se usa ese formato a propósito: el visor de conversaciones que ya tiene
    Koru lo entiende, así que una solicitud archivada se lee igual que un
    ticket antiguo sin escribir nada nuevo.
    """
    from datetime import datetime

    from . import discordapi

    lineas = []
    for cuando, autor, texto, adjuntos in discordapi.leer_canal(canal_id):
        try:
            t = datetime.fromisoformat(str(cuando).replace("Z", "+00:00"))
            sello = t.strftime("%d/%m/%Y, %H:%M:%S")
        except (ValueError, TypeError):
            sello = str(cuando)
        cuerpo = texto or ""
        for nombre in adjuntos:
            # ⚠ Solo el NOMBRE del adjunto. El enlace de Discord caduca a las
            # pocas horas, así que guardarlo sería guardar un enlace muerto y
            # hacer creer que el fichero está.
            cuerpo += f" [ADJUNTO: {nombre}]"
        lineas.append(f"[{sello}] {autor}: {cuerpo}".rstrip())

    return "\n".join(lineas)


def uid_piloto(solicitud):
    """El id de Discord del solicitante, para mencionarle. Vacío si no lo hay."""
    bruto = (solicitud.instantanea or {}).get("discord") or ""
    if "(" in bruto and bruto.rstrip().endswith(")"):
        return bruto.rsplit("(", 1)[1].rstrip(")").strip()
    return ""


def archivar_canal(solicitud):
    """
    Guarda la conversación en la solicitud y luego borra el canal.

    ⚠ EL ORDEN IMPORTA Y NO ES NEGOCIABLE: si el guardado falla, el canal NO se
    borra. Una conversación perdida no se recupera; un canal de más se borra a
    mano en diez segundos.
    """
    from django.utils import timezone

    from . import discordapi

    if not solicitud.discord_channel_id:
        return "sin canal"

    texto = transcribir(solicitud.discord_channel_id)
    solicitud.transcripcion = texto
    solicitud.transcrita_en = timezone.now()
    solicitud.save(update_fields=["transcripcion", "transcrita_en", "updated_at"])

    discordapi.borrar_canal(solicitud.discord_channel_id)
    solicitud.discord_channel_id = ""
    solicitud.save(update_fields=["discord_channel_id", "updated_at"])
    return f"{len(texto)} caracteres guardados"


# ---------------------------------------------------------------------------
# Quién puede invitar de verdad
# ---------------------------------------------------------------------------
#
# ★ EL ROL IN-GAME MANDA MÁS QUE UNA LISTA. A quién puede invitar a la corp lo
# decide el CEO dentro del juego, no una casilla del admin. Si lo sacamos de
# ahí, la lista se mantiene sola: el día que alguien deja de ser Personnel
# Manager, deja de poder marcar invitaciones sin que nadie toque nada.
#
# ⚠ PERO EL ROL ES POR CORP. En la base hay 258 personnel managers, y muchos
# son alts de nuestros miembros en corps ajenas —«The Dark Techno Club», «La
# Forja»…—. Mandar en otra corp no da derecho a invitar a la nuestra, así que
# hay que exigir las dos cosas: el rol Y estar en una corp rastreada.
#
# ⚠ Y los ids de corptools otra vez: `characterroles.character_id` es el PK del
# AUDIT, no el de EveCharacter. Comprobado contra producción, igual que pasaba
# con los SP y el historial.

SQL_PUEDE_INVITAR = """
SELECT 1
FROM authentication_characterownership co
JOIN eveonline_evecharacter ec      ON ec.id = co.character_id
JOIN corptools_characteraudit ca    ON ca.character_id = ec.id
JOIN corptools_characterroles cr    ON cr.character_id = ca.id
JOIN koru_stats_trackedcorporation tc
       ON tc.corporation_id = ec.corporation_id AND tc.is_active = 1
WHERE co.user_id = %s
  AND (cr.personnel_manager = 1 OR cr.director = 1)
LIMIT 1
"""


def tiene_rol_invitar(user):
    """¿Alguno de sus personajes puede invitar a una corp nuestra, in-game?"""
    from django.db import connection

    if not user.is_authenticated:
        return False
    try:
        with connection.cursor() as cur:
            cur.execute(SQL_PUEDE_INVITAR, [user.id])
            return cur.fetchone() is not None
    except Exception as exc:
        # Si corptools no tiene el dato, no se bloquea a nadie: se cae a los
        # grupos de AA, que es el respaldo.
        logger.warning("koru recruit: no se pudo mirar el rol in-game: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Las acciones, en un solo sitio
# ---------------------------------------------------------------------------
#
# ★ AQUI VIVE LA LOGICA, Y LA LLAMAN LOS DOS: la pantalla web y el cog de
# Discord. Si cada uno tuviera la suya, se desincronizarian en la primera
# modificacion — y entonces aprobar desde Discord y aprobar desde la web harian
# cosas distintas sin que nadie se diera cuenta.
#
# Todas devuelven (ok, mensaje). El mensaje se enseña tal cual: en la web como
# aviso, en Discord como respuesta efimera.

def _nombre(user):
    """El main de quien actúa, para dejarlo escrito."""
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute(
            "SELECT mc.character_name FROM authentication_userprofile up "
            "JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id "
            "WHERE up.user_id = %s", [user.id])
        fila = cur.fetchone()
    return (fila[0] if fila else "") or str(user)


def exige_entrevista():
    from .models import RecruitConfig

    cfg = RecruitConfig.objects.filter(tag="default").first()
    return bool(cfg and cfg.exigir_entrevista)


def marcar_entrevista(sol, user, nota=""):
    from django.utils import timezone

    from .models import RecruitNote

    ok, motivo = puede(user, "reclutadores")
    if not ok:
        return False, motivo
    if sol.entrevista_en:
        return False, "La entrevista ya estaba marcada."

    quien = _nombre(user)
    nota = (nota or "").strip()[:5000]
    sol.entrevista_por, sol.entrevista_en = user, timezone.now()
    sol.entrevista_nota = nota
    sol.save(update_fields=["entrevista_por", "entrevista_en",
                            "entrevista_nota", "updated_at"])
    if nota:
        # ★ Lo que salió de la entrevista va a las notas del staff, no escondido
        # en un campo: es lo que el siguiente de la cadena necesita leer.
        RecruitNote.objects.create(solicitud=sol, autor=user,
                                   autor_nombre=quien, texto="Entrevista: " + nota)
    return True, f"Entrevista marcada por {quien}."


def aprobar(sol, user, paso):
    from django.utils import timezone

    ok, motivo = puede(user, paso)
    if not ok:
        return False, motivo
    if paso == "reclutadores" and not sol.entrevista_en and exige_entrevista():
        # ⚠ Un «aprobado» sin que conste que alguien habló con la persona no
        # cuenta lo que pasó.
        return False, ("Antes de dar el OK hay que marcar la entrevista. Si se "
                       "aprobó sin hablar con nadie, eso también hay que poder contarlo.")
    if paso == "asuntos":
        faltan = checks_pendientes(sol)
        if faltan:
            # ⚠ Mismo motivo que la entrevista: quien lleva veinte auditorias
            # da por hecho que miro algo que no miro. El sistema es el unico
            # que se acuerda. Un punto que no aplica se marca «No aplica»,
            # que tambien es una respuesta — lo que no vale es el silencio.
            return False, ("Falta por mirar: " + ", ".join(faltan) +
                           ". Si alguno no aplica, márcalo como «No aplica».")
    if paso != sol.fase:
        return False, f"Ahora toca «{sol.fase}», no «{paso}»."

    quien = _nombre(user)
    setattr(sol, f"ok_{paso}_por", user)
    setattr(sol, f"ok_{paso}_en", timezone.now())
    if sol.estado == sol.NUEVO:
        sol.estado = sol.EN_CURSO
    sol.save()
    return True, f"Paso «{paso}» aprobado por {quien}."


def checks_de(sol):
    """
    La checklist de la solicitud: puntos activos, con lo que ya se marcó.

    Los automáticos llegan con su valor calculado al vuelo; los que ya tienen
    un marcado guardado enseñan **el valor congelado de entonces**, no el de
    hoy. corptools se actualiza solo, y una auditoría tiene que poder explicar
    qué se vio cuando se decidió.
    """
    from .models import AuditCheck, RecruitCheck
    from . import auditoria

    puntos = list(AuditCheck.objects.filter(activo=True))
    hechos = {c.clave: c for c in RecruitCheck.objects.filter(solicitud=sol)}

    # Solo se calcula si hay algún punto automático sin marcar: una consulta a
    # corptools por cada visita a una ficha ya cerrada no la necesita nadie.
    hace_falta = any(p.fuente and (p.clave not in hechos or
                                   hechos[p.clave].estado == RecruitCheck.PENDIENTE)
                     for p in puntos)
    auto = auditoria.calcular(sol.user) if (hace_falta and sol.user) else {}

    main_id = 0
    for p in (sol.instantanea or {}).get("personajes", []):
        if p.get("es_main"):
            main_id = p.get("eve_id") or 0

    fuera = []
    for p in puntos:
        hecho = hechos.get(p.clave)
        calculado = auto.get(p.fuente) if p.fuente else None
        fuera.append({
            "clave": p.clave,
            "etiqueta": p.etiqueta,
            "ayuda": p.ayuda,
            "obligatorio": p.obligatorio,
            "automatico": bool(p.fuente),
            "enlace": auditoria.enlace_de(p.enlace, sol.main_character_name, main_id),
            "estado": hecho.estado if hecho else RecruitCheck.PENDIENTE,
            "nota": hecho.nota if hecho else "",
            "por": hecho.por_nombre if hecho else "",
            "en": hecho.en if hecho else None,
            # El congelado manda sobre el calculado en cuanto existe.
            "valor": (hecho.valor if (hecho and hecho.valor)
                      else (calculado or {}).get("valor", "")),
            "detalle": [] if (hecho and hecho.valor) else (calculado or {}).get("detalle", []),
            "congelado": bool(hecho and hecho.valor),
        })
    return fuera


def checks_pendientes(sol):
    """Las etiquetas de los puntos obligatorios que nadie ha mirado."""
    from .models import AuditCheck, RecruitCheck

    hechos = {c.clave: c.estado for c in RecruitCheck.objects.filter(solicitud=sol)}
    return [p.etiqueta for p in AuditCheck.objects.filter(activo=True, obligatorio=True)
            if hechos.get(p.clave, RecruitCheck.PENDIENTE) in RecruitCheck.SIN_RESOLVER]


def marcar_check(sol, user, clave, estado, nota=""):
    """
    Deja constancia de cómo quedó un punto de la auditoría.

    ★ Se congela el valor que se vio y quién lo vio. El bug de identidad de
    W4b —checks estampados con el nombre del CEO en vez del que pulsaba—
    aquí no puede pasar: quien lo marca es quien está logueado.
    """
    from django.utils import timezone

    from .models import AuditCheck, RecruitCheck
    from . import auditoria

    ok, motivo = puede(user, "asuntos")
    if not ok:
        return False, motivo

    punto = AuditCheck.objects.filter(clave=clave, activo=True).first()
    if not punto:
        return False, "Ese punto de auditoría no existe o está desactivado."
    if estado not in dict(RecruitCheck.ESTADOS):
        return False, "Ese no es un estado válido."
    if estado in (RecruitCheck.DUDA, RecruitCheck.PROBLEMA) and not (nota or "").strip():
        # ⚠ Una duda sin explicar no le sirve a Dirección, que es quien la lee
        # para decidir. «Algo no me cuadra» es exactamente lo que hay que
        # escribir, y basta.
        return False, "Una duda o un problema necesitan una línea explicando qué viste."

    valor = ""
    if punto.fuente:
        calc = auditoria.calcular(sol.user) if sol.user else {}
        valor = (calc.get(punto.fuente) or {}).get("valor", "")

    RecruitCheck.objects.update_or_create(
        solicitud=sol, clave=clave,
        defaults={"etiqueta": punto.etiqueta, "estado": estado,
                  "nota": (nota or "").strip()[:5000], "valor": valor,
                  "por": user, "por_nombre": _nombre(user), "en": timezone.now()},
    )
    return True, f"«{punto.etiqueta}» marcado como {dict(RecruitCheck.ESTADOS)[estado].lower()}."


def marcar_invitacion(sol, user):
    from django.utils import timezone

    ok, motivo = puede(user, "invitacion")
    if not ok:
        return False, motivo
    if not sol.ok_directores_en:
        return False, "Todavía falta el OK de Dirección."
    if sol.invitacion_en:
        return False, "Ya estaba marcada como enviada."

    quien = _nombre(user)
    sol.invitacion_por, sol.invitacion_en = user, timezone.now()
    sol.save(update_fields=["invitacion_por", "invitacion_en", "updated_at"])
    return True, f"Invitación marcada por {quien}."


def cerrar(sol, user, estado, motivo_texto):
    from django.utils import timezone

    ok, motivo = puede(user, "rechazo")
    if not ok:
        return False, motivo
    if estado not in sol.CERRADOS:
        return False, "Ese no es un estado de cierre."

    texto = (motivo_texto or "").strip()
    if not texto:
        # ★ Obligatorio: una solicitud cerrada sin explicación no le sirve a
        # nadie dentro de seis meses, que es justo cuando se consulta.
        return False, "Pon un motivo: es lo que queda escrito en el expediente."

    sol.estado = estado
    sol.motivo_cierre = texto[:2000]
    sol.cerrada_por = user
    sol.fecha_cierre = timezone.now()
    sol.save()
    return True, f"Cerrada como «{sol.get_estado_display()}» por {_nombre(user)}."


def usuario_de_discord(uid):
    """
    El usuario de AA que hay detrás de un id de Discord. None si no lo hay.

    ⚠ Esto es lo que hace que el cog no tenga que mapear roles de Discord a
    permisos: la persona que pulsa ES un usuario del Auth, con sus grupos.
    """
    from django.contrib.auth.models import User
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("SELECT user_id FROM discord_discorduser WHERE uid = %s", [str(uid)])
        fila = cur.fetchone()
    return User.objects.filter(id=fila[0]).first() if fila else None
