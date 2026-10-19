# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico, con el `0.x` indicando que la API interna puede moverse.

## [0.11.0] — 2026-10-19

Regalos, R3b completo: la pantalla de sorteos. **Con esto la fiesta se puede
celebrar entera desde la web, sin shell y sin admin.**

### Añadido

- **Sorteos** (`/koru/regalos/sorteos/`): listado con estado, gente, premios y el
  hash publicado de cada uno.
- **Detalle de sorteo** con todo lo del día de la fiesta:
  - **Constructor de roster**: filtrar por state y por rango, **ver a quién saca**
    y solo entonces fijarlo. La previsualización no escribe nada.
  - **Alta a mano** con motivo obligatorio, resuelta contra ESI: vale para alguien
    que no está en la corp ni en el Auth.
  - **Bolsa de premios**: exclusivos del CEO, regalos aportados que aún no están en
    ninguna bolsa, y la **caja de pegado** que valora contra Jita, arma lotes
    equilibrados y los crea como premios.
  - **Cerrar → sortear → verificar**, y anular entero con motivo.
- Los sorteos de tipo especial solo los ven y tocan quienes tengan `gift_ceo`; para
  el resto salen en el listado como «lo lleva el CEO».

### Decisiones

- **El filtro viaja al POST en JSON.** Así se fija exactamente lo que se vio en la
  previsualización, no lo que diga el formulario al reenviarse.
- **Un despachador con `accion`** en vez de diez URLs: son diez acciones pequeñas
  sobre el mismo objeto y partirlas solo añade sitios donde perderse.
- Los states del filtro **se leen de la base de datos**, no de una lista escrita a
  mano que se quedaría vieja.

## [0.10.0] — 2026-10-19

Regalos, R3b (primera mitad): la pantalla de los directores. Hasta ahora validar y
ajustar valores obligaba a pasar por el admin de Django.

### Añadido

- **Gestión de regalos** (`/koru/regalos/gestion/`, permiso `gift_manage`):
  KPIs de la campaña, lista de aportaciones con filtros por estado y origen, el
  desglose de ítems con el motivo de cada uno sin precio fiable, y el ranking por
  persona con su rango.
- Validar, **ajustar el valor a mano** y descartar, cada uno desde su fila.
- Entrada de menú para directores, estacional como la del piloto: sin campaña
  abierta no se pinta.

### Decisiones

- **Cambiar el valor o descartar exigen nota.** No es burocracia: es el registro de
  por qué se decidió así, y alguien preguntará. Validar sin tocar nada no la pide.
- **Los KPI se calculan sobre toda la campaña, no sobre el filtro.** Si no, al
  filtrar por «por revisar» el total aportado bajaría y parecería que se ha perdido
  dinero.
- El valor a mano admite `1.500.000.000` y `1500000000`: el director escribe como
  le sale, no como le conviene a la base de datos.

## [0.9.1] — 2026-10-19

### Corregido

- **Lo que está sin valorar ya no parece no haber aportado nada.** Un BPC o algo
  sin mercado vale 0 hasta que un director lo valora, así que el total salía corto
  y el piloto leía un rango más bajo del que le toca — y si era su única
  aportación, la tarjeta llegaba a decirle «todavía no has aportado nada a la
  fiesta». Ahora tanto la tarjeta como «Mi aportación» dicen cuántas cosas están
  esperando valoración y que el rango puede subir.

## [0.9.0] — 2026-10-19

Regalos, R6: pegado desde el juego y armador de lotes. Módulo `lotes.py`, con el
núcleo puro igual que `raffles.py`.

### Añadido

- `parse_pegado`: lee el portapapeles de EVE (TSV). Aguanta el inventario
  completo, nombre+cantidad y nombre suelto, y busca la cantidad como el primer
  campo entero después del nombre, no por posición fija.
- `resolver_tipos`: resuelve nombres contra el SDE **en todos los idiomas**.
- `armar_lotes`: reparte N objetos en K lotes equilibrados (LPT) y nivela con ISK
  por inundación. Devuelve la dispersión, los avisos y **cuánto ISK faltaría para
  dejarlos a la par**.

### Las trampas que esto resuelve

- ⚠ **El idioma del cliente.** Si el director tiene EVE en español, el pegado trae
  nombres en español; buscar solo contra `name` (inglés) no encontraría nada y
  parecería que el sistema está roto. Las columnas de idioma se descubren por
  **introspección**: dar por hecho un `name_es` que no existe revienta la consulta.
- ⚠ **El separador de miles también cambia** (`1.234` / `1,234`). Como la cantidad
  es siempre entera, se limpian los dos sin ambigüedad.
