# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico, con el `0.x` indicando que la API interna puede moverse.

## [0.5.0] — 2026-10-19

Regalos, R2: la pantalla del piloto.

### Añadido

- **Mi aportación** (`/koru/regalos/mi/`, permiso `gift_access`): lo aportado, cómo
  se valoró cada ítem, el rango en el que cae y cuánto falta para el siguiente.
  Página propia y no una pestaña de Mi Dashboard, por el mismo criterio que
  «Mi Tax Lunar»: son preguntas distintas.
- **Entrada de menú estacional**: solo existe mientras hay una campaña abierta.
  Una fiesta son seis semanas al año; en enero desaparece sola.
- **Tarjeta en Mi Dashboard** con lo aportado y el rango, visible solo durante la
  campaña. Va como template tag (`{% koru_gift_card %}`) en vez de por contexto de
  la vista, para no tocar `mi_dashboard` — y si algo fallara, la tarjeta no pinta
  nada en vez de tumbar el dashboard.

## [0.4.1] — 2026-10-19

### Corregido

- `sync_gift_contributions` se habría tragado **los pagos del tax lunar como
  regalos**: van al mismo destinatario, son `item_exchange` y van a precio 0, así
  que encajan en el filtro uno por uno. Y aquí no se puede filtrar por contenido,
  porque un regalo es cualquier cosa. Ahora se saltan los contratos que ya están
  fichados como tax. Lo limpio del todo sigue siendo usar un destinatario
  distinto para los regalos.

## [0.4.0] — 2026-10-19

Regalos de la fiesta, R1: el Auth ya detecta y valora lo que aporta cada uno. Sin
pantallas todavía — se ve y se gestiona desde el admin.

### Añadido

- Modelos `GiftCampaign`, `GiftRecipient`, `GiftTier`, `GiftContribution` y
  `GiftContributionItem` (migración `0027`).
- Tarea `sync_gift_contributions`: detecta contratos de ítems y donaciones de ISK
  dentro de la ventana de la campaña, leyendo lo que **corptools ya trae**. No
  necesita scope ESI ni ingesta propia.
- Valoración contra el mercado real de **Jita 4-4** (Fuzzwork, una petición por
  lote de tipos deduplicados), guardada en columnas nuevas de `KoruMarketPrice`
  junto al `average_price` de la ESI, que se queda como contraste.
- Reglas explícitas de "este precio no me lo creo" → el ítem se marca para que lo
  valore una persona: sin órdenes, volumen menor que lo regalado, spread
  desorbitado, desviación fuerte frente al `average_price`, y **cualquier BPC**.
- Permisos `gift_access`, `gift_manage` y `gift_ceo`.
- Admin de campañas con destinatarios y rangos en línea; las aportaciones se ven
  y se ajustan, pero no se crean a mano.

### Notas

- Un BPC **comparte typeID con su BPO**, así que preguntar el precio por typeID le
  pondría a la copia el del original. Va siempre a valoración manual; el chivato en
  los ítems de contrato es el `raw_quantity` negativo.
- La deduplicación usa una columna `fuente_key` (`c:<contract_id>` / `w:<entry_id>`)
  en vez de restricciones únicas condicionales: MariaDB no soporta índices
  parciales y Django no llega a crearlas.
- Se guardan siempre los dos valores, `valor_estimado` y `valor_ajustado`. Una vez
  validada, la aportación no se recalcula: el precio justo es el del momento en que
  se aportó.

## [0.3.0] — 2026-10-19

Primera versión numerada de verdad. Hasta aquí el paquete declaraba `0.2.0` desde
hacía meses mientras el código crecía por debajo, así que este número **no refleja
un lote de cambios**: marca el punto a partir del cual cada despliegue tiene
versión y etiqueta propias.

### Añadido

- `CHANGELOG.md`.
- Clasificadores, autor y enlace al changelog en `pyproject.toml`.

### Cambiado

- **La versión vive solo en `koru_stats/__init__.py`.** `pyproject.toml` la lee con
  `dynamic = ["version"]`. Se acabó el `pip install --upgrade` que decía "already
  satisfied" y obligaba a `--force-reinstall --no-deps`.
- `[project.urls] Repository` apuntaba a un remoto que solo redirige; ahora apunta
  a `RoGiz7/AA-Koru`.
- README reescrito: documentaba un proyecto anterior (`rekstats`), con URLs
  `/rekstats/` cuando el prefijo real es `/koru/`, y un `pip install` a un
  repositorio que no existe.

### Eliminado

- `default_app_config` en `koru_stats/__init__.py`: Django lo ignora desde la 4.1.

## Antes de 0.3.0

Sin changelog. Lo desplegado hasta octubre de 2026, a grandes rasgos:

- Estadísticas de mineral y bounties, por corp y por personaje, con export CSV.
- PvP completo desde zKillboard + ESI: resumen, kill feed, actividad y ficha de
  piloto.
- Tax lunar v2: deuda por piloto y mineral con reparto por resto mayor, detección
  de contratos desde `corptools`, libro de saldos y validación por un director
  congelando la foto.
- Rentabilidad de lunas y tarifa de alianza por fractura.
- Auditor de comportamiento (F1-F3) y panel de Dirección: salud de corp,
  reclutamiento, grafo social y retención por cohortes.
- Tickets (T1) conectados al ecosistema n8n/Baserow.
