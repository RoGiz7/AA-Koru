from django.urls import path
from . import views

app_name = "koru_stats"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Los tres paneles de Koru. Una ruta por panel y no una con parámetro:
    # `MenuItemHook` hace `reverse(url_name)` a secas, y una ruta que necesita
    # argumento reventaría al construir el menú de todo el Auth.
    path("panel/mio/",       views.koru_panel, {"area": "mio"},       name="panel_mio"),
    path("panel/gestion/",   views.koru_panel, {"area": "gestion"},   name="panel_gestion"),
    path("panel/direccion/", views.koru_panel, {"area": "direccion"}, name="panel_direccion"),

    # Reclutamiento: lo ve cualquiera que haya entrado, sea o no de la corp.
    path("reclutamiento/", views.recruit_wizard, name="recruit_wizard"),
    path("reclutamiento/enviar/", views.recruit_enviar, name="recruit_enviar"),
    path("reclutamiento/enviada/", views.recruit_enviada, name="recruit_enviada"),

    # La parte del staff
    path("reclutamiento/gestion/", views.recruit_lista, name="recruit_lista"),
    path("reclutamiento/gestion/<int:sol_id>/", views.recruit_ficha, name="recruit_ficha"),
    path("reclutamiento/gestion/<int:sol_id>/accion/", views.recruit_accion, name="recruit_accion"),

    path("personal/", views.mi_dashboard, name="mi_dashboard"),
    path("corp/", views.corp_dashboard, name="corp_dashboard"),
    path("lunas/", views.moon_dashboard_v2, name="moon_dashboard"),
    path("lunas/pagar/<int:payment_id>/", views.moon_mark_paid, name="moon_mark_paid"),
    path("lunas/mi/", views.moon_tax_mi, name="moon_tax_mi"),
    path("lunas/gestion/", views.moon_tax_gestion, name="moon_tax_gestion"),
    path("lunas/gestion/validar/<int:main_char_id>/", views.moon_tax_validar, name="moon_tax_validar"),
    path("pvp/", views.pvp_dashboard, name="pvp_dashboard"),
    path("auditor/", views.auditor_dashboard, name="auditor_dashboard"),
    path("auditor/piloto/<int:main_id>/", views.auditor_pilot, name="auditor_pilot"),
    path("auditor/piloto/<int:main_id>/marcar/", views.auditor_marcar, name="auditor_marcar"),
    path("auditor/piloto/<int:main_id>/auditar/", views.auditor_abrir_auditoria,
         name="auditor_abrir_auditoria"),
    path("auditor/corp/", views.corp_health_dashboard, name="corp_health_dashboard"),
    path("auditor/corp/reclutamiento/", views.corp_recruitment_dashboard, name="corp_recruitment_dashboard"),
    path("auditor/corp/social/", views.corp_social_dashboard, name="corp_social_dashboard"),
    path("auditor/corp/lunas/", views.corp_moons_dashboard, name="corp_moons_dashboard"),
    path("tickets/", views.tickets_dashboard, name="tickets_dashboard"),
    path("tickets/stats/", views.tickets_stats, name="tickets_stats"),
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:ticket_id>/reclamar/", views.ticket_reclamar, name="ticket_reclamar"),
    path("tickets/<int:ticket_id>/estado/", views.ticket_estado, name="ticket_estado"),
    # ⚠ Índice, NO una URL: una vista que acepte direcciones es un proxy abierto.
    path("tickets/<int:ticket_id>/fichero/<int:idx>/", views.ticket_fichero,
         name="ticket_fichero"),
    path("regalos/mi/", views.gift_mi, name="gift_mi"),
    path("regalos/gestion/", views.gift_gestion, name="gift_gestion"),
    path("regalos/gestion/validar/<int:pk>/", views.gift_validar, name="gift_validar"),
    path("regalos/sorteos/", views.gift_sorteos, name="gift_sorteos"),
    path("regalos/sorteos/<int:pk>/", views.gift_sorteo, name="gift_sorteo"),
    path("regalos/sorteos/<int:pk>/accion/", views.gift_sorteo_accion, name="gift_sorteo_accion"),
    path("regalos/sorteos/<int:pk>/ruleta/", views.gift_ruleta, name="gift_ruleta"),
    path("regalos/entregas/", views.gift_entregas, name="gift_entregas"),
    path("regalos/entregas/<int:pk>/accion/", views.gift_entrega_accion, name="gift_entrega_accion"),
    path("export/resumen/", views.export_csv_summary, name="export_csv_summary"),
    path("export/pvp/",     views.export_csv_pvp,     name="export_csv_pvp"),
    path("export/ore/",     views.export_csv_ore,     name="export_csv_ore"),
]
