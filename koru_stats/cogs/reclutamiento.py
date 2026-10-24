"""
⚠⚠ DESACTIVADO EL 24/10/2026. NO ESTÁ REGISTRADO EN `hooks.py`.

Qué pasó, para quien lo retome:

- El comando se quedaba en «está pensando…» para siempre. Ni error ni
  respuesta: un bloqueo, no un fallo.
- Se probó: py-cord en vez de discord.py (ese sí era un error real, y se
  arregló), capturar y responder las excepciones, y `thread_sensitive=False`
  en `sync_to_async`. Ninguna lo resolvió.
- **La causa raíz de no poder arreglarlo es que el log del `authbot` no
  escribe nada después del arranque.** Sin rastro, cada intento es una
  hipótesis que cuesta un despliegue. Van cuatro.

Antes de volver a intentarlo: **arreglar el log del bot**. Con un traceback
esto se resuelve en diez minutos; sin él, no se resuelve.

Y la decisión de fondo (Zigor, 24/10): el trabajo se hace en el Auth y Discord
lo refleja. Lo que el cog ahorraba era abrir el navegador — comodidad, no
capacidad. Todo lo que hace está en la pantalla web, verificado y funcionando.

El código se deja porque la lógica es correcta y la mitad del camino está
hecha: llama a `recruit.py`, igual que la web.
"""

import logging

from asgiref.sync import sync_to_async
from django.conf import settings

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


def _guilds():
    """
    Registrar los comandos EN EL SERVIDOR y no globalmente.

    Los globales tardan hasta una hora en aparecer; los de guild son
    inmediatos. Si no hay guild configurado, se cae a global — tardará, pero
    funcionará.
    """
    g = str(getattr(settings, "DISCORD_GUILD_ID", "") or "")
    return [int(g)] if g.isdigit() else None


# --- Lo que toca la base, aislado -------------------------------------------

def _resumen(sol):
    """En qué punto va la solicitud."""
    pasos = [
        ("Entrevista", sol.entrevista_en),
        ("Reclutadores", sol.ok_reclutadores_en),
        ("Asuntos Internos", sol.ok_asuntos_en),
        ("Dirección", sol.ok_directores_en),
        ("Invitación", sol.invitacion_en),
    ]
    hechos = " · ".join(f"{'✅' if c else '⬜'} {n}" for n, c in pasos)
    if not sol.abierta:
        return (f"**{sol.main_character_name}** — cerrada como "
                f"«{sol.get_estado_display()}»\n{hechos}")

    falta = {
        "entrevista": "Falta marcar la entrevista — `/recluta entrevista`",
        "reclutadores": "Falta el OK de reclutadores — `/recluta ok`",
        "asuntos": "Falta el OK de Asuntos Internos — `/recluta ok`",
        "directores": "Falta el OK de Dirección — `/recluta ok`",
        "invitacion": "Falta mandar la invitación — `/recluta invitacion`",
        "esperando_entrada": "Invitación enviada: esperando a que entre en la corp",
    }.get(sol.fase, sol.fase)
    return f"**{sol.main_character_name}**\n{hechos}\n\n{falta}"


def _hacer(canal_id, uid, accion, dato=""):
    """
    Resuelve quién ejecuta, encuentra la solicitud del canal y llama a `recruit`.

    Devuelve (ok, respuesta_privada, aviso_publico). El aviso vacío significa
    que no hay nada que anunciar al canal.
    """
    from koru_stats import recruit
    from koru_stats.models import RecruitApplication

    sol = (RecruitApplication.objects
           .filter(discord_channel_id=str(canal_id))
           .order_by("-created_at").first())
    if not sol:
        return False, "Este canal no es el de ninguna solicitud.", ""

    user = recruit.usuario_de_discord(uid)
    if not user:
        # ⚠ Pasa de verdad: alguien del staff con el rol en Discord pero sin el
        # servicio activado en el Auth. Mejor decírselo que dejarle ejecutando
        # comandos sin efecto.
        return False, ("Tu Discord no está vinculado a ninguna cuenta del Auth, "
                       "así que no puedo saber qué permisos tienes."), ""

    quien = recruit._nombre(user)

    if accion == "estado":
        return True, _resumen(sol), ""

    if accion == "entrevista":
        ok, msg = recruit.marcar_entrevista(sol, user, dato)
        return ok, msg, (f"🎙️ **Entrevista hecha** por {quien}." if ok else "")

    if accion == "ok":
        paso = sol.fase
        if paso in ("entrevista", "esperando_entrada", "cerrada"):
            return False, f"Ahora no toca un OK: {paso}.", ""
        ok, msg = recruit.aprobar(sol, user, paso)
        if not ok:
            return False, msg, ""
        etiquetas = {"reclutadores": "Reclutadores", "asuntos": "Asuntos Internos",
                     "directores": "Dirección"}
        return True, msg, f"✅ **{etiquetas.get(paso, paso)}** dan su OK — {quien}."

    if accion == "invitacion":
        ok, msg = recruit.marcar_invitacion(sol, user)
        return ok, msg, (f"📨 **Invitación enviada** por {quien}. "
                         f"Acéptala desde el juego." if ok else "")

    return False, "No sé hacer eso.", ""


