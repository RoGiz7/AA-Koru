"""
Lo que Koru cuelga del menú de Alliance Auth.

★ TRES ENTRADAS, NO ONCE (24/10/2026). Antes había once, todas empezando por
«🌀 Koru —». El problema no era el número: era QUIÉN las veía. Un miembro
normal veía tres o cuatro; un director, las once. El menú se ensuciaba justo
para quien más deprisa necesita encontrar las cosas — el mismo fallo que
tenía la ficha de solicitud antes de las pestañas.

⚠ Alliance Auth 5.3 NO tiene submenús: se comprobó en
`allianceauth/services/hooks.py` y no hay ni `children` ni `folder`. Por eso
cada panel es una página con tarjetas y no un desplegable. Cuesta un clic;
a cambio, un director pasa de once entradas a tres.

El reparto vive en `paneles.py`, no aquí: añadir una pantalla nueva debería
ser una línea en una lista, no tocar los hooks.
"""

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import paneles, urls


class PanelMenuHook(MenuItemHook):
    """
    Una entrada por panel, y solo si el usuario tiene algo dentro.

    ★ Un menú que lleva a una página vacía es peor que no tener el menú: el
    que lo pulsa se queda sin saber si le falta un permiso o si la pantalla
    está rota.

    ⚠⚠ CADA PANEL NECESITA SU PROPIA SUBCLASE, y no es manía de estilo:
    **Alliance Auth identifica cada elemento del menú por la clase del hook.**
    Registrar los tres paneles con esta misma clase los colapsa en UNA sola
    fila de `MenuItem`: la crea el primero y el último le pisa el texto.
    Se vio en producción el 24/10/2026 — una única entrada «Koru — Dirección»
    con el orden 1200, que es el de «Koru» a secas.

    Por eso debajo hay tres subclases que no añaden nada: lo que aportan es
    ser clases distintas.
    """

    area = None

    def render(self, request):
        if not request.user.is_authenticated:
            return ""
        if not paneles.tiene_algo(request.user, self.area):
            return ""
        return super().render(request)


class PanelMioHook(PanelMenuHook):
    area = paneles.MIO


class PanelGestionHook(PanelMenuHook):
    area = paneles.GESTION


class PanelDireccionHook(PanelMenuHook):
    area = paneles.DIRECCION


@hooks.register("menu_item_hook")
def register_menu_mio():
    return PanelMioHook(
        "🌀 Koru",
        "fas fa-chart-bar fa-fw",
        # ⚠ Una URL propia por panel en vez de pasarle el área como argumento:
        # `MenuItemHook` hace `reverse(url_name)` sin más, así que una ruta con
        # parámetro reventaría al construir el menú — y un menú que revienta se
        # lleva por delante TODO el Auth, no solo Koru.
        "koru_stats:panel_mio",
        navactive=["koru_stats:panel_mio"],
        order=1200,
    )


@hooks.register("menu_item_hook")
def register_menu_gestion():
    return PanelGestionHook(
        "🌀 Koru — Gestión",
        "fas fa-user-check fa-fw",
        "koru_stats:panel_gestion",
        navactive=["koru_stats:panel_gestion"],
        order=1201,
    )


@hooks.register("menu_item_hook")
def register_menu_direccion():
    return PanelDireccionHook(
        "🌀 Koru — Dirección",
        "fas fa-chart-line fa-fw",
        "koru_stats:panel_direccion",
        navactive=["koru_stats:panel_direccion"],
        order=1202,
    )


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "koru_stats", r"^koru/")


class ReclutamientoMenuHook(MenuItemHook):
    """
    ★ FUERA DE LOS PANELES Y ARRIBA DEL TODO, a propósito. Quien la necesita
    es el que menos sabe moverse por el Auth: alguien que acaba de registrarse
    y no tiene ni un grupo. Meterla detrás de un panel es justo lo contrario
    de lo que se busca.

    ⚠ Y desaparece cuando ya estás dentro. Antes la veía TODO el mundo,
    incluido el veterano de hace tres años, que tenía en su menú una
    invitación permanente a solicitar entrar en su propia corp. Se oculta en
    cuanto alguno de sus personajes está en una corp vigilada — el mismo dato
    que usa la tarea que detecta las entradas, para no inventar un criterio
    nuevo que luego diga otra cosa.
    """

    def render(self, request):
        if not request.user.is_authenticated:
            return ""
        try:
            if self._ya_esta_dentro(request.user):
                return ""
        except Exception:
            # Si la comprobación falla, se ENSEÑA. Esconder la puerta de
            # entrada por un error de base de datos es el peor de los dos
            # fallos posibles.
            pass
        return super().render(request)

    @staticmethod
    def _ya_esta_dentro(user):
        # Con el ORM y no con SQL a mano: el nombre de la tabla es un detalle
        # que no hay que repetir, y así no se olvida `is_active` — una corp
        # que se dejó de vigilar no debería seguir escondiendo la entrada.
        from allianceauth.authentication.models import CharacterOwnership

        from .models import TrackedCorporation

        corps = (TrackedCorporation.objects.filter(is_active=True)
                 .values_list("corporation_id", flat=True))
        return (CharacterOwnership.objects
                .filter(user=user, character__corporation_id__in=list(corps))
                .exists())


@hooks.register("menu_item_hook")
def register_menu_reclutamiento():
    return ReclutamientoMenuHook(
        "Únete a Rekium",
        "fas fa-user-plus fa-fw",
        "koru_stats:recruit_wizard",
        navactive=["koru_stats:recruit_wizard"],
        # Número bajo para que salga arriba, junto a Patreon, y no enterrado
        # entre las pantallas de staff.
        order=15,
    )


# ⚠ EL COG ESTA DESACTIVADO A PROPOSITO (24/10/2026). Ver el comentario de
# `koru_stats/cogs/reclutamiento.py`. Resumen: el comando se quedaba colgado
# sin error ni respuesta, el log del bot no escribe nada despues de arrancar, y
# depurarlo costaba un despliegue por hipotesis. El trabajo se hace en el Auth
# y Discord lo refleja; es mas facil de mantener y no se rompe solo.
#
# Para reactivarlo: descomentar, y ANTES arreglar el log del authbot — sin
# rastro no hay forma de saber por que falla.
#
# @hooks.register("discord_cogs_hook")
# def register_cogs():
#     return ["koru_stats.cogs.reclutamiento"]
