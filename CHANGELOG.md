# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico, con el `0.x` indicando que la API interna puede moverse.

## [0.26.0] — 2026-10-22

### Añadido

- **Abrir una auditoría de Asuntos Internos desde la ficha del Auditor (K2).**
  El Auditor ya detectaba; ahora desde la misma pantalla se abre el caso. El
  botón pide un motivo —obligatorio, mínimo 10 caracteres, porque una auditoría
  cuyo único rastro es «la abrió el Auditor» no le sirve a nadie dentro de tres
  meses— y se lo pasa a n8n, que crea el canal en Discord con los permisos de
  siempre, la ficha en la tabla 1702 con el Main ya enlazado y el Claim a
  nombre de quien la abrió. Antes había que irse a Discord, acordarse del
  comando y volver a escribir el nombre a mano.
- Guarda contra duplicados: **una auditoría abierta por piloto**. Si ya hay
  una sin cerrar, el botón lleva a su ficha en vez de abrir un segundo canal
  para el mismo caso.
- La tarjeta de tickets del piloto ahora aparece aunque no tenga ninguno, para
  que el botón esté donde se mira el riesgo y no en otra pantalla.

### Notas

- Hacen falta **dos** permisos: `auditor_access` para estar en la pantalla y
  `tickets_asuntos_internos` para abrir el expediente. Ver el riesgo de alguien
  y abrirle un caso no son la misma autoridad.
- Koru sigue sin escribir en Baserow: todo pasa por el webhook de n8n.
  Requiere importar `K2 Auditoría desde Koru` y colgarlo del Switch de K1.

## [0.25.2] — 2026-10-22

### Corregido

- **El arreglo de la 0.25.1 rompió el pie de dos tarjetas.** El alto se fijaba
  en el `parentNode` del canvas, que en varias tarjetas es el `card-body`
  entero — con sus etiquetas y su texto explicativo debajo. Al darle 90 px, lo
  de abajo se salía y se montaba encima del bloque siguiente: en el embudo,
  «Ya terminadas» aparecía pisando el título de Reclutamiento. Ahora el canvas
  se envuelve en su propia caja y el alto va ahí.

## [0.25.1] — 2026-10-22

### Corregido

- **Las gráficas ocupaban media pantalla.** Chart.js, si le dejas, estira las
  barras hasta llenar el contenedor: el embudo, con una sola barra, salía como
  un rectángulo azul gigante. Ahora el alto se ata al **número de barras** (34 px
  cada una, entre 90 y 520) y se apaga `maintainAspectRatio`, que es quien
  provocaba el estirón. Los donuts y el volumen mensual quedan a 300 px.

## [0.25.0] — 2026-10-22

### Corregido

- **El embudo de reclutamiento estaba montado sobre el campo equivocado.** Se
  apoyaba en `Fase`, que casi nadie rellena: sumaba 165 de 573. El campo que sí
  tienen las 573 es **`Estado`**. Lo que pasa es que `Estado` mezcla tres cosas
  —dónde está la solicitud, cómo acabó, y si está cerrada— así que ahora se
  clasifican en Koru.
  - **Sin tocar Baserow.** La alternativa era partir el campo en tres y migrar
    573 filas; los valores ya se distinguen solos, así que no hace falta. El
    campo `Fase` queda de adorno: no se borra, solo se deja de usar.
  - Se compara **sin acentos y en minúsculas**, porque en Baserow conviven
    «Se marcho» y «Se marchó» según quién creara la opción.
  - Un estado que no sepamos clasificar **no desaparece**: sale entre las
    terminadas. Si alguien añade una opción allí, esto lo canta.
- **«A IT» aparecía con 150 tickets y 0% cerrados, como si fueran 150 tickets
  abandonados.** No lo son: esa tabla lleva **desde mayo de 2025** sin un ticket
  nuevo — se usaba para apuntar updates del Auth y ya no se usa. Ahora cualquier
  tabla sin movimiento en seis meses sale marcada como **histórica**, atenuada y
  con la fecha del último. Se deja a la vista en vez de esconderla: ocultar
  datos es otra forma de mentir, pero presentarlos sin contexto también.

### Añadido

- **Gráfico «Cómo acabaron las solicitudes»**: Pasa a Corp, Pasa a Academia,
  Rechazado, Se marchó, Fue a otra corp. Solo las que terminaron con una salida
  clara; las que están en curso viven en el embudo.

## [0.24.0] — 2026-10-22

### Añadido

- **Cambiar el estado de un ticket desde la web.** Selector en la ficha, junto a
  «Reclamar», que pide a n8n el cambio por el mismo webhook y el mismo secreto —
  una acción más, no configuración nueva.
  - **Los estados los dice Baserow, no nosotros.** `sync_tickets` lee las
    opciones del campo `Estado` de cada tabla y las guarda. Una lista escrita a
    mano se desincronizaría el día que alguien añada un estado allí, y el fallo
    saldría al guardar, en la cara del director y sin que nadie entienda por
    qué. Si esa lectura falla, el sync no se rompe: los estados son un extra.
  - **Solo tres tablas tienen `Estado`**: reclutamiento, directores y soporte.
    En IT y Asuntos Internos no aparece el selector porque el campo no existe.
  - **Esto NO cierra el ticket, y lo dice.** Cerrar de verdad es lo que hace W5
    desde Discord: vuelca la transcripción, sube el fichero y archiva. Desde la
    web solo cambia la etiqueta. La confirmación lo avisa, porque si no, alguien
    marcará «Archivado» creyendo que ha cerrado y se quedará sin transcripción.
  - En Discord queda una línea diciendo quién lo cambió y que fue desde la web.
    Si ese aviso falla, la ejecución **no** falla: el estado ya está escrito y
    sería dar un error por algo que sí se hizo.