# --- El cog -----------------------------------------------------------------

class Reclutamiento(commands.Cog):
    """Los pasos de una solicitud, desde su canal."""

    def __init__(self, bot):
        self.bot = bot

    grupo = discord.SlashCommandGroup(
        "recluta", "Pasos de la solicitud de este canal", guild_ids=_guilds())

    async def _responder(self, ctx, accion, dato=""):
        """
        ★ TODO VA ENVUELTO, Y EL ERROR SE RESPONDE EN DISCORD. El log del bot
        no escribe nada despues del arranque, asi que una excepcion aqui deja
        el comando colgado en «esta pensando…» para siempre y sin rastro en
        ningun sitio. Contarlo en la respuesta convierte un fallo invisible en
        uno que se lee.
        """
        try:
            # `ctx.channel.id` y no `ctx.channel_id`: el primero existe en
            # todas las versiones, el segundo no siempre.
            canal = ctx.channel.id if ctx.channel else 0
            # ⚠⚠ `thread_sensitive=False` NO ES OPCIONAL AQUI. Por defecto
            # `sync_to_async` ejecuta el codigo de Django en el hilo principal
            # — que en un bot es justo el que atiende el bucle de eventos. Se
            # quedan esperandose el uno al otro y el comando no responde NUNCA:
            # ni error ni respuesta, solo «esta pensando…» para siempre.
            # Con False va a un hilo aparte y no hay bloqueo.
            ok, msg, aviso = await sync_to_async(_hacer, thread_sensitive=False)(
                canal, ctx.author.id, accion, dato)
        except Exception as exc:
            logger.exception("koru cog: fallo en /recluta %s", accion)
            await ctx.respond(
                f"⚠ Se rompió al ejecutarlo: `{type(exc).__name__}: {exc}`",
                ephemeral=True)
            return

        # ⚠ La respuesta a quien ejecuta va SIEMPRE en efímero; lo que se
        # anuncia al canal es otra cosa. Mezclarlas llena el canal de ruido.
        await ctx.respond(msg, ephemeral=True)

        if ok and aviso:
            try:
                await ctx.channel.send(aviso)
            except Exception as exc:
                logger.warning("koru cog: no se pudo avisar en el canal: %s", exc)

    @grupo.command(name="estado", description="En qué punto va esta solicitud")
    async def estado(self, ctx: discord.ApplicationContext):
        await self._responder(ctx, "estado")

    @grupo.command(name="entrevista", description="Marcar que ya has hecho la entrevista")
    async def entrevista(
            self, ctx: discord.ApplicationContext,
            nota: discord.Option(str, "Lo que quieras dejar escrito", required=False) = ""):
        await self._responder(ctx, "entrevista", nota or "")

    @grupo.command(name="ok", description="Dar tu OK al paso que toque ahora")
    async def ok(self, ctx: discord.ApplicationContext):
        await self._responder(ctx, "ok")

    @grupo.command(name="invitacion", description="Marcar la invitación in-game como enviada")
    async def invitacion(self, ctx: discord.ApplicationContext):
        await self._responder(ctx, "invitacion")


def setup(bot):
    # ⚠ `setup` SÍNCRONO: py-cord lo llama así, no como corrutina.
    bot.add_cog(Reclutamiento(bot))