- Lo que no se reconoce **se devuelve aparte**, nunca se descarta en silencio.

### Lo que el armador dice en vez de disimular

- Un lote que se dispara, nombrando el objeto que lo arrastra.
- Que los lotes **no han quedado igualados**, mirando la dispersión y no solo el
  máximo: un reparto puede no tener ningún lote disparado y aun así estar al 106%
  porque los de abajo se quedan cortos.
- Que hay menos objetos que lotes.

Un objeto indivisible muy caro no lo arregla ningún algoritmo. Lo que hace el
armador es decirlo y ofrecer la cifra para arreglarlo a mano.

## [0.8.0] — 2026-10-19

### Añadido

- `preview_roster` admite **tramos**: `valor_max` (excluido, para que los tramos
  encajen sin solaparse ni dejar hueco) y `rangos`, que filtra por el nombre del
  rango calculado.

### Por qué

La estructura de la fiesta son **cuatro ruletas por rango de aportación**, no una
con papeletas ponderadas: compites solo contra quien aportó lo mismo que tú. Con
solo `valor_min`, quien aportó 10 B habría salido también en el roster del primer
rango. Filtrar por `rangos` es la vía limpia, porque el tramo lo define el propio
`GiftTier` y las cifras no se repiten en dos sitios.

## [0.7.1] — 2026-10-19

### Cambiado

- El contacto del User-Agent que se envía a ESI pasa a la dirección noreply de
  GitHub. Estaba en **dos** sitios de `tasks.py`, no en uno, y viajaba a CCP en
  cada petición además de estar en el repositorio público.
- Un comentario de `tasks.py` llevaba el nombre real del autor en vez del alias.
  Corregido; barrido del repo entero a cero apariciones.

## [0.7.0] — 2026-10-19

### Añadido

- **Alta de participantes por nombre, contrastada contra ESI** (`anadir_por_nombre`):
  para cuando el CEO quiere meter a alguien que no está en la corp ni en el Auth.
  Se teclea el nombre y se resuelve en ese momento.
- `RaffleEntrant.externo` y `verificado_esi` (migración `0029`): quien no existe en
  Alliance Auth queda marcado, y en el admin sale con su propia columna.

### Notas

- **Se mira primero en la base de datos del Auth**: a ESI no se le pregunta lo que
  ya sabemos. Solo se sale a internet si el nombre no está en casa.
- ★ **Verificado en vivo**: `POST /universe/ids/` **no da error con un nombre que
  no existe — lo omite de la respuesta**. Sin emparejar explícitamente el nombre
  pedido con el devuelto, un nombre mal escrito entraría con el id de otro.
- El User-Agent se toma de `tasks.py` con un import **perezoso**: hacerlo arriba
  arrastraría celery entero por una cadena y abriría la puerta a un import circular.

## [0.6.0] — 2026-10-19

Regalos, R3a: el motor de sorteos. Sin pantallas todavía — se opera desde el
admin, donde están las acciones de cerrar, sortear y verificar.

### Añadido

- Modelos `Raffle`, `RaffleEntrant`, `RafflePrize`, `RaffleDraw` y
  `RaffleRosterFilter` (migración `0028`).
- Módulo `raffles.py` con el motor. El núcleo (`sortear_core`) es una función
  **pura**: ni Django ni base de datos, así que se prueba en una mesa.
- **Limpieza demostrable**: al cerrar se genera una semilla y se publica su
  SHA-256; al sortear se revela la semilla. Con eso, el roster y la bolsa —los
  tres congelados— cualquiera reproduce el sorteo. `verificar()` lo recomputa y
  compara; probado manipulando una fila a mano, y la caza.
- El sorteo **no usa el `random` de Python**: cada tirada sale de
  `sha256("<semilla>:<premio>:<intento>")`, reproducible con cualquier
  herramienta en cualquier lenguaje.
- Constructor de roster: `preview_roster` (filtra y **enseña** sin escribir),
  `fijar_roster` (congela filas, no la consulta) y `anadir_por_meritos`, que pide
  motivo obligatorio y marca al participante como manual.
- Reglas por sorteo: ponderar por rango, que no te toque tu propio regalo, y si
  un ganador puede repetir.

### Notas

- **Las ruletas especiales del CEO no necesitaron código propio**: son un sorteo
  con roster manual y premios de origen `exclusivo`. Ese era el objetivo de
  separar el sorteo de la aportación.
- Un regalo solo puede estar en una bolsa (`OneToOne`), o se sortearía dos veces
  lo mismo.
- Anular es en bloque y con motivo: nunca se borra una tirada suelta en silencio.

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