Los nodos para n8n están en `documentacion/n8n/K1 v2 - nodos nuevos (estado).json`,
con las instrucciones dentro.

## [0.23.2] — 2026-10-22

### Corregido

- **Los campos del webhook de n8n no salían en el admin.** La 0.23.0 los añadió
  al modelo y creó su columna, pero `TicketsConfigAdmin` define `fieldsets`
  explícitos y no se incluyeron: el formulario los ocultaba. Resultado práctico:
  no había dónde poner la URL, y el sitio que más se le parecía era el campo de
  Baserow — que es justo donde no van. Ahora tienen su propia sección,
  **«n8n — acciones desde la web»**, con la explicación de para qué es.
- De paso, la sección de Baserow dice ahora explícitamente que es **para leer**,
  para que no se confunda con la otra.

## [0.23.1] — 2026-10-22

### Corregido

- **Los tres export CSV se saltaban el permiso de su propia pantalla.** Solo
  pedían estar logueado, y vuelcan la tabla entera de la corp: cada piloto con
  su minería, sus bounties y su PvP. La pantalla equivalente sí exigía permiso
  —`dashboard` pide `basic_access`, `pvp_dashboard` pide `pvp_access`— así que
  bastaba con usar la URL de al lado para saltárselo. Cualquier usuario del
  Auth, incluido un recluta sin permisos de Koru, podía descargárselo todo.
  Ahora cada CSV pide **el mismo permiso que su pantalla**.

  Encontrado barriendo todas las vistas expuestas en `urls.py` contra sus
  decoradores. De paso quedó comprobado que las demás están bien: las que solo
  llevan `permission_required` no necesitan `login_required`, porque ese
  decorador ya manda al login a los anónimos; y las de tickets filtran por
  permiso dentro, con `_tickets_allowed`.

## [0.23.0] — 2026-10-22

### Añadido

- **T3, primera pieza: reclamar un ticket desde la web.** Con una decisión de
  fondo: **Koru no escribe en Baserow**, le pide a n8n que escriba.
  - La regla de junio era «un único dueño por dato»: Baserow es la fuente de
    verdad del ticket operativo y lo escribe n8n. Un `PATCH` directo desde Koru
    serían dos sistemas escribiendo la misma fila, justo lo que se decidió
    evitar — y encima **Discord no se enteraría**: reclamarías el ticket en la
    web y en el canal seguiría figurando sin reclamar, con su botón intacto.
  - Koru manda un POST al webhook de n8n con cabecera `X-Koru-Token`, y n8n hace
    lo de siempre con sus credenciales: vincular el Claim en Baserow y editar el
    mensaje de Discord.
  - **El permiso se comprueba en Koru**, con los grupos de AA. El ticket guarda
    *quién* lo cogió; *quién puede cogerlo* lo decide el Auth. n8n solo
    comprueba que la llamada viene de Koru.
  - **El espejo local no se toca al reclamar.** Lo que vale es lo que quede en
    Baserow, y eso entra por `sync_tickets`. Escribirlo aquí «para que se vea
    ya» sería inventar un estado que quizá n8n no llegó a guardar.
  - El botón solo aparece si hay webhook configurado y el ticket no está ya
    reclamado: un botón que no va a funcionar es peor que no tenerlo.
  - Config nueva en *Configuración de Tickets*: `n8n_webhook_url` y
    `n8n_webhook_secret`. Vacíos = la web no escribe, que es como queda al
    actualizar.

## [0.22.0] — 2026-10-22

### Añadido

- **Reparto de la duración de las auditorías**, por tramos: menos de 1 minuto,
  de 1 a 10, de 10 a 60, y más de una hora, más las que no tienen marcas
  suficientes para medirse. Con mediana 1 min y P90 280 no hay «una duración
  típica»: hay **dos poblaciones** metidas en la misma fila, y un número del
  medio las tapa las dos.
- La tarjeta dice explícitamente lo que el dato **no** significa: las marcas
  miden **cuándo se hizo clic en el check**, no cuánto se revisó. Un auditor
  puede mirarlo todo y luego marcar los siete seguidos. El reparto describe el
  ritmo de los clics, no el esfuerzo, y presentarlo como lo segundo sería acusar
  a alguien con un dato que no lo sostiene.

## [0.21.5] — 2026-10-22

### Añadido

