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
    "koru_stats.tickets_directores": {"directores"},
    "koru_stats.tickets_it": {"it", "soporte"},
    # ★ Los ayudantes atienden Soporte y nada más: IT tiene las llaves de todo.
    "koru_stats.tickets_soporte": {"soporte"},
}

PREFIJO_NUMERO = {"directores": "D", "it": "IT", "soporte": "S"}


def config(tipo):
    from .models import TicketTipoConfig
    return TicketTipoConfig.objects.filter(tipo=tipo).first()


def tipos_que_gestiona(user):
    """Los tipos de ticket que este usuario puede ver y llevar."""
    if not user.is_authenticated:
        return set()
    if user.is_superuser or user.has_perm("koru_stats.tickets_admin"):
        return {"directores", "it", "soporte"}
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
