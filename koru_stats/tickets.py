"""
El motor de tickets dentro del AA: Directores, IT y Soporte.

★ UN MOTOR, NO TRES. En n8n eran D1–D3b, IT1/IT1b y los de Soporte, y hacían
lo mismo con otro nombre: abrir un canal privado, que alguien lo coja, cerrarlo
con la conversación guardada. Aquí es una sola pieza y lo que cambia entre
tipos vive en `TicketTipoConfig`, editable en el admin.

★ EL TICKET NACE EN LA WEB, NO EN DISCORD. El botón de Discord es un enlace: no
lo atiende el bot. Así el AA sabe QUIÉN abre cada ticket antes de crearlo —en
Baserow 282 de 353 tickets de Directores no tenían ni estado, y el «Usuario
Discord» llegaba vacío siempre— y quien no tiene permiso no puede abrir nada
por mucho que pulse el botón.

⚠ Las mismas reglas que el reclutamiento:
  · el canal se crea EN SEGUNDO PLANO: si Discord falla, el ticket ya existe;
  · cerrar no borra el canal: se borra 24 h después, con la conversación
    guardada ANTES de borrarlo;
  · quién lo cogió, quién lo cerró y cuándo, cada cosa en su columna.
"""

import logging

from django.db import connection

logger = logging.getLogger(__name__)

# Qué tipos gestiona cada permiso. Es el MISMO reparto que ya usa la lista de
# tickets del espejo de Baserow: la gente que veía los tickets viejos de un
# tipo ve los nuevos, sin tocar grupos.
PERMISO_TIPOS = {
    # ★ Dirección ve también las auditorías: es quien decide con ellas, igual
    # que en el reclutamiento («solo Asuntos Internos y Dirección»).
    "koru_stats.tickets_directores": {"directores", "asuntos"},
    "koru_stats.tickets_asuntos_internos": {"asuntos"},
    "koru_stats.tickets_it": {"it", "soporte"},
    # ★ Los ayudantes atienden Soporte y nada más: IT tiene las llaves de todo.
    "koru_stats.tickets_soporte": {"soporte"},
}

PREFIJO_NUMERO = {"directores": "D", "it": "IT", "soporte": "S", "asuntos": "AI"}


def config(tipo):
    from .models import TicketTipoConfig
    return TicketTipoConfig.objects.filter(tipo=tipo).first()


def tipos_que_gestiona(user):
    """Los tipos de ticket que este usuario puede ver y llevar."""
    if not user.is_authenticated:
        return set()
    if user.is_superuser or user.has_perm("koru_stats.tickets_admin"):
        return {"directores", "it", "soporte", "asuntos"}
    fuera = set()
    for perm, tipos in PERMISO_TIPOS.items():
        if user.has_perm(perm):
            fuera |= tipos
    return fuera


def puede_archivar_ya(user):
    """
    Borrar el canal sin esperar las 24 h. Solo CEO, Directores y Rekium TI.

    ⚠ Los ayudantes de Soporte (`tickets_soporte`) NO: las 24 h son la red de
    seguridad para que el piloto lea el cierre, y saltársela es una decisión
    de quien manda, no de quien atiende.
    """
    if not user.is_authenticated:
        return False
    return user.is_superuser or any(user.has_perm(p) for p in (
        "koru_stats.tickets_admin", "koru_stats.tickets_directores", "koru_stats.tickets_it"))