- **`python manage.py koru_plantillas_check`**, que busca los dos errores de
  plantilla que *no dan error*:
  - El **comentario corto escrito en varias líneas**. Django no lo reconoce y lo
    imprime tal cual en la página; no falla, no avisa, sale. Es el que nos mordió
    dos veces el mismo día, y uno de ellos llevaba meses saliendo en el tax
    lunar de cada piloto.
  - Las **etiquetas de bloque descuadradas**. Un `{% if %}` sin cerrar revienta
    al renderizar, pero solo cuando alguien entra en esa pantalla, que puede ser
    semanas después. `{% comment %}` entra en la lista a propósito: sin cerrar
    se come el resto de la plantilla en silencio.

  Devuelve 1 si encuentra algo, así que vale para un hook o para CI el día que
  lo haya. No sustituye a abrir la página y mirarla: evita que estos dos haya
  que buscarlos a ojo.

## [0.21.4] — 2026-10-22

### Corregido

- **Dos comentarios de Django se estaban imprimiendo en pantalla.** El
  comentario corto `{# … #}` es de UNA línea, y escrito en dos sale tal cual.
  Uno era de la 0.21.3 y salía en la ficha del ticket; el otro llevaba meses
  ahí, en `mi_tax_lunar.html`, imprimiéndose en la pantalla del tax lunar de
  cada piloto sin que nadie lo notara. Los dos pasan a `{% comment %}`, y se
  revisaron todas las plantillas del plugin: no quedan más.
- **Las miniaturas de la transcripción dejaban un pie de texto huérfano.** Los
  enlaces de Discord caducan —ese `?ex=…` es la fecha de expiración— así que en
  una transcripción de hace semanas no carga ninguna, y quedaba la explicación
  flotando sin nada encima. Ahora el bloque nace oculto y solo aparece si alguna
  imagen llega a cargar.

## [0.21.3] — 2026-10-22

### Corregido

- **La duración de una auditoría se cortaba en el último check.** El asunto trae
  «Aprobado por … · 21/10/2026, 0:54:14», seis minutos después, y ese tramo se
  perdía: el ticket 146 constaba de 5,3 minutos cuando duró 11,4. La aprobación
  solo puede **alargar** el intervalo, nunca adelantar el principio, porque se
  aprueba al terminar. De paso, ahora se puede medir una auditoría con **un solo
  check** si tiene aprobación; antes hacían falta dos y se descartaba.

### Añadido

- **Las imágenes pegadas dentro de la transcripción se ven.** Discord las deja
  como una URL cruda larguísima que ocupaba dos líneas y ni se podía pinchar —
  siendo la prueba de la auditoría, merecía verse. Ahora el texto pasa por
  `urlizetrunc` (que escapa el contenido y solo convierte los enlaces, así que
  una transcripción con HTML dentro no puede inyectar nada) y las imágenes salen
  como miniaturas debajo.
  - La extensión se comprueba sobre la ruta **antes del `?`**: los enlaces de
    Discord acaban en `?ex=…&is=…&hm=…` y mirando la URL entera no se
    reconocería ni un png.
  - Las de Discord caducan, así que la que no cargue se esconde sola en vez de
    dejar el hueco roto.

## [0.21.2] — 2026-10-22

### Corregido

- **Las auditorías salían con mediana 0 d**, que era cierto e inútil: una
  auditoría se hace del tirón —los checks van de las 0:42 a las 0:48— así que
  en días siempre vale cero. La hora venía en el mismo texto del check y se
  estaba tirando. Ahora `asuntos` se mide en **minutos** y cada fila de la tabla
  lleva su unidad.
- Los ejes de las barras salían con decimales (0,2 · 0,4) cuando lo que cuentan
  son tickets. No existe medio ticket.

## [0.21.1] — 2026-10-22

### Corregido

Las gráficas de T2, con los datos reales delante, enseñaron dos huecos:

- **Las 73 auditorías salían con 0 cerradas.** No es que no se cierren: la tabla
  de Asuntos Internos **no tiene campo `Fecha`**, y sin fecha de apertura no hay
  intervalo que medir, así que se caían enteras de los tiempos y ni siquiera
  aparecían en el volumen por mes. Ahora la apertura se toma del **primer
  `Check …`**: no es cuando nació el ticket, es cuando el auditor se puso con
  él, que para medir cuánto dura una auditoría es justo lo que interesa.
- **El embudo mentía por omisión.** Sumaba 165 de 573 solicitudes, porque la
  mayoría no tiene `Fase` rellena y no se pintaban; y mezclaba «Archivado»,
  «Completado» y «Rechazado» —que son finales, no fases— con «Con
  Reclutadores», aplastando la escala y escondiendo lo único accionable: cuánta
  gente está esperando ahora mismo. Ahora el gráfico enseña **solo las fases
  vivas**, con el total en curso en la cabecera, y las terminadas más las «(sin
  fase anotada)» van debajo como etiquetas, para que las partes sumen el total.

### Nota sobre los datos

`directores` solo tiene fecha de resolución en el **9,6%** de sus tickets, así
que su mediana sale de 34 de 353. Eso no es un fallo del código: es que nadie
rellena *Fecha resolución* en Baserow. Mientras siga así, ese número se lee con
pinzas.

## [0.21.0] — 2026-10-22

