from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from allianceauth.eveonline.models import EveCorporationInfo

from .models import (
    TrackedCorporation, MoonTaxConfig, MoonTaxPayment,
    AuditorConfig, AuditorRiskScore, AuditorAlert,
    KoruMarketPrice, CharacterValueSnapshot,
    CharacterOwnershipSnapshot, CharacterLifecycleEvent,
    TicketsConfig, Ticket,
    MoonAllianceFee, MoonTaxRecipient,
    GiftCampaign, GiftRecipient, GiftTier,
    GiftContribution, GiftContributionItem,
    Raffle, RaffleEntrant, RafflePrize, RaffleDraw, RaffleRosterFilter,
    GiftDelivery,
    RecruitApplication, RecruitNote, RecruitQuestion, RecruitConfig,
)


# ---------------------------------------------------------------------------
# TrackedCorporation
# ---------------------------------------------------------------------------

def _corps_con_miembros():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ci.corporation_id, ci.corporation_name
            FROM eveonline_evecorporationinfo ci
            JOIN eveonline_evecharacter ec ON ec.corporation_id = ci.corporation_id
            JOIN authentication_characterownership co ON co.character_id = ec.id
            ORDER BY ci.corporation_name
        """)
        return [(row[0], f"{row[1]} ({row[0]})") for row in cursor.fetchall()]


class TrackedCorporationForm(forms.ModelForm):
    corp_choice = forms.ChoiceField(
        choices=[],
        label="Corporación",
        required=True,
        help_text="Solo corps con personajes registrados en Auth"
    )

    class Meta:
        model  = TrackedCorporation
        fields = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")] + _corps_con_miembros()
        self.fields["corp_choice"].choices = choices
        if self.instance and self.instance.pk:
            self.fields["corp_choice"].initial = self.instance.corporation_id

    def clean(self):
        cleaned = super().clean()
        corp_id = cleaned.get("corp_choice")
        if corp_id:
            try:
                corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
                cleaned["_corporation_id"]   = corp.corporation_id
                cleaned["_corporation_name"] = corp.corporation_name
            except EveCorporationInfo.DoesNotExist:
                raise forms.ValidationError("Corp no encontrada")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.corporation_id   = self.cleaned_data["_corporation_id"]
        instance.corporation_name = self.cleaned_data["_corporation_name"]
        if commit:
            instance.save()
        return instance


@admin.register(TrackedCorporation)
class TrackedCorporationAdmin(admin.ModelAdmin):
    form          = TrackedCorporationForm
    list_display  = ("corporation_name", "corporation_id", "is_active")
    list_editable = ("is_active",)
    ordering      = ("corporation_name",)


# ---------------------------------------------------------------------------
# MoonTaxConfig
# ---------------------------------------------------------------------------

@admin.register(MoonTaxConfig)
class MoonTaxConfigAdmin(admin.ModelAdmin):
    list_display = ("tag", "ubiquitous_rate", "common_rate", "uncommon_rate", "rare_rate", "exceptional_rate", "is_active", "updated_at")
    list_editable = ("ubiquitous_rate", "common_rate", "uncommon_rate", "rare_rate", "exceptional_rate", "is_active")
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Identificación", {
            "fields": ("tag", "is_active", "updated_at")
        }),
        ("Tasas por tier (%)", {
            "description": "Porcentaje sobre el valor de mercado del ore minado.",
            "fields": (
                ("ubiquitous_rate", "common_rate"),
                ("uncommon_rate",   "rare_rate"),
                ("exceptional_rate",),
            )
        }),
    )


# ---------------------------------------------------------------------------
# MoonTaxPayment
# ---------------------------------------------------------------------------

@admin.register(MoonTaxPayment)
class MoonTaxPaymentAdmin(admin.ModelAdmin):
    list_display  = ("character_name", "period", "isk_owed_display", "is_paid", "paid_by", "paid_at")
    list_filter   = ("is_paid", "period")
    search_fields = ("character_name", "period")
    readonly_fields = ("character_id", "character_name", "period", "isk_owed", "created_at", "updated_at", "paid_by", "paid_at")
    ordering = ("-period", "character_name")

    fieldsets = (
        ("Piloto", {
            "fields": ("character_name", "character_id", "period", "isk_owed")
        }),
        ("Estado del pago", {
            "fields": ("is_paid", "paid_by", "paid_at", "notes")
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def isk_owed_display(self, obj):
        v = float(obj.isk_owed)
        if v >= 1e9:
            return f"{v/1e9:.2f} B ISK"
        if v >= 1e6:
            return f"{v/1e6:.2f} M ISK"
        return f"{v:,.0f} ISK"
    isk_owed_display.short_description = "ISK owed"

    def has_add_permission(self, request):
        return False  # Solo se crean desde la vista, no manualmente


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------

@admin.register(AuditorConfig)
class AuditorConfigAdmin(admin.ModelAdmin):
    list_display    = ("tag", "modo_calibracion", "calibracion_hasta", "umbral_amarillo", "umbral_naranja", "umbral_rojo", "updated_at")
    readonly_fields = ("updated_at", "blue_alliance_ids", "blue_corp_ids", "own_alliance_ids", "own_corp_ids")

    fieldsets = (
        ("Identificación", {
            "fields": ("tag", "updated_at"),
        }),
        ("Calibración", {
            "description": "En modo calibración el Auditor calcula y muestra, pero NO envía avisos a Discord.",
            "fields": ("modo_calibracion", "calibracion_hasta"),
        }),
        ("Pesos por dimensión (0–1, idealmente suman 1)", {
            "fields": (
                ("w_pvp", "w_ciclo", "w_espias"),
                ("w_fuga", "w_huecos", "w_financiero"),
            ),
        }),
        ("Umbrales de nivel (0–100)", {
            "fields": (("umbral_amarillo", "umbral_naranja", "umbral_rojo"),),
        }),
        ("Parámetros de señales", {
            "fields": ("token_stale_dias", "inactividad_dias", "donacion_externa_min"),
        }),
        ("States del core AA (qué cuenta como azul / propio)", {
            "fields": ("blue_state_ids", "own_state_ids"),
        }),
        ("Standings cacheados (auto, vía sync_blue_standings)", {
            "classes": ("collapse",),
            "fields": ("blue_alliance_ids", "blue_corp_ids", "own_alliance_ids", "own_corp_ids"),
        }),
        ("Assets / staging (Fase 2)", {
            "classes": ("collapse",),
            "fields": ("staging_location_ids",),
        }),
    )


@admin.register(AuditorRiskScore)
class AuditorRiskScoreAdmin(admin.ModelAdmin):
    list_display  = ("main_character_name", "period", "risk_total", "nivel",
                     "score_pvp", "score_ciclo", "score_espias", "score_fuga", "score_huecos", "score_financiero", "computed_at")
    list_filter   = ("nivel", "period", "corporation_id")
    search_fields = ("main_character_name",)
    ordering      = ("-period", "-risk_total")
    readonly_fields = ("computed_at",)

    def has_add_permission(self, request):
        return False  # Lo crea la task


@admin.register(AuditorAlert)
class AuditorAlertAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "severidad", "familia", "codigo", "main_character_name", "period", "estado", "revisada_por")
    list_filter   = ("estado", "severidad", "familia", "period")
    search_fields = ("main_character_name", "codigo")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        return False  # Las crea la task


@admin.register(KoruMarketPrice)
class KoruMarketPriceAdmin(admin.ModelAdmin):
    list_display  = ("type_id", "type_name", "average_price", "adjusted_price", "updated_at")
    search_fields = ("type_id", "type_name")
    ordering      = ("type_id",)

    def has_add_permission(self, request):
        return False  # La puebla la task


@admin.register(CharacterValueSnapshot)
class CharacterValueSnapshotAdmin(admin.ModelAdmin):
    list_display  = ("snapshot_date", "character_id", "main_character_id", "asset_value", "wallet_balance", "item_count")
    list_filter   = ("snapshot_date",)
    search_fields = ("character_id", "main_character_id")
    ordering      = ("-snapshot_date",)

    def has_add_permission(self, request):
        return False


@admin.register(CharacterOwnershipSnapshot)
class CharacterOwnershipSnapshotAdmin(admin.ModelAdmin):
    list_display  = ("snapshot_date", "character_id", "character_name", "main_character_id", "corporation_id")
    list_filter   = ("snapshot_date",)
    search_fields = ("character_id", "character_name")
    ordering      = ("-snapshot_date",)

    def has_add_permission(self, request):
        return False


@admin.register(CharacterLifecycleEvent)
class CharacterLifecycleEventAdmin(admin.ModelAdmin):
    list_display  = ("fecha", "evento", "character_name", "main_character_id", "estado_anterior", "estado_nuevo")
    list_filter   = ("evento",)
    search_fields = ("character_name", "character_id")
    ordering      = ("-fecha",)

    def has_add_permission(self, request):
        return False


@admin.register(TicketsConfig)
class TicketsConfigAdmin(admin.ModelAdmin):
    list_display    = ("tag", "enabled", "baserow_base_url", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (None, {
            "fields": ("tag", "enabled", "updated_at"),
        }),
        ("Baserow", {
            "description": "URL base y token de SOLO LECTURA de Baserow para el sync de tickets. "
                           "Esto es para LEER: la web no escribe aquí nunca.",
            "fields": ("baserow_base_url", "baserow_token"),
        }),
        ("n8n — acciones desde la web", {
            "description": "Koru NO escribe en Baserow: le pide a n8n que escriba, y así Discord "
                           "se entera del cambio. Pon aquí el webhook del workflow «K1 Claim desde "
                           "Koru» y el mismo secreto que en su credencial Header Auth. "
                           "Vacíos, el botón «Reclamar» ni aparece.",
            "fields": ("n8n_webhook_url", "n8n_webhook_secret"),
        }),
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ("tipo", "numero", "discord_ticket", "main_character_name",
                     "estado", "tipo_detalle", "claim_name", "visible_piloto", "alerta_peligro", "fecha")
    list_filter   = ("tipo", "estado", "visible_piloto", "alerta_peligro")
    search_fields = ("main_character_name", "numero", "discord_ticket", "asunto")
    ordering      = ("-fecha", "-baserow_row_id")
    readonly_fields = ("synced_at",)

    def has_add_permission(self, request):
        return False  # La puebla el sync


# ---------------------------------------------------------------------------
# Tax lunar — destinatarios y tarifa de la alianza
# ---------------------------------------------------------------------------

@admin.register(MoonTaxRecipient)
class MoonTaxRecipientAdmin(admin.ModelAdmin):
    list_display  = ("entity_name", "entity_id", "is_active", "expected_location_name")
    list_filter   = ("is_active",)
    search_fields = ("entity_name", "entity_id")


@admin.register(MoonAllianceFee)
class MoonAllianceFeeAdmin(admin.ModelAdmin):
    list_display  = ("_quien", "isk_por_fractura", "valid_from", "notes")
    list_filter   = ("valid_from",)
    search_fields = ("structure_name", "notes")
    fields        = ("structure_id", "structure_name", "isk_por_fractura",
                     "valid_from", "notes")

    @admin.display(description="Aplica a")
    def _quien(self, obj):
        return obj.structure_name or obj.structure_id or "TODAS las lunas (por defecto)"


# ---------------------------------------------------------------------------
# Regalos de la fiesta — R1
#
# La campana, los destinatarios y los rangos se montan aqui. Las aportaciones
# las detecta `sync_gift_contributions`, asi que se ven pero no se crean a mano.
# ---------------------------------------------------------------------------

class GiftTierInline(admin.TabularInline):
    model = GiftTier
    extra = 0
    fields = ("orden", "nombre", "umbral_min", "papeletas", "color")
    ordering = ("orden",)


class GiftRecipientInline(admin.TabularInline):
    model = GiftRecipient
    extra = 0
    fields = ("entity_name", "entity_id", "is_active", "acepta_contratos",
              "acepta_isk", "wallet_division", "expected_location_id",
              "expected_location_name")


@admin.register(GiftCampaign)
class GiftCampaignAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "estado", "ventana_desde", "ventana_hasta",
                     "fecha_evento", "precio_modo")
    list_filter   = ("estado",)
    search_fields = ("nombre",)
    inlines       = (GiftRecipientInline, GiftTierInline)
    fieldsets = (
        (None, {"fields": ("nombre", "estado", "ventana_desde", "ventana_hasta", "fecha_evento", "notes")}),
        ("Valoración", {
            "fields": ("precio_modo", "usar_percentil", "spread_max_pct", "desviacion_max_pct"),
            "description": "Jita sell es lo que costaría comprar el regalo; es lo que se ahorra quien lo "
                           "recibe. El percentil evita que una sola orden rara decida un rango. Los dos "
                           "umbrales marcan para valorar a mano, nunca descartan.",
        }),
    )


@admin.register(GiftRecipient)
class GiftRecipientAdmin(admin.ModelAdmin):
    list_display  = ("entity_name", "entity_id", "campaign", "is_active",
                     "acepta_contratos", "acepta_isk", "wallet_division")
    list_filter   = ("is_active", "campaign")
    search_fields = ("entity_name", "entity_id")


@admin.register(GiftTier)
class GiftTierAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "campaign", "umbral_min", "papeletas", "orden")
    list_filter   = ("campaign",)
    ordering      = ("campaign", "orden")


class GiftContributionItemInline(admin.TabularInline):
    model = GiftContributionItem
    extra = 0
    can_delete = False
    fields = ("type_name", "quantity", "es_bpc", "precio_unitario",
              "valor_linea", "precio_fuente", "requiere_valoracion", "motivo")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(GiftContribution)
class GiftContributionAdmin(admin.ModelAdmin):
    list_display  = ("_quien", "campaign", "origen", "valor_estimado",
                     "valor_ajustado", "estado", "fecha", "aviso")
    list_filter   = ("campaign", "origen", "estado", "requiere_valoracion")
    search_fields = ("main_name", "donante_name", "fuente_key")
    date_hierarchy = "fecha"
    inlines = (GiftContributionItemInline,)
    # Se puede ajustar el valor y validar; lo que detecto el sistema se mira,
    # no se reescribe: el precio es el del momento en que se aporto.
    readonly_fields = ("campaign", "origen", "fuente_key", "donante_id", "donante_name",
                       "main_char_id", "main_name", "contract_id", "assignee_id",
                       "acceptor_id", "acceptor_name", "contract_type", "esi_status",
                       "price", "reward", "volume", "start_location_id",
                       "start_location_name", "entry_id", "wallet_division", "reason",
                       "fecha", "valor_estimado", "valor_fuente", "valor_consultado_en",
                       "requiere_valoracion", "ubicacion_rara", "cobra_isk", "sin_main",
                       "aviso", "detected_at", "updated_at")

    def has_add_permission(self, request):
        return False  # Las detecta el sync

    @admin.display(description="Quién", ordering="main_name")
    def _quien(self, obj):
        return obj.main_name or obj.donante_name or obj.donante_id


# ---------------------------------------------------------------------------
# Regalos — R3: sorteos
#
# Mientras no estan las pantallas de gestion (R3b), el admin ES la herramienta:
# las acciones de cerrar, sortear y verificar estan aqui y hacen lo mismo que
# haran los botones.
# ---------------------------------------------------------------------------

class RaffleEntrantInline(admin.TabularInline):
    model = RaffleEntrant
    extra = 0
    fields = ("main_name", "main_char_id", "origen", "externo", "papeletas",
              "rango_nombre", "valor_aportado", "motivo")
    readonly_fields = ("valor_aportado", "verificado_esi")
    ordering = ("-papeletas", "main_name")


class RafflePrizeInline(admin.TabularInline):
    model = RafflePrize
    extra = 0
    fields = ("orden", "origen", "descripcion", "contribution", "valor",
              "isk_del_fondo", "type_id", "donante_name")
    ordering = ("orden",)


@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "campaign", "tipo", "estado", "_participantes",
                     "_premios", "cerrado_en", "sorteado_en")
    list_filter   = ("campaign", "tipo", "estado")
    search_fields = ("nombre",)
    inlines       = (RaffleEntrantInline, RafflePrizeInline)
    actions       = ("accion_cerrar", "accion_sortear", "accion_verificar")
    readonly_fields = ("semilla", "semilla_hash", "cerrado_en", "sorteado_en",
                       "anulado_por", "anulado_en", "creado_por", "created_at")
    fieldsets = (
        (None, {"fields": ("campaign", "nombre", "tipo", "orden", "estado")}),
        ("Reglas", {
            "fields": ("ponderar_por_rango", "excluir_propio_regalo", "permitir_repetir_ganador"),
            "description": "Se aplican al sortear. «Excluir el propio regalo» solo tiene efecto "
                           "en los sorteos comunitarios.",
        }),
        ("Limpieza demostrable", {
            "fields": ("semilla_hash", "semilla", "cerrado_en", "sorteado_en"),
            "description": "Al cerrar se publica el hash de la semilla; al sortear se revela la "
                           "semilla. Con eso, el roster y la bolsa, cualquiera reproduce el sorteo.",
        }),
        ("Anulación", {"fields": ("anulado_por", "anulado_en", "motivo_anulacion"),
                       "classes": ("collapse",)}),
    )

    @admin.display(description="Participantes")
    def _participantes(self, obj):
        return obj.entrants.count()

    @admin.display(description="Premios")
    def _premios(self, obj):
        return obj.prizes.count()

    @admin.action(description="1) Cerrar y publicar el hash de la semilla")
    def accion_cerrar(self, request, queryset):
        from . import raffles
        for r in queryset:
            try:
                h = raffles.cerrar(r)
                self.message_user(request, f"{r.nombre}: cerrado. Hash {h[:16]}…")
            except ValueError as exc:
                self.message_user(request, f"{r.nombre}: {exc}", level=messages.ERROR)

    @admin.action(description="2) Sortear")
    def accion_sortear(self, request, queryset):
        from . import raffles
        for r in queryset:
            try:
                res, inc = raffles.sortear(r)
                msg = f"{r.nombre}: {len(res)} premios repartidos"
                if inc:
                    msg += f" · {len(inc)} incidencias: " + "; ".join(inc[:3])
                self.message_user(request, msg,
                                  level=messages.WARNING if inc else messages.INFO)
            except ValueError as exc:
                self.message_user(request, f"{r.nombre}: {exc}", level=messages.ERROR)

    @admin.action(description="3) Verificar (recomputa desde la semilla)")
    def accion_verificar(self, request, queryset):
        from . import raffles
        for r in queryset:
            ok, detalles = raffles.verificar(r)
            self.message_user(request, f"{r.nombre}: " + "; ".join(detalles),
                              level=messages.INFO if ok else messages.ERROR)


@admin.register(RaffleEntrant)
class RaffleEntrantAdmin(admin.ModelAdmin):
    list_display  = ("main_name", "raffle", "origen", "_externo", "papeletas",
                     "rango_nombre", "valor_aportado", "motivo", "anadido_por")
    list_filter   = ("raffle", "origen", "externo")
    search_fields = ("main_name", "main_char_id", "motivo")

    @admin.display(description="De fuera", boolean=True)
    def _externo(self, obj):
        return obj.externo


@admin.register(RafflePrize)
class RafflePrizeAdmin(admin.ModelAdmin):
    list_display  = ("etiqueta", "raffle", "origen", "valor", "isk_del_fondo",
                     "donante_name", "orden")
    list_filter   = ("raffle", "origen")
    search_fields = ("descripcion", "donante_name")


@admin.register(RaffleDraw)
class RaffleDrawAdmin(admin.ModelAdmin):
    list_display  = ("raffle", "orden", "_ganador", "_premio", "created_at")
    list_filter   = ("raffle",)
    readonly_fields = ("raffle", "prize", "entrant", "orden", "hash_usado", "created_at")

    def has_add_permission(self, request):
        return False      # Los resultados salen del sorteo, no se escriben a mano

    @admin.display(description="Ganador")
    def _ganador(self, obj):
        return obj.entrant.main_name

    @admin.display(description="Premio")
    def _premio(self, obj):
        return obj.prize.etiqueta


@admin.register(RaffleRosterFilter)
class RaffleRosterFilterAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "notes", "created_at")
    search_fields = ("nombre",)


@admin.register(GiftDelivery)
class GiftDeliveryAdmin(admin.ModelAdmin):
    """Para mirar y para arreglar un caso raro. Lo normal se hace en la pantalla."""
    list_display  = ("draw", "estado", "contract_id", "emparejado_por",
                     "aceptado_en", "cerrado_en")
    list_filter   = ("estado", "emparejado_por", "draw__raffle")
    search_fields = ("draw__entrant__main_name", "draw__prize__descripcion", "nota")
    readonly_fields = ("draw", "detectado_en", "aceptado_en", "updated_at")

    def has_add_permission(self, request):
        return False      # La ficha nace con la tirada, no se escribe a mano


# ---------------------------------------------------------------------------
# Reclutamiento
# ---------------------------------------------------------------------------

@admin.register(RecruitQuestion)
class RecruitQuestionAdmin(admin.ModelAdmin):
    """El formulario de solicitud se edita aquí, sin tocar código."""

    list_display  = ("orden", "etiqueta", "clave", "tipo", "obligatoria", "activa")
    # ⚠ Django no admite que la PRIMERA columna sea editable sin decirle cuál
    # es el enlace a la ficha (admin.E124). El enlace es la etiqueta.
    list_display_links = ("etiqueta",)
    list_editable = ("orden", "obligatoria", "activa")
    list_filter   = ("activa", "tipo")
    search_fields = ("clave", "etiqueta")
    ordering      = ("orden", "id")

    fieldsets = (
        ("La pregunta", {
            "fields": ("etiqueta", "ayuda", "tipo", "opciones", "obligatoria"),
            "description": "«Elegir de una lista» usa el campo Opciones; los otros dos lo ignoran.",
        }),
        ("Dónde va", {"fields": ("orden", "activa")}),
        ("Identificador", {
            "fields": ("clave",),
            "classes": ("collapse",),
            "description": "⚠ Enlaza esta pregunta con las respuestas ya guardadas. "
                           "Si lo cambias, las fichas antiguas dejan de saber a qué "
                           "contestaban. Para cambiar una pregunta a fondo: crea otra "
                           "y desactiva ésta.",
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # ★ No se borra: se desactiva. Borrar la pregunta no borra las respuestas
        # que ya dio la gente, pero deja esas fichas sin saber qué se preguntó.
        return False


class RecruitNoteInline(admin.TabularInline):
    model = RecruitNote
    extra = 0
    readonly_fields = ("autor", "autor_nombre", "texto", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False      # Las notas se escriben en la ficha, no aquí


@admin.register(RecruitApplication)
class RecruitApplicationAdmin(admin.ModelAdmin):
    """Para mirar y para desatascar un caso raro. Lo normal va en la pantalla."""

    list_display  = ("main_character_name", "estado", "fase", "claim_por",
                     "discord_channel_id", "created_at")
    list_filter   = ("estado", "created_at")
    search_fields = ("main_character_name", "motivo_cierre")
    date_hierarchy = "created_at"
    inlines = [RecruitNoteInline]

    # ⚠ Todo esto es historia: quién aprobó qué y cuándo, y el retrato del
    # piloto al solicitar. Editarlo a mano sería reescribir lo que pasó.
    readonly_fields = ("user", "main_character_id", "main_character_name",
                       "respuestas", "instantanea", "instantanea_en",
                       "ok_reclutadores_por", "ok_reclutadores_en",
                       "ok_asuntos_por", "ok_asuntos_en",
                       "ok_directores_por", "ok_directores_en",
                       "claim_por", "claim_en", "cerrada_por", "fecha_cierre",
                       "created_at", "updated_at", "fase")

    def has_add_permission(self, request):
        return False      # Una solicitud nace del formulario, no del admin


class RecruitConfigForm(forms.ModelForm):
    """
    ★ Los roles se ELIGEN de una lista, no se teclean. Un id de Discord son 18
    dígitos: copiarlos a mano es una invitación a que uno salga mal, y un id mal
    copiado aquí es un canal que no ve quien tiene que verlo.

    ⚠ La lista se le pide a Discord. Si Discord no contesta, el campo se queda
    como estaba —texto JSON— en vez de impedir guardar la configuración: no
    poder tocar nada porque un servicio externo está caído sería peor.
    """

    class Meta:
        model  = RecruitConfig
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from . import discordapi
        try:
            opciones = discordapi.listar_roles()
        except Exception as exc:
            self.fields["roles_ver"].help_text = (
                "No se ha podido consultar Discord para ofrecer la lista "
                f"({exc}). Escribe los ids a mano, como lista JSON.")
            return

        actuales = [str(x) for x in (self.initial.get("roles_ver") or [])]
        self.fields["roles_ver"] = forms.MultipleChoiceField(
            choices=opciones,
            initial=actuales,
            required=False,
            widget=forms.SelectMultiple(attrs={"size": min(len(opciones), 14)}),
            label="Roles que ven el canal",
            help_text="Ctrl+clic para marcar varios. La lista viene de tu Discord.",
        )

        # Las categorías y el canal de aviso, igual: elegidos, no tecleados.
        # ⚠ Cada uno en su try: que no se pueda listar una cosa no tiene por qué
        # dejar la otra sin lista.
        self._lista(discordapi, "categoria_id", discordapi.CATEGORIA,
                    "Categoría donde van los canales",
                    "Los canales de reclutamiento nacerán dentro de ésta.")
        self._lista(discordapi, "avisar_en", discordapi.CANAL_TEXTO,
                    "Avisar en",
                    "Dónde avisar de que hay solicitud nueva. Déjalo vacío para no avisar.")

    def _lista(self, discordapi, campo, tipo, etiqueta, ayuda):
        from django import forms as f
        try:
            opciones = discordapi.listar_canales(tipo)
        except Exception:
            return      # se queda como texto libre, con su id a mano
        actual = str(self.initial.get(campo) or "")
        # El vacío va SIEMPRE, aunque el campo tenga valor: si no, no habría
        # forma de dejar de avisar una vez elegido un canal.
        self.fields[campo] = f.ChoiceField(
            choices=[("", "— ninguno —")] + opciones,
            initial=actual, required=False, label=etiqueta, help_text=ayuda)

    def clean_roles_ver(self):
        # Se guardan como lista de textos: los ids de Discord son demasiado
        # grandes para un entero de 32 bits y en JSON se irían a notación
        # científica si alguien los tratara como números.
        return [str(x) for x in (self.cleaned_data.get("roles_ver") or [])]


@admin.register(RecruitConfig)
class RecruitConfigAdmin(admin.ModelAdmin):
    """Dónde nacen los canales de reclutamiento y quién los ve."""

    form = RecruitConfigForm

    list_display = ("__str__", "categoria_id", "prefijo_canal", "updated_at")

    fieldsets = (
        ("Interruptor", {
            "fields": ("activo",),
            "description": "Apagado: la solicitud se guarda igual, pero no se crea canal. "
                           "La pantalla del reclutador la enseña marcada como «sin canal».",
        }),
        ("Discord", {
            "fields": ("categoria_id", "prefijo_canal", "roles_ver", "avisar_en"),
            "description": "⚠ Los ids se copian de Discord con el modo desarrollador activado "
                           "(clic derecho → Copiar id). Los roles se eligen de la lista: "
                           "quien no esté marcado no verá el canal.",
        }),
    )

    def has_add_permission(self, request):
        # Una sola configuración. La crea la migración.
        return not RecruitConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
