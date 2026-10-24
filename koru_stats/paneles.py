"""
El catálogo de pantallas de Koru, agrupado en tres paneles.

★ POR QUE. Había once entradas de menú, todas empezando por «🌀 Koru —». El
problema no era el número: era QUIEN las veía. Un miembro normal veía tres o
cuatro; un director, las once. O sea que el menú se ensuciaba justo para quien
más deprisa necesita encontrar las cosas.

★ AGRUPADAS POR LO QUE HACES, no por rango. Un reclutador también es miembro:
si los paneles fueran «miembros / mandos / dirección», estaría en dos. Que los
tres grupos se parezcan a los tres niveles es consecuencia, no criterio.

⚠ ESTO NO ES SEGURIDAD. Que una tarjeta no se dibuje no protege nada: cada
vista sigue teniendo su `permission_required`. Esto decide qué se OFRECE, no
qué se puede abrir. Si alguna vez alguien llega a una URL que no le toca, lo
para la vista, no esta lista.

⚠ Alliance Auth 5.3 no tiene submenús (comprobado en `services/hooks.py`: ni
`children` ni `folder`), así que un panel es una página de verdad con tarjetas.
El coste es un clic; a cambio, un director pasa de once entradas a tres.
"""

MIO       = "mio"
GESTION   = "gestion"
DIRECCION = "direccion"

PANELES = {
    MIO:       ("🌀 Koru",             "Lo tuyo: tu actividad, tus números y lo que te toca a ti."),
    GESTION:   ("🌀 Koru — Gestión",   "Las pantallas de trabajo del staff."),
    DIRECCION: ("🌀 Koru — Dirección", "La foto de la corp y lo que solo lleva Dirección."),
}


def _perm(*nombres):
    """Vale con tener UNO de esos permisos."""
    def comprobar(user):
        return any(user.has_perm(n) for n in nombres)
    return comprobar


def _ve_reclutamiento(user):
    # Importado aquí dentro y no arriba: `views` importa modelos, y este módulo
    # lo carga `hooks`, que Django lee durante el arranque.
    from .views import _ve_reclutamiento as f
    return f(user)


def _campaña_abierta(user, perm):
    if not user.has_perm(perm):
        return False
    from .models import GiftCampaign
    return GiftCampaign.objects.filter(estado=GiftCampaign.ESTADO_ABIERTA).exists()


# (área, url, título, icono, para qué sirve, quién la ve)
TARJETAS = [
    (MIO, "koru_stats:dashboard", "Estadísticas", "fas fa-chart-bar",
     "Los números de la corp: minería, PvP, actividad.",
     _perm("koru_stats.basic_access")),
    (MIO, "koru_stats:mi_dashboard", "Mi actividad", "fas fa-user",
     "Lo tuyo y lo de tus personajes, mes a mes.",
     _perm("koru_stats.basic_access")),
    (MIO, "koru_stats:pvp_dashboard", "PvP", "fas fa-crosshairs",
     "Kills, pérdidas y quién anda peleando.",
     _perm("koru_stats.basic_access")),
    (MIO, "koru_stats:moon_tax_mi", "Mi tax lunar", "fas fa-moon",
     "Lo que has minado en lunas y lo que te toca pagar.",
     _perm("koru_stats.basic_access")),
    (MIO, "koru_stats:gift_mi", "Mi aportación", "fas fa-gift",
     "Tu parte de la campaña de regalos.",
     lambda u: _campaña_abierta(u, "koru_stats.gift_access")),

    (GESTION, "koru_stats:recruit_lista", "Reclutamiento", "fas fa-user-check",
     "Las solicitudes de ingreso y su cadena de aprobación.",
     _ve_reclutamiento),
    (GESTION, "koru_stats:tickets_dashboard", "Tickets", "fas fa-ticket-alt",
     "Soporte, IT, Directores y Asuntos Internos.",
     _perm("koru_stats.tickets_admin", "koru_stats.tickets_reclutamiento",
           "koru_stats.tickets_directores", "koru_stats.tickets_asuntos_internos",
           "koru_stats.tickets_it")),
    (GESTION, "koru_stats:auditor_dashboard", "Auditor", "fas fa-user-shield",
     "Alertas de seguridad y fichas de piloto.",
     _perm("koru_stats.auditor_access")),
    (GESTION, "koru_stats:moon_dashboard", "Tax de lunas", "fas fa-moon",
     "Lo minado en lunas por todo el mundo.",
     _perm("koru_stats.moon_tax_access")),
    (GESTION, "koru_stats:moon_tax_gestion", "Validar tax lunar", "fas fa-check-double",
     "Revisar y dar por bueno lo que han pagado.",
     _perm("koru_stats.moon_tax_admin")),

    (DIRECCION, "koru_stats:corp_dashboard", "Finanzas", "fas fa-coins",
     "Cartera, impuestos y de dónde sale el ISK.",
     _perm("koru_stats.corp_finance_access")),
    (DIRECCION, "koru_stats:corp_health_dashboard", "Salud de la corp", "fas fa-chart-line",
     "Actividad, retención y cómo va entrando gente.",
     _perm("koru_stats.auditor_corp_health")),
    (DIRECCION, "koru_stats:gift_gestion", "Gestión de regalos", "fas fa-gifts",
     "Aportaciones, sorteos y entregas.",
     lambda u: _campaña_abierta(u, "koru_stats.gift_manage")),
]


def tarjetas_de(user, area):
    """Las tarjetas de ese panel que este usuario puede abrir."""
    if not getattr(user, "is_authenticated", False):
        return []
    fuera = []
    for zona, url, titulo, icono, texto, mira in TARJETAS:
        if zona != area:
            continue
        try:
            if mira(user):
                fuera.append({"url": url, "titulo": titulo, "icono": icono,
                              "texto": texto})
        except Exception:
            # Una comprobación que falle esconde su tarjeta, nunca tumba el
            # menú entero: el resto del Auth no tiene por qué caerse con ella.
            continue
    return fuera


def tiene_algo(user, area):
    """Si no hay ni una tarjeta, el panel no se ofrece. Un menú a una página
    vacía es peor que no tener el menú."""
    return bool(tarjetas_de(user, area))