### Añadido

- **T2 completo: tiempos de resolución y embudo.**
  - **Cuánto se tarda en cerrar**, por tipo: mediana, P90, media y porcentaje de
    cerrados. Se da la **mediana** como número principal porque un ticket que se
    quedó abierto seis meses sin que nadie lo cerrara arrastra la media y hace
    parecer que se tarda el triple; el P90 cuenta cómo son los peores. `it` y
    `soporte` no tienen fecha de cierre en Baserow, así que ahí no se inventa
    ningún número.
  - **Embudo de reclutamiento** por `Fase`: cuántas solicitudes hay con
    Reclutadores, en Asuntos Internos y en Directores.
  - Los tickets con **fecha de cierre anterior a la de apertura** se apartan, se
    cuentan y se avisan. No son tiempos, son datos mal metidos, y mezclarlos
    solo serviría para que el número saliera más bonito de lo que es.
- **La carga por staff se agrupa por PERSONA, no por personaje.** Quien reclama
  con dos personajes distintos aparecía como dos personas y su carga real salía
  partida por la mitad. El Claim se resuelve ahora al main contra el Auth, y lo
  que no se puede resolver se enseña aparte con su nombre crudo en vez de
  esconderse: eso es justo lo que delata un Claim mal escrito.
  - **El rol no se guarda.** Quién puede coger qué ticket lo decide AA con sus
    grupos; duplicarlo en una tabla a mano solo garantiza que los dos registros
    se desincronicen en cuanto alguien cambie de puesto. El ticket guarda
    **quién**, no **con qué permiso**.
- **`fecha_cierre` sale a columna** en vez de quedarse en el JSON, porque cada
  tabla la llama distinto —«Fecha cierre», «Fecha resolución», y en auditorías
  no existe: hay que deducirla del último `Check …`, que es texto libre— y
  agregar tiempos escarbando un JSON por fila ni escala ni se puede indexar.

## [0.20.0] — 2026-10-22

### Añadido

- **T2 — los tickets de un piloto, dentro del Auditor.** Este era el premio de
  tener el espejo: ver los Asuntos Internos de alguien **al lado de su riesgo**,
  no en otra pantalla y buscándolo por nombre, que es justo el momento en que se
  deja de mirar. La tarjeta va arriba, antes del ciclo de vida, porque lo
  primero que uno quiere saber al abrir una ficha es si ya hubo una auditoría.
  Los de Asuntos Internos salen en rojo.
  - Se respeta el **mismo permiso** que en la pantalla de tickets: estar en el
    Auditor no da derecho a leer Asuntos Internos. Sin permiso no se consulta
    siquiera, para que no se pueda deducir nada por lo que falta.
  - Se buscan por **todos los personajes** del piloto, no solo por el main: el
    campo Main de Baserow lleva a veces el alt con el que se abrió el ticket.

### Corregido

- **El botón «Ficha Auditor» de un ticket llevaba a una ficha vacía** cuando el
  ticket estaba a nombre de un alt: mandaba a `/auditor/piloto/<id del
  personaje>/` y el Auditor espera el id del **main**. Ahora se resuelve antes
  de pintar el enlace. Y la URL se construye por su nombre en vez de pegada a
  mano, así que un cambio de prefijo ya no la rompe en silencio.

## [0.19.1] — 2026-10-22

### Corregido

- **Tickets huérfanos por una letra.** El cruce ticket → piloto se rompía con
  cualquier diferencia de mayúsculas: `Kimuxl muxia` no casaba con
  `kimuxl muxia`, ni `Tricky hunterz` con `Tricky Hunterz`. Lo curioso es
  **dónde** estaba el fallo: la consulta SQL sí casa sin mayúsculas —la
  colación de MariaDB es case-insensitive— y traía la fila correcta; lo que
  perdía el dato era el diccionario de Python, indexado con la grafía de la base
  y preguntado con la de Baserow. El nombre existía, la consulta lo encontraba,
  y se tiraba al guardarlo. Ahora se indexa normalizado por los dos lados.
- **Campos con dos nombres dentro** (`Kilyadent / Kilya_JDC`) ya no se descartan:
  se prueba el campo entero y luego cada trozo.
- El ticket guarda ahora la **grafía canónica de EVE**, no la que tecleó quien lo
  abrió, así que la pantalla enseña siempre el mismo nombre.
- `sync_tickets` dice al terminar **cuántos nombres no pudo casar**. Antes no
  había forma de saber que esto pasaba sin ir a buscarlo a mano.

## [0.19.0] — 2026-10-22

### Añadido

- **Regalos recibidos en el personaje del CEO.** Un contrato asignado a la corp
  lo puede aceptar cualquiera, así que los regalos se mandan al CEO. Un
  destinatario válido puede ser ahora un **personaje**: se leen sus contratos
  (`corptools_contract`) y sus donaciones de ISK (diario de cartera del
  personaje). Necesita que ese personaje esté auditado en corptools con
  contratos y cartera; si no lo está, el sync lo avisa en el log.
