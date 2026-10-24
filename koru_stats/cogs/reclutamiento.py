"""
El reclutamiento, desde el propio canal de Discord.

★ POR QUÉ COMANDOS Y NO BOTONES. Los botones quedan más bonitos, pero los
botones persistentes se pierden cuando el bot reinicia si no se vuelven a
registrar — y ese fallo no se nota el día que pasa: se nota semanas después,
cuando alguien pulsa y no ocurre nada. Un comando no tiene ese modo de fallo.
Los botones se pueden añadir encima más adelante.

★ ESTE COG NO DECIDE NADA. Toda la lógica —quién puede, en qué orden, qué se
escribe— vive en `recruit.py` y la comparte con la pantalla web. Si aquí se
reimplementara, aprobar desde Discord y aprobar desde la web harían cosas
distintas a la primera modificación, sin que nadie se diera cuenta.

⚠ Django es síncrono y discord.py es asíncrono: TODO lo que toque la base va
envuelto en `sync_to_async`. Sin eso, el bot se bloquea o Django protesta.
"""

import logging

from asgiref.sync import sync_to_async

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


# --- Lo que toca la base, aislado -------------------------------------------

def _solicitud_del_canal(canal_id):
    from koru_stats.models import RecruitApplication

    return (RecruitApplication.objects
            .filter(discord_channel_id=str(canal_id))
            .order_by("-created_at").first())


def _quien(uid):
    from koru_stats import recruit

    return recruit.usuario_de_discord(uid)


def _resumen(sol):
    """En qué punto va, en una línea."""
    pasos = [
        ("Entrevista", sol.entrevista_en),
        ("Reclutadores", sol.ok_reclutadores_en),
        ("Asuntos Internos", sol.ok_asuntos_en),
        ("Dirección", sol.ok_directores_en),
        ("Invitación", sol.invitacion_en),
    ]
    hechos = " · ".join(f"{'✅' if c else '⬜'} {n}" for n, c in pasos)
    if not sol.abierta:
        return f"**{sol.main_character_name}** — cerrada como «{sol.get_estado_display()}»\n{hechos}"

    falta = {
        "entrevista": "Falta marcar la entrevista (`/recluta entrevista`)",
        "reclutadores": "Falta el OK de reclutadores (`/recluta ok`)",
        "asuntos": "Falta el OK de Asuntos Internos (`/recluta ok`)",
        "directores": "Falta el OK de Dirección (`/recluta ok`)",
        "invitacion": "Falta mandar la invitación (`/recluta invitacion`)",
        "esperando_entrada": "Invitación enviada: esperando a que entre en la corp",
    }.get(sol.fase, sol.fase)
    return f"**{sol.main_character_name}**\n{hechos}\n\n{falta}"


def _hacer(canal_id, uid, accion, dato=""):
    """
    Resuelve quién pulsa, encuentra la solicitud y llama a `recruit`.

    Devuelve (ok, mensaje, aviso_publico). El aviso público es lo que se manda
    al canal; vacío significa que no hay nada que anunciar.
    """
    from koru_stats import recruit

    sol = _solicitud_del_canal(canal_id)
    if not sol:
        return False, "Este canal no es el de ninguna solicitud.", ""

    user = _quien(uid)
    if not user:
        # ⚠ Pasa de verdad: alguien del staff que no ha vinculado Discord en el
        # Auth. Mejor decírselo que dejarle pulsando sin efecto.
        return False, ("Tu Discord no está vinculado a ninguna cuenta del Auth, "
                       "así que no puedo saber qué permisos tienes."), ""

    if accion == "estado":
        return True, _resumen(sol), ""

    if accion == "entrevista":
        ok, msg = recruit.marcar_entrevista(sol, user, dato)
        return ok, msg, (f"🎙️ **Entrevista hecha** por {recruit._nombre(user)}." if ok else "")

    if accion == "ok":
        paso = sol.fase
        if paso in ("entrevista", "esperando_entrada", "cerrada"):
            return False, f"Ahora no toca un OK: {paso}.", ""
        ok, msg = recruit.aprobar(sol, user, paso)
        if not ok:
            return False, msg, ""
        etiquetas = {"reclutadores": "Reclutadores", "asuntos": "Asuntos Internos",
                     "directores": "Dirección"}
        return True, msg, f"✅ **{etiquetas.get(paso, paso)}** dan su OK — {recruit._nombre(user)}."

    if accion == "invitacion":
        ok, msg = recruit.marcar_invitacion(sol, user)
        return ok, msg, (f"📨 **Invitación enviada** por {recruit._nombre(user)}. "
                         f"Acéptala desde el juego." if ok else "")

    return False, "No sé hacer eso.", ""


# --- El cog -----------------------------------------------------------------

class Reclutamiento(commands.Cog):
    """Los pasos de una solicitud, desde su canal."""

    def __init__(self, bot):
        self.bot = bot

    grupo = app_commands.Group(
        name="recluta",
        description="Pasos de la solicitud de este canal")

    async def _responder(self, interaction, canal_id, uid, accion, dato=""):
        ok, msg, aviso = await sync_to_async(_hacer)(canal_id, uid, accion, dato)

        # ⚠ La respuesta al que pulsa va SIEMPRE en efímero: lo que se anuncia
        # al canal es otra cosa, y mezclarlas llena el canal de ruido.
        await interaction.response.send_message(msg, ephemeral=True)

        if ok and aviso:
            try:
                await interaction.channel.send(aviso)
            except Exception as exc:
                logger.warning("koru cog: no se pudo avisar en el canal: %s", exc)

    @grupo.command(name="estado", description="En qué punto va esta solicitud")
    async def estado(self, interaction: discord.Interaction):
        await self._responder(interaction, interaction.channel_id,
                              interaction.user.id, "estado")

    @grupo.command(name="entrevista", description="Marcar que ya has hecho la entrevista")
    @app_commands.describe(nota="Lo que quieras dejar escrito (opcional)")
    async def entrevista(self, interaction: discord.Interaction, nota: str = ""):
        await self._responder(interaction, interaction.channel_id,
                              interaction.user.id, "entrevista", nota)

    @grupo.command(name="ok", description="Dar tu OK al paso que toque ahora")
    async def ok(self, interaction: discord.Interaction):
        await self._responder(interaction, interaction.channel_id,
                              interaction.user.id, "ok")

    @grupo.command(name="invitacion", description="Marcar la invitación in-game como enviada")
    async def invitacion(self, interaction: discord.Interaction):
        await self._responder(interaction, interaction.channel_id,
                              interaction.user.id, "invitacion")


async def setup(bot):
    await bot.add_cog(Reclutamiento(bot))