def main_de(user):
    """(character_id, nombre) del main, o (None, "") si no tiene."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT mc.character_id, mc.character_name FROM authentication_userprofile up "
            "JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id "
            "WHERE up.user_id = %s", [user.id])
        fila = cur.fetchone()
    return (int(fila[0]), fila[1] or "") if fila else (None, "")


def uid_discord(user):
    """El id de Discord vinculado en el Auth. Vacío si no lo tiene."""
    with connection.cursor() as cur:
        cur.execute("SELECT uid FROM discord_discorduser WHERE user_id = %s", [user.id])
        fila = cur.fetchone()
    return str(fila[0]) if fila and fila[0] else ""


def puede_abrir(user, tipo):
    """
    (sí/no, motivo). El motivo se enseña tal cual: «no puedes» sin decir por
    qué hace que la gente vuelva a Discord a preguntar.
    """
    if tipo == "asuntos":
        # ⚠ Una auditoría no la pide el auditado: la abre el staff desde la
        # ficha del piloto o desde un ticket de Directores.
        return False, "Las auditorías las abre el staff, no se piden desde aquí."
    cfg = config(tipo)
    if not cfg or not cfg.activo:
        return False, "Este tipo de ticket todavía no se abre desde aquí."
    if not user.is_authenticated:
        return False, "Tienes que entrar en el Auth."
    mid, _ = main_de(user)
    if not mid:
        return False, "Primero tienes que elegir tu personaje principal en el Auth."
    # ★ «Solo miembros» se mide con el mismo permiso que da acceso a Mi
    # Dashboard, que es el que tienen Miembros y Academy. Un sitio donde
    # decidir quién es de la casa, no dos.
    if cfg.solo_miembros and not (user.is_superuser or user.has_perm("koru_stats.basic_access")):
        return False, "Este tipo de ticket es solo para miembros de Rekium."
    # ★ Freno al spam: quien quiera entorpecer no puede abrir veinte canales.
    from .models import KoruTicket
    abiertos = (KoruTicket.objects.filter(user=user, tipo=tipo)
                .exclude(estado__in=KoruTicket.CERRADOS).count())
    if cfg.max_abiertos and abiertos >= cfg.max_abiertos:
        return False, (f"Ya tienes {abiertos} ticket(s) abierto(s) de este tipo. "
                       "Cuando se cierre alguno podrás abrir otro.")
    return True, ""


def numero(ticket):
    return f"{PREFIJO_NUMERO.get(ticket.tipo, 'T')}-{ticket.id}"


def ficha_discord(ticket):
    """El primer mensaje del canal: quién, qué y dónde gestionarlo."""
    from django.conf import settings
    from django.urls import reverse

    base = str(getattr(settings, "SITE_URL", "") or "").rstrip("/")
    enlace = base + reverse("koru_stats:koruticket_ficha", args=[ticket.id])
    if ticket.tipo == "asuntos":
        ficha_aud = base + reverse("koru_stats:auditor_pilot", args=[ticket.main_character_id])
        return "\n".join([
            f"🔎 **{numero(ticket)} · Auditoría de {ticket.main_character_name}**",
            f"**Abierta por:** {_nombre(ticket.abierto_por)}",
            "",
            ticket.descripcion or "",
            "",
            f"Checklist y cierre: <{enlace}>",
            f"Ficha del Auditor: <{ficha_aud}>",
        ])
    lineas = [
        f"🎫 **{numero(ticket)} · {ticket.get_tipo_display()}**"
        + (f" — {ticket.categoria}" if ticket.categoria else ""),
        f"**De:** {ticket.main_character_name}",
        f"**Asunto:** {ticket.asunto}",
        "",
        ticket.descripcion or "",
        "",
        f"Gestión en el Auth: <{enlace}>",
    ]
    return "\n".join(lineas)


def crear_canal(ticket):
    """
    Abre el canal privado del ticket y publica la ficha. Devuelve el id.

    Lanza ValueError con un motivo legible si falta configuración: quien llama
    lo guarda en `discord_error` y el ticket sigue vivo.
    """
    from . import discordapi

    cfg = config(ticket.tipo)
    if not cfg or not cfg.categoria_id:
        raise ValueError("Falta la categoría de Discord en la configuración de este tipo")

    nombre = discordapi.nombre_canal(cfg.prefijo_canal,
                                     f"{ticket.id}-{ticket.main_character_name}")
    uid = ticket.discord_uid if cfg.invitar_piloto else ""
    canal = discordapi.crear_canal(nombre, cfg.categoria_id,
                                   roles_ver=cfg.roles_ver or [], uid_invitado=uid)

    # ⚠ Sin mención el canal aparece en la lista y nadie lo abre.
    saludo = ""
    if cfg.rol_avisar:
        saludo += f"<@&{cfg.rol_avisar}> "
    if uid:
        saludo += f"<@{uid}> "
    try:
        discordapi.publicar(canal, (saludo.strip() + "\n\n" if saludo else "") + ficha_discord(ticket))
    except Exception as exc:
        logger.error("koru tickets: canal %s creado pero sin ficha: %s", canal, exc)

    if cfg.avisar_en:
        try:
            discordapi.publicar(
                cfg.avisar_en,
                (f"<@&{cfg.rol_avisar}> " if cfg.rol_avisar else "")
                + f"🎫 **{numero(ticket)}** de **{ticket.main_character_name}**: "
                  f"{ticket.asunto} — <#{canal}>")
        except Exception as exc:
            logger.warning("koru tickets: no se pudo avisar en %s: %s", cfg.avisar_en, exc)
    return canal


def avisar(ticket, texto):
    """Una línea en el canal del ticket. Nunca revienta la acción que la provoca."""
    from . import discordapi

    if not ticket.discord_channel_id:
        return
    try:
        discordapi.publicar(ticket.discord_channel_id, texto)
    except Exception as exc:
        logger.warning("koru tickets: aviso en %s falló: %s", ticket.discord_channel_id, exc)


def archivar_canal(ticket):
    """
    Guarda la conversación y luego borra el canal.

    ⚠ Si el guardado falla, el canal NO se borra: una conversación perdida no
    se recupera; un canal de más se borra a mano.
    """
    from django.utils import timezone

    from . import discordapi
    from .recruit import transcribir

    if not ticket.discord_channel_id:
        return "sin canal"
    texto = transcribir(ticket.discord_channel_id)
    ticket.transcripcion = texto
    ticket.transcrita_en = timezone.now()
    ticket.save(update_fields=["transcripcion", "transcrita_en", "updated_at"])

    discordapi.borrar_canal(ticket.discord_channel_id)
    ticket.discord_channel_id = ""
    ticket.save(update_fields=["discord_channel_id", "updated_at"])
    return f"{len(texto)} caracteres guardados"


# ---------------------------------------------------------------------------
# Auditorías de Asuntos Internos (0.56)
# ---------------------------------------------------------------------------

def _nombre(user):
    if not user:
        return "—"
    with connection.cursor() as cur:
        cur.execute(
            "SELECT mc.character_name FROM authentication_userprofile up "
            "JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id "
            "WHERE up.user_id = %s", [user.id])
        fila = cur.fetchone()
    return (fila[0] if fila else "") or str(user)


def puede_auditar(user):
    """Abrir una auditoría: Asuntos Internos, Dirección y CEO. Con el tipo encendido."""
    cfg = config("asuntos")
    if not cfg or not cfg.activo or not user.is_authenticated:
        return False
    return user.is_superuser or any(user.has_perm(p) for p in (
        "koru_stats.tickets_admin", "koru_stats.tickets_asuntos_internos",
        "koru_stats.tickets_directores"))


def _usuario_de(main_id):
    """(User, nombre) del dueño de ese personaje, o (None, nombre) si no está en el Auth."""
    from django.contrib.auth.models import User
    with connection.cursor() as cur:
        cur.execute(
            "SELECT co.user_id, ec.character_name FROM eveonline_evecharacter ec "
            "LEFT JOIN authentication_characterownership co ON co.character_id = ec.id "
            "WHERE ec.character_id = %s", [main_id])
        fila = cur.fetchone()
    if not fila:
        return None, ""
    return (User.objects.filter(id=fila[0]).first() if fila[0] else None), (fila[1] or "")


def abrir_auditoria(main_id, motivo, user, relacionado=None, riesgo=None):
    """
    Abre (o devuelve la que ya hay abierta) la auditoría de un piloto.

    ★ Una abierta por piloto: dos auditorías a la vez sobre la misma persona
    son dos auditores haciendo lo mismo sin saberlo.
    Devuelve (ticket, creada). (None, False) si el piloto no existe.
    """
    from django.db import transaction

    from .models import KoruTicket
    from .tasks import tickets_preparar

    ya = (KoruTicket.objects.filter(tipo="asuntos", main_character_id=main_id)
          .exclude(estado__in=KoruTicket.CERRADOS).first())
    if ya:
        return ya, False

    piloto, nombre = _usuario_de(main_id)
    if not nombre:
        return None, False

    texto = (motivo or "").strip()
    if riesgo:
        texto += f"\n\nRiesgo en el Auditor al abrirla: {riesgo}"
    if relacionado is not None:
        texto += f"\n\nViene del ticket {numero(relacionado)}: {relacionado.asunto}"

    t = KoruTicket.objects.create(
        tipo="asuntos", user=piloto, main_character_id=main_id, main_character_name=nombre,
        discord_uid="", asunto=f"Auditoría de {nombre}", descripcion=texto[:5000],
        abierto_por=user, relacionado=relacionado)
    transaction.on_commit(lambda: tickets_preparar.delay(t.id))
    return t, True


def checks_de(ticket):
    """La checklist de la auditoría: puntos activos con lo ya marcado (congelado) o lo calculado."""
    from .models import AuditCheck, RecruitCheck, TicketCheck
    from . import auditoria

    puntos = list(AuditCheck.objects.filter(activo=True))
    hechos = {c.clave: c for c in TicketCheck.objects.filter(ticket=ticket)}
    hace_falta = any(p.fuente and (p.clave not in hechos or hechos[p.clave].estado == RecruitCheck.PENDIENTE)
                     for p in puntos)
    auto = auditoria.calcular(ticket.user) if (hace_falta and ticket.user) else {}

    fuera = []
    for p in puntos:
        h = hechos.get(p.clave)
        calc = auto.get(p.fuente) if p.fuente else None
        fuera.append({
            "clave": p.clave, "etiqueta": p.etiqueta, "ayuda": p.ayuda,
            "obligatorio": p.obligatorio, "automatico": bool(p.fuente),
            "enlace": auditoria.enlace_de(p.enlace, ticket.main_character_name, ticket.main_character_id),
            "estado": h.estado if h else RecruitCheck.PENDIENTE,
            "estado_txt": dict(RecruitCheck.ESTADOS)[h.estado if h else RecruitCheck.PENDIENTE],
            "nota": h.nota if h else "", "por": h.por_nombre if h else "", "en": h.en if h else None,
            "valor": (h.valor if (h and h.valor) else (calc or {}).get("valor", "")),
            "detalle": [] if (h and h.valor) else (calc or {}).get("detalle", []),
            "congelado": bool(h and h.valor),
        })
    return fuera


def checks_pendientes(ticket):
    from .models import AuditCheck, RecruitCheck, TicketCheck
    hechos = {c.clave: c.estado for c in TicketCheck.objects.filter(ticket=ticket)}
    return [p.etiqueta for p in AuditCheck.objects.filter(activo=True, obligatorio=True)
            if hechos.get(p.clave, RecruitCheck.PENDIENTE) in RecruitCheck.SIN_RESOLVER]


def marcar_check(ticket, user, clave, estado, nota=""):
    """Marca un punto. Quien marca es quien está logueado: el bug de W4b aquí no puede pasar."""
    from django.utils import timezone

    from .models import AuditCheck, RecruitCheck, TicketCheck
    from . import auditoria

    if "asuntos" not in tipos_que_gestiona(user):
        return False, "Marcar la auditoría es cosa de Asuntos Internos o Dirección."
    punto = AuditCheck.objects.filter(clave=clave, activo=True).first()
    if not punto:
        return False, "Ese punto de auditoría no existe o está desactivado."
    if estado not in dict(RecruitCheck.ESTADOS):
        return False, "Ese no es un estado válido."
    if estado in (RecruitCheck.DUDA, RecruitCheck.PROBLEMA) and not (nota or "").strip():
        return False, "Una duda o un problema necesitan una línea explicando qué viste."
    valor = ""
    if punto.fuente and ticket.user:
        valor = (auditoria.calcular(ticket.user).get(punto.fuente) or {}).get("valor", "")
    TicketCheck.objects.update_or_create(
        ticket=ticket, clave=clave,
        defaults={"etiqueta": punto.etiqueta, "estado": estado, "nota": (nota or "").strip()[:5000],
                  "valor": valor, "por": user, "por_nombre": _nombre(user), "en": timezone.now()})
    return True, f"«{punto.etiqueta}» marcado como {dict(RecruitCheck.ESTADOS)[estado].lower()}."