- **Todo lo que llega a un personaje entra como «Por revisar»** con la marca
  *personal*, y **no cuenta** para rangos, bote ni premios hasta que alguien lo
  valida: al CEO le llegan también ventas, pagos y traspasos, y es él quien
  elige qué es de la fiesta. Lo que se manda a sí mismo desde un alt ni aparece.
- **«Anotar a…» al validar**: el regalo se apunta al main de otro piloto
  (por nombre o id de cualquiera de sus personajes). Pide nota.

### Corregido

- **Las aportaciones descartadas resucitaban** en el siguiente sync: solo se
  protegían las validadas. Ahora el programa no toca nada que haya decidido una
  persona.

## [0.18.5] — 2026-10-20

### Corregido

- **El enlace del fondo salía también dentro del sorteo**, donde la bolsa de
  premios está a medio palmo: un enlace que te saca de donde ya estás es peor
  que no poner nada. Ahí el texto ahora dice «lo apuntas aquí abajo» y no lleva
  a ninguna parte. La tarjeta lo decide con `en_sorteo`.

## [0.18.4] — 2026-10-20

### Añadido

- **Las tres pantallas del módulo, enlazadas entre sí.** El recorrido real es
  aportaciones → sorteos → entregas, y hasta ahora había que volver al menú
  lateral entre paso y paso. Gestión lleva ahora a *Sorteos y bolsa de premios* y
  a *Entregas*.
- **El fondo responde a la pregunta que provoca.** Mirando el bote, lo siguiente
  que uno piensa es «vale, ¿y dónde apunto lo que compré?». La tarjeta ahora lo
  dice y enlaza: en la bolsa de premios del sorteo, marcando «sale del fondo».

## [0.18.3] — 2026-10-20

### Añadido

- **`LICENSE`**, que faltaba. Dice lo mismo que ya decía el README —código
  interno de Rekium, todos los derechos reservados— pero donde se busca, y
  declarado en `pyproject.toml`.
- **Sitio para el fondo propio de la ruleta**, con su LEEME:
  `koru_stats/static/koru_stats/ruleta/`. Explica que el fichero va en la carpeta
  de estáticos recogidos y **no** en la del paquete dentro del `venv`, donde lo
  borraría el siguiente `pip install --upgrade`.
- **El README al día**: las cinco pantallas de regalos, sus tres permisos, las
  tres tareas nuevas, y una sección contando las cuatro ideas que sostienen el
  módulo, cómo se valora, por qué el sorteo es reproducible y de qué va lo del
  título del contrato.
- **Nota sobre Package Monitor**: lo ve como «Unknown» porque comprueba versiones
  contra PyPI y `koru-stats` se instala desde git. No está roto; es que no se
  publica. Queda escrito para que nadie lo investigue dos veces.

## [0.18.2] — 2026-10-20

### Corregido

- **El patrimonio diario contaba las copias de plano como si fueran el
  original.** Un BPC comparte `typeID` con su BPO, así que preguntar el precio
  por `typeID` devuelve el precio del original: un plano de investigación que en
  el mercado no vale nada sumaba como un BPO entero. Es exactamente el fallo que
  infló 610 B el patrimonio en koru-desktop, y la rama de regalos ya lo trataba
  bien mientras esta foto seguía mintiendo. Ahora `blueprint_copy = 1` vale 0;
  los BPO se siguen valorando, porque su precio sí es el suyo.
  - **La historia anterior no se puede rehacer**: los assets son estado actual,
    no hay forma de saber qué había hace tres meses. Las fotos viejas se quedan
    con su número inflado, así que en la gráfica habrá un **escalón hacia abajo**
    el día que esto entre. No es una caída de patrimonio: es el día que dejó de
    mentir.
- **`run_koru_ore_and_summary` y `run_koru_aggregations` estaban definidas dos
  veces.** Un pegado duplicado, con la primera copia de `run_koru_aggregations`
  cortada a media función. Python se quedaba con la segunda, así que el
  comportamiento era el correcto, pero quien leyera el fichero leía código
  muerto. Fuera la copia, y el docstring bueno —que se había quedado en la
  muerta— recuperado.

## [0.18.1] — 2026-10-19

### Corregido

El diagnóstico contra 365 días de datos reales —la primera vez que la rama de
contratos veía algo que no fuera una prueba— destapó que la detección proponía
basura con cara de regalo. Tres filtros que no estaban:

- **Los courier.** A la corp le llegan contratos de logística a diario, y cuatro
  de ellos iban a nombre del destinatario de regalos. Un courier no es un regalo.
  Ahora solo cuenta `item_exchange`.
- **Los que nadie aceptó.** Había contratos en `deleted` y `outstanding` con
  ítems dentro: cosas que se ofrecieron y se quedaron ahí. Apuntarlos es decirle
  a alguien que aportó algo que la corp nunca recibió. Ahora solo cuentan los
  terminados.
- **Las compras.** En un `item_exchange` el `price` lo paga el destinatario: si
  hay precio, la corp está comprando, no recibiendo un regalo.
- Además se saltan los contratos **sin nada incluido** (a precio 0 y vacíos son
  alguien *pidiendo* cosas a la corp, y salen a puñados): creaban una aportación
  de 0 ISK por cada uno.

