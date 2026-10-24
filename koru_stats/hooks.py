from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls


def _tiene_acceso(request):
    return request.user.has_perm("koru_stats.basic_access")


class RankingMenuHook(MenuItemHook):
    def render(self, request):
        if _tiene_acceso(request):
            return super().render(request)
        return ""


class CorpMenuHook(MenuItemHook):
    def render(self, request):
        if request.user.has_perm("koru_stats.corp_finance_access"):
            return super().render(request)
        return ""


class LunasMenuHook(MenuItemHook):
    def render(self, request):
        if request.user.has_perm("koru_stats.moon_tax_access"):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_ranking():
    return RankingMenuHook(
        "🌀 Koru — Estadísticas",
        "fas fa-chart-bar fa-fw",
        "koru_stats:dashboard",
        navactive=["koru_stats:dashboard"],
        order=1200,
    )


@hooks.register("menu_item_hook")
def register_menu_corp():
    return CorpMenuHook(
        "🌀 Koru — Finanzas",
        "fas fa-coins fa-fw",
        "koru_stats:corp_dashboard",
        navactive=["koru_stats:corp_dashboard"],
        order=1201,
    )


@hooks.register("menu_item_hook")
def register_menu_lunas():
    return LunasMenuHook(
        "🌀 Koru — Tax Lunas",
        "fas fa-moon fa-fw",
        "koru_stats:moon_dashboard",
        navactive=["koru_stats:moon_dashboard"],
        order=1202,
    )


class PvpMenuHook(MenuItemHook):
    def render(self, request):
        if _tiene_acceso(request):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_pvp():
    return PvpMenuHook(
        "🌀 Koru — PvP",
        "fas fa-crosshairs fa-fw",
        "koru_stats:pvp_dashboard",
        navactive=["koru_stats:pvp_dashboard"],
        order=1203,
    )


class AuditorMenuHook(MenuItemHook):
    def render(self, request):
        if request.user.has_perm("koru_stats.auditor_access"):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_auditor():
    return AuditorMenuHook(
        "🌀 Koru — Auditor",
        "fas fa-user-shield fa-fw",
        "koru_stats:auditor_dashboard",
        navactive=["koru_stats:auditor_dashboard"],
        order=1204,
    )


class TicketsMenuHook(MenuItemHook):
    def render(self, request):
        perms = [
            "koru_stats.tickets_admin", "koru_stats.tickets_reclutamiento",
            "koru_stats.tickets_directores", "koru_stats.tickets_asuntos_internos",
            "koru_stats.tickets_it",
        ]
        if any(request.user.has_perm(p) for p in perms):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_tickets():
    return TicketsMenuHook(
        "🌀 Koru — Tickets",
        "fas fa-ticket-alt fa-fw",
        "koru_stats:tickets_dashboard",
        navactive=["koru_stats:tickets_dashboard"],
        order=1205,
    )


class DirectoresMenuHook(MenuItemHook):
    def render(self, request):
        if request.user.has_perm("koru_stats.auditor_corp_health"):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_corp_health():
    return DirectoresMenuHook(
        "\U0001f300 Koru \u2014 Direcci\u00f3n",
        "fas fa-chart-line fa-fw",
        "koru_stats:corp_health_dashboard",
        navactive=["koru_stats:corp_health_dashboard"],
        order=1206,
    )


class RegalosMenuHook(MenuItemHook):
    """
    Estacional: la entrada solo existe mientras haya una campana abierta.

    Una fiesta son seis semanas al ano; una entrada fija que diez meses no
    enseña nada es ruido en el menu. En enero desaparece sola, sin que nadie
    tenga que acordarse de quitarla.
    """
    def render(self, request):
        if not request.user.has_perm("koru_stats.gift_access"):
            return ""
        from .models import GiftCampaign
        if not GiftCampaign.objects.filter(estado=GiftCampaign.ESTADO_ABIERTA).exists():
            return ""
        return super().render(request)


@hooks.register("menu_item_hook")
def register_menu_regalos():
    return RegalosMenuHook(
        "\U0001f381 Koru — Mi aportación",
        "fas fa-gift fa-fw",
        "koru_stats:gift_mi",
        navactive=["koru_stats:gift_mi"],
        order=1207,
    )


class RegalosGestionMenuHook(MenuItemHook):
    """Para directores, y tambien estacional: sin campaña abierta no se pinta."""
    def render(self, request):
        if not request.user.has_perm("koru_stats.gift_manage"):
            return ""
        from .models import GiftCampaign
        if not GiftCampaign.objects.filter(estado=GiftCampaign.ESTADO_ABIERTA).exists():
            return ""
        return super().render(request)


@hooks.register("menu_item_hook")
def register_menu_regalos_gestion():
    return RegalosGestionMenuHook(
        "\U0001f381 Koru \u2014 Gesti\u00f3n de regalos",
        "fas fa-gifts fa-fw",
        "koru_stats:gift_gestion",
        navactive=["koru_stats:gift_gestion", "koru_stats:gift_sorteos",
                   "koru_stats:gift_sorteo", "koru_stats:gift_entregas"],
        order=1208,
    )


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "koru_stats", r"^koru/")


class ReclutamientoMenuHook(MenuItemHook):
    """
    ★ SIN COMPROBAR NINGÚN PERMISO, a propósito. Esta entrada es justo para
    quien todavía no es nadie en la corp: alguien que acaba de entrar al Auth y
    no tiene grupo ninguno. Si pidiera `basic_access` la vería todo el mundo
    menos las personas a las que va dirigida.
    """

    def render(self, request):
        if not request.user.is_authenticated:
            return ""
        return super().render(request)


@hooks.register("menu_item_hook")
def register_menu_reclutamiento():
    return ReclutamientoMenuHook(
        "Únete a Rekium",
        "fas fa-user-plus fa-fw",
        "koru_stats:recruit_wizard",
        navactive=["koru_stats:recruit_wizard"],
        # Número bajo para que salga arriba, junto a Patreon, y no enterrado
        # entre las pantallas de staff: quien lo necesita es el que menos sabe
        # moverse por aquí.
        order=15,
    )


class ReclutamientoGestionMenuHook(MenuItemHook):
    """
    ⚠ Ver y aprobar no son lo mismo: Asuntos Internos y Dirección tienen que
    poder entrar aunque no tengan `recruit_manage`, porque su paso está dentro.
    Por eso también se mira si el usuario está en algún grupo de la cadena.
    """

    def render(self, request):
        if not request.user.is_authenticated:
            return ""
        from .views import _ve_reclutamiento
        if _ve_reclutamiento(request.user):
            return super().render(request)
        return ""


@hooks.register("menu_item_hook")
def register_menu_reclutamiento_gestion():
    return ReclutamientoGestionMenuHook(
        "🌀 Koru — Reclutamiento",
        "fas fa-user-check fa-fw",
        "koru_stats:recruit_lista",
        navactive=["koru_stats:recruit_lista"],
        order=1209,
    )