Los filtros van dentro del subselect que deduplica, no fuera: filtrando solo en
el `SELECT` exterior, el `MIN(id)` podría elegir una fila descartada y el
contrato se perdería entero.

El propio diagnóstico mentía a medias y también se arregla: avisaba de estas
cosas pero la ingesta no hacía caso de los avisos. Ahora separa lo que **descarta**
de lo que es solo una advertencia, y dice de cada contrato si cuenta o se salta.

## [0.18.0] — 2026-10-19

### Añadido

- **R5: entrega y seguimiento.** Pantalla nueva *Koru → Entregas* con toda la
  campaña en una sola tabla —no una por sorteo, porque la pregunta de verdad es
  «¿qué me queda por mandar?»— y la máquina de estados
  `por mandar → contrato puesto → aceptado → cerrado`, más `entregado a mano`
  para lo que no pasa por un contrato (ISK, un trade, algo dado en fleet).
  - **El título del contrato es la clave del invento.** Emparejar por contenido
    es imposible: un premio puede ser un lote suelto, ISK o una nave con su
    fitting. Lo que sí es fiable es que el director ponga `Yoiul #<id>` en el
    título; la pantalla lo da hecho y se copia con un clic. Si lo pone, el
    emparejamiento es exacto; si no, se intenta por descarte **y solo cuando no
    hay ninguna duda** (un premio pendiente y un contrato libre). Con dos y dos
    se espera a que lo diga un humano: decirle a alguien que ya cobró cuando no
    ha cobrado es el error que no se puede cometer aquí.
  - Se miran las **dos** tablas de corptools (contratos de la corp y de los
    personajes auditados), deduplicando por `contract_id`: el mismo contrato
    sale en las dos cuando el director lo manda desde su personaje y encima está
    auditado.
  - Se acepta el contrato puesto a **cualquier alt** del ganador: el premio se
    manda muchas veces al alt que está en la estación, y mirando solo el main
    media gala quedaría como no entregada.
  - Un contrato **rechazado o caducado devuelve el premio a pendientes** con
    nota. Sin eso se quedaría como «puesto» para siempre.
  - `GiftDelivery` va **aparte** de `RaffleDraw` a propósito: la tirada es un
    hecho sellado y no se toca nunca; la entrega cambia, se corrige y se reabre.
  - Tarea `sync_gift_deliveries`, repetible y barata: no toca nada cerrado ni
    entregado a mano.

## [0.17.0] — 2026-10-19

### Añadido

- **El fondo es ahora la fiesta, no un catálogo de naves**: cruzan el logo de la
  corp, el retrato del CEO, la cara de **cada participante** y el render de
  **cada premio**. Las caras salen redondas y con aro dorado; el logo, con un
  halo en rojo de corp. El pozo se baraja (en orden saldrían todos los retratos
  seguidos y se notaría el truco) y pasa uno cada 7 s, porque con uno cada 18 s
  la mayoría no llegaría a salir en toda la gala.
  - El CEO sale de `EveCorporationInfo.ceo_id`, que el Auth ya mantiene: ni un
    ajuste nuevo que nadie recuerda poner ni una llamada a ESI en plena gala. Si
    la corp es cerrada ESI devuelve `ceo_id = 1`, que no es nadie, y se descarta.
- **Aire de Yoiul**: nieve cayendo con vaivén —reciclando los copos al salir por
  abajo, así que no se crea ni se destruye nada en todo el sorteo— y dos
  cortinas de aurora verde y morada que respiran muy despacio. Todo pintado, sin
  imágenes que haya que distribuir con el plugin.
- **Hueco para un fondo propio**: si se deja una imagen en
  `koru_stats/static/koru_stats/ruleta/fondo.jpg`, manda esa y lo demás queda
  por debajo. A propósito **no** se usa el tag `static`: con el almacenamiento
  por manifiesto del Auth, pedir un fichero que no está no da un 404, revienta
  la plantilla con `ValueError`.

### Corregido

- **Un comentario de Django de los cortos, escrito en dos líneas**, se imprimía
  tal cual en la cabecera de la proyección. El de varias líneas es
  `{% comment %}`.
- **La ventana pequeña se comía el botón de girar** y no había forma de llegar a
  él: la página tenía `overflow: hidden`. Ahora las ruedas tienen suelo de
  tamaño (240 px) y lo que no cabe se baja con la rueda del ratón. En el
  proyector no sobra nada, así que la barra no llega a aparecer.

## [0.16.2] — 2026-10-19

### Añadido

- **Sello «ENTREGADO» sobre lo ya repartido.** El nombre y el premio que ya han
  salido se apagan en la rueda —porción en gris, retrato o render sin color,
  rótulo tachado— y encima del retrato se estampa un sello rojo. Lo repartido
  **no se borra de la rueda**: borrarlo cambiaría el número de porciones a mitad
  de gala y la rueda bailaría entre tirada y tirada; además la gente quiere
  seguir viendo quién va cayendo. El sello se pone **al cantar el resultado**, no
  al acabar la tirada, así que ya está puesto antes de que nadie pueda volver a
  girar.

### Corregido

- **Dos premios con el mismo nombre** («Lote 1» repetido) hacían que la rueda
  parara siempre en la misma porción, porque se buscaba con `indexOf`. Ahora se
  busca la primera porción **que no esté ya repartida**.

## [0.16.1] — 2026-10-19

### Corregido

- **Las ruedas se salían de una ventana baja**, comiéndose hasta el botón de
  girar: estaban dimensionadas solo por ancho. Ahora el alto manda igual que el
  ancho (`min(42vw, 560px, 52vh)`), y la cabecera, el pie, el retrato y los
  rótulos se encogen con la altura disponible.
- **La demo no enseñaba ni retratos ni naves**, que era justo lo que había que
  ver: inventaba `character_id` —así que EVE devolvía el avatar por defecto— y
  creaba los premios sin pasar por el adivinador de `type_id`. Ahora coge
  **pilotos reales del Auth** cuando los hay y resuelve los nombres de los
  premios **contra el SDE**, así que enseña renders de verdad y de paso ejercita
  el adivinador con los mismos datos que usa la web. Al terminar dice cuántos
  premios salieron con imagen y cuántos pilotos eran reales.

### Nota de historial

Las versiones 0.15.0 y 0.16.0 viajaron en el mismo commit (`3db4969`): se editaron
ficheros mientras el bloque de la 0.15.0 estaba pendiente de lanzar, así que su
`git add` se llevó también lo de la 0.16.0. Los dos tags apuntan ahí. El código es
correcto; lo que no cuadra es el relato.

## [0.16.0] — 2026-10-19

### Añadido

- **La ruleta se viste con los colores de la corp**, leídos del propio logo: se
  cargan sus píxeles en un canvas y se saca el color de marca. No hay que
  configurar ningún código de color, y vale para cualquier corp.
- **Naves de fondo cruzando despacio**, y no unas cualquiera: **las de los premios
  de ese sorteo**. El fondo cuenta lo que se está jugando.

### Lo que la medición cambió

Comprobado contra el logo real de Rekium: sus tres colores dominantes son **el
mismo ámbar** (`#feb23d`, `#f6ac3b`, `#eaa438`). Muchos logos de corp son de un
solo color, así que coger «los dos más frecuentes» habría dejado la pantalla
monocroma y sin contraste. Ahora el dominante es el color protagonista y el acento
sale de otro tono del logo **solo si de verdad es distinto**; si no, se deriva un
complementario. Para Rekium: ámbar `#feb23d` + cian `#2294d3`.

También verificado que `images.evetech.net` permite leer el canvas desde otro
dominio; si algún día dejara de permitirlo, salta la excepción y se queda la
paleta de serie.

## [0.15.0] — 2026-10-19

Las ruedas, como las de verdad.

### Añadido

- **Retrato del piloto** en cada porción de la rueda de nombres y **render de EVE**
  en cada premio, también junto al rótulo del ganador.
- `RafflePrize.type_id` (migración `0031`), que se **adivina solo** desde la
  descripción al crear el premio: «Orca (prueba)» → Orca → su render. Limpia
  paréntesis, cantidades y prefijos de lote, y prueba de lo más específico a lo
  más general. Si no acierta deja el campo vacío y se pinta un icono: **nunca
  inventa un id**. Los premios que salen de un contrato o de un lote cogen el
  `type_id` del ítem más valioso.

### Cambiado

- **Texto radial dentro de su porción**, volteado en la mitad izquierda para que
  nunca se lea del revés — y a diferencia de la versión horizontal, esto sigue
  valiendo con la rueda girada, que es como se queda al parar.
- Ruedas más grandes (560 px).

### El detalle que costó dos vueltas

El recorte del texto sale del **espacio radial libre**, no de un número a ojo: con
la imagen puesta el texto llegaba al radio 77 y la imagen empezaba en el 63, así
que «Satanax Lefour» salía comido; y por dentro se metía bajo el disco central.
Ahora se mide contra el hueco real entre el disco y la imagen.

## [0.14.2] — 2026-10-19

### Corregido

- **Las ruedas no giraban sobre su centro**, sino alrededor de un punto fuera de
  la pantalla. En SVG, `transform-origin: 50% 50%` no se resuelve contra el propio
  elemento si no se dice con **`transform-box`** respecto a qué caja. Con
  `transform-box: fill-box` el origen pasa a ser el centro del dibujo, que es el
  eje de la rueda. Verificado forzando rotaciones de 137° y 221°: las dos ruedas
  se quedan centradas bajo su aguja.

### Sabido y aceptado

Al girar, las etiquetas giran **con** la rueda, así que al pararse quedan en
ángulos arbitrarios. Es lo que hace cualquier ruleta de verdad, y el ganador se lee
en el texto grande de debajo, no en la porción.

## [0.14.1] — 2026-10-19

### Corregido en las ruedas

- **La mitad de las etiquetas salían boca abajo.** Las porciones de la izquierda
  invertían el texto, que en un proyector canta muchísimo. Ahora el texto es
  siempre horizontal: se rota el grupo y se deshace la rotación en la etiqueta.
- **Las etiquetas largas se encabalgaban.** Con etiquetas horizontales el límite
  no es el ángulo sino el **ancho**: con 4 porciones cabe un texto larguísimo en
  grados de sobra y aun así pisa al vecino de arriba. Recorte por ancho y radios
  alternos para que las vecinas no estén a la misma altura.
- **El techo de la rueda baja de 24 a 12 porciones.** El criterio es el proyector,
  no cuántas quepan dibujadas: por encima de doce la letra baja de lo que se lee
  desde el fondo de una sala, y la tira vertical se lee mejor.
- Ruedas algo más grandes y la cuenta de premios pendientes visible de entrada.

## [0.14.0] — 2026-10-19

### Cambiado — la ruleta ahora son DOS ruedas

- **Ruedas circulares**: una de premios y otra de nombres, girando a la vez. La de
  premios para antes; después para la de nombres y aparece el ganador.
- **Regla de legibilidad, no manía**: rueda redonda hasta 24 porciones; si un
  sorteo concreto lleva más gente, esa rueda cae sola a la tira vertical. Lo
  decide el número, porque con 60 nombres los segmentos quedan de dos grados.
- ★ **El orden de revelado sale de la semilla** (`orden_de_revelado`). Si la rueda
  de premios gira, el público entiende que el premio también sale al azar: ahora
  eso es **verdad** y además se reproduce, en vez de ser una animación bonita
  sobre una lista decidida a dedo.

### Añadido — ambiente de fiesta

- Campo de **estrellas** de fondo y **fuegos artificiales** al revelar cada
  ganador, hechos a mano con canvas: ni librerías ni imágenes que descargar,
  porque esto corre en el portátil que mueve el proyector.
- Logo de la corp en la cabecera, sacado del destinatario de la campaña — no hay
  un ajuste nuevo que nadie recuerde poner.

### Añadido — herramientas de prueba

- `manage.py koru_regalos_demo`: monta un sorteo **«PRUEBAS — borrar»** con gente y
  premios inventados para ensayar la ruleta sin tocar la fiesta. `--gente 30`
  fuerza la tira, `--sortear` lo deja listo para proyectar y `--borrar` se lo lleva
  entero sin dejar huérfanos. Repetirlo lo reemplaza, no lo acumula.
- `manage.py koru_regalos_diagnostico`: **no escribe nada**. Lee los contratos y el
  diario de cartera de verdad y enseña qué detectaría, qué marcaría y por qué.
  Sirve para estrenar la rama de contratos sin esperar a que llegue un regalo, y
  para ver qué tipos de movimiento hay realmente antes de fiarse de los filtros.
  Con `--valorar` pide además los precios a Jita.

## [0.13.0] — 2026-10-19

Regalos, R4: **la ruleta**. Pantalla de directo para proyectar en la fiesta.

### Añadido

- `/koru/regalos/sorteos/<id>/ruleta/`: página **completa, sin el menú de Alliance
  Auth**, en oscuro y a pantalla grande. Se abre desde el botón «Proyectar la
  ruleta» del sorteo.
- Revela **premio a premio**, al ritmo que marque quien presenta: botón o barra
  espaciadora. Primero se ve el premio, después se gira, después el ganador con su
  retrato.
- El hash de la semilla va impreso en la propia pantalla, para que se vea mientras
  se sortea.
- Abajo se va formando la lista de lo ya repartido.

### Decisiones

- ★ **La página no decide nada.** El resultado ya está en `RaffleDraw`; esto solo
  lo anima. Si el ganador lo eligiera el navegador, cualquiera con la consola
  abierta podría discutirlo.
- **Tira vertical tipo tragaperras, no ruleta circular.** Con 60 nombres los
  segmentos de una rueda quedan de dos grados y no se lee nada en un proyector.
- **Giran TODOS los del roster**, no solo los premiados: si solo giraran los
  ganadores, el primero que se fijara vería que la tira ya sabe el resultado.
- Los nombres se pasan con `json_script` y se pintan con `textContent`: un
  personaje con `<b>` en el nombre no rompe la página.

## [0.12.0] — 2026-10-19

### Añadido

- **El fondo de la fiesta.** El ISK que aporta la gente no es un premio: es un bote
  con el que el CEO compra naves y con el que el armador nivela los lotes. Ahora se
  ve en las tres pantallas: **entrado / comprometido / disponible**, en rojo y con
  aviso si se compromete más del que entró.
- `RafflePrize.isk_del_fondo` (migración `0030`): cuánto de cada premio salió del
  bote. Al crear un premio exclusivo hay casilla para marcarlo, y el ISK que el
  armador usa como mortero se marca solo.

### Por qué un decimal y no un sí/no

Un lote lleva objetos **más** ISK de mortero, así que la parte pagada con el fondo
es parcial. Con un booleano habría que mentir en un sentido o en el otro.

### ⚠ Lo que esto evita

**Comprar con el fondo es un traspaso, no valor nuevo.** Si el CEO compra una Gila
de 500 M con el bote y la mete como premio, ese ISK ya se contó cuando entró como
aportación: sumarlo otra vez inflaría el valor de la fiesta y cualquiera que eche
la cuenta a mano nos pillaría.

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
