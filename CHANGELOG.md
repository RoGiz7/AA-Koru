# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico, con el `0.x` indicando que la API interna puede moverse.

## [0.47.1] — 2026-10-24

### Arreglado

- **De los tres paneles solo aparecía uno.** Los tres se registraban con la
  misma clase de hook, y **Alliance Auth identifica cada elemento del menú por
  la clase**: los tres colapsaban en una sola fila de `MenuItem`, creada por el
  primero y con el texto pisado por el último.
  - Se vio en el admin: una única entrada «Koru — Dirección» con **orden
    1200**, que es el de «Koru» a secas. El dato que lo delató no fue el
    nombre, fue el número.
  - Los once hooks antiguos funcionaban porque cada uno tenía su propia clase.
    El refactor los unificó en una — más limpio de leer y roto en producción.
  - Ahora hay tres subclases que no añaden nada: lo que aportan es **ser clases
    distintas**. Queda escrito en el código para que a nadie le tiente
    «simplificarlo» otra vez.

## [0.47.0] — 2026-10-24

### Cambiado

- **De once entradas de menú a tres paneles.** 🌀 Koru · 🌀 Koru — Gestión ·
  🌀 Koru — Dirección, cada uno una página con tarjetas.
  - ★ **El problema no era el número, era quién las veía.** Un miembro normal
    veía tres o cuatro entradas; un director, las once. El menú se ensuciaba
    justo para quien más deprisa necesita encontrar las cosas — el mismo fallo
    que tenía la ficha de solicitud antes de las pestañas.
  - Agrupadas **por lo que haces, no por rango**: un reclutador también es
    miembro, y con grupos de «miembros / mandos / dirección» estaría en dos.
    Que los tres paneles se parezcan a los tres niveles es consecuencia.
  - **Un panel sin nada dentro no se ofrece.** Un menú que lleva a una página
    vacía es peor que no tener el menú: quien lo pulsa no sabe si le falta un
    permiso o si la pantalla está rota.
  - El reparto vive en `paneles.py`: añadir una pantalla es una línea en una
    lista, no tocar los hooks.
  - ⚠ **Las tarjetas no son seguridad**: cada vista mantiene su
    `permission_required`. Esto decide qué se ofrece, no qué se puede abrir.
  - ⚠ Una ruta propia por panel, no una con parámetro: `MenuItemHook` hace
    `reverse(url_name)` a secas, y una ruta que necesita argumento reventaría
    al construir el menú — y un menú que revienta se lleva por delante **todo**
    el Auth, no solo Koru.
  - Las URLs de cada pantalla no cambian: los enlaces guardados siguen valiendo.

### Arreglado

- **«Únete a Rekium» la veía todo el mundo, también quien ya estaba dentro.**
  Un veterano de hace tres años tenía en su menú una invitación permanente a
  solicitar entrar en su propia corp.
  - Ahora desaparece cuando alguno de sus personajes está en una corp vigilada
    — el mismo dato que usa la tarea que detecta entradas, para no inventar un
    criterio nuevo que luego diga otra cosa. Y respeta `is_active`: una corp
    que se dejó de vigilar no debe seguir escondiendo la entrada.
  - Sigue **fuera de los paneles y arriba del todo**: quien la necesita es el
    que menos sabe moverse por el Auth.
  - ★ Si la comprobación falla, **se enseña**. Esconder la puerta de entrada
    por un error de base de datos es el peor de los dos fallos posibles.

### Verificado

- **Alliance Auth 5.3 no tiene submenús** — comprobado en
  `allianceauth/services/hooks.py`: ni `children` ni `folder`. De ahí que un
  panel sea una página y no un desplegable.

## [0.46.1] — 2026-10-24

### Arreglado

- **Los botones secundarios casi no se veían** sobre el fondo oscuro: el borde
  de `btn-outline-secondary` quedaba del mismo tono que el fondo. El botón
  estaba y funcionaba, pero no se veía — que para un botón es lo mismo que no
  estar.
  - ★ Se arregla con **un parcial de estilos compartido**, no botón a botón:
    esa clase sale en 28 sitios de 14 pantallas, y en varias la escribe
    JavaScript al vuelo (paginaciones, el «copiado» de los dashboards de
    lunas). Esos no se habrían arreglado tocando plantillas.
  - Un botón deshabilitado sigue viéndose apagado: eso **es** información.
  - Incluido de momento en reclutamiento (ficha, lista, asistente) y tickets
    (detalle y panel). El resto de pantallas lo heredarán añadiendo una línea.

## [0.46.0] — 2026-10-24

### Cambiado

- **La ficha de una solicitud va por pestañas**: Trámite · Lo que nos ha
  contado · Conversación · Notas · 🔒 Auditoría.
  - ★ **El problema era justo al revés de lo que parece**: cuantos más
    permisos tiene alguien, más bloques se le dibujan — así que la pantalla
    se volvía más larga precisamente para quien más rápido necesita encontrar
    las cosas. Dirección lo veía todo de golpe.
  - La pestaña de auditoría lleva **un contador de puntos obligatorios sin
    mirar**: se ve lo que falta sin abrirla.
  - Tras guardar un check se vuelve a la pestaña de auditoría, no al principio.
    En una lista de nueve puntos, tener que buscar dónde estabas cansa a la
    tercera vez.
  - El retrato del piloto se queda **fuera de las pestañas**, en su columna: es
    lo que se consulta mientras se mira cualquier otra cosa.
  - ⚠ **Las pestañas no son seguridad.** La de auditoría solo se dibuja si los
    checks llegaron a la plantilla, y la vista los pone a `None` para quien no
    puede leer reservadas. Lo que no se puede ver no llega a la página — y
    menos escondido detrás de un clic.
  - Cada check se colorea por su estado, para leer la lista de un vistazo.

## [0.45.0] — 2026-10-24

### Añadido

- **La auditoría de Asuntos Internos, dentro de la propia solicitud.** Ya no
  hay que irse a otra pantalla ni abrir otro ticket.
  - La lista de partida son los siete puntos de la tabla 1702 de Baserow:
    Auth, Personajes, Zkill, Skill Points, Omega, ISK, Assets. Se editan desde
    el admin, como las preguntas del formulario.
  - ★ **Cinco de los siete llegan ya resueltos**, con el dato al lado: Auth,
    Personajes, Skill Points, ISK y Assets salen de corptools. Un check que
    obliga a ir a buscar el dato a otro sitio es burocracia, no control.
  - **Zkill lleva el enlace del piloto ya montado.** Un check externo solo
    ahorra tiempo si se pincha en vez de buscar.
  - **Omega se queda manual**: no existe ese dato en corptools. Y los assets
    se cuentan, no se valoran: `corptools_typeprice` está vacía.
  - Dos puntos nuevos que el dato permitía y no estaban: **contactos** (a
    quién pone standing alto) y **actividad de la cuenta** (último login y
    total de entradas — retrata solo al que dice llevar años jugando con un
    personaje de hace tres semanas). Nacen **no obligatorios**: meterle a
    Asuntos Internos trabajo nuevo por la puerta de atrás, no.
  - ⚠ **Contactos NO dice «tiene contactos hostiles».** No existe una lista de
    quién es hostil para Rekium. Dice a quién aprecia; los nombres los
    reconoce una persona. Prometer más sería mentir en una auditoría.

- **Tres estados por punto, no una casilla**: correcto / duda / problema / no
  aplica.
  - ★ Con un sí/no, el auditor que tiene una sospecha blanda marca que sí
    —tampoco es un «no»— y esa sospecha se pierde justo antes de que Dirección
    decida. «Duda» existe para que quede escrita, y **exige una línea
    explicando qué se vio**.

- **El OK de Asuntos Internos se bloquea** si queda algún punto obligatorio sin
  mirar. Mismo motivo que la entrevista: quien lleva veinte auditorías da por
  hecho que miró algo que no miró, y el sistema es el único que se acuerda.

- **Se congela el dato que se vio.** corptools se actualiza solo: dentro de
  seis meses el saldo y los SP serán otros, y la auditoría tiene que poder
  explicar qué se miró **entonces**, no lo que hay hoy.

### Arreglado

- **El bug de identidad de W4b desaparece por construcción.** Los checks se
  estampaban con el nombre del CEO en vez del de quien pulsaba, porque n8n
  tenía que resolver la identidad por una cadena de lookups. Aquí quien marca
  es quien está logueado; no hay cadena que resolver.

### Seguridad

- **La pestaña de auditoría no llega a la página** para quien no puede leer
  notas reservadas: la vista manda `None`, no se esconde con CSS. Un
  reclutador no ve ni que existe — «hay una pestaña que no puedo abrir» ya es
  información sobre una investigación en curso.
- **Los checks no se avisan en el canal del solicitante.** Es el canal donde
  está él: contarle ahí que acaban de marcar algo como «duda» sería enseñarle
  la investigación.

### Verificado

- **La trampa de ids de corptools, cerrada de una vez** — no «a ojo», sino
  preguntándole a la base a qué tabla apunta cada clave ajena. Solo
  `characteraudit.character_id` apunta a `eveonline_evecharacter`; **todo lo
  demás cuelga del id del audit**: `characterasset`, `charactercontact`,
  `characterroles`, `clone`, `jumpclone`, `corporationhistory`, `skill`,
  `skillqueue`, `skilltotals`.
  - Hacía falta porque los dos joins devolvían filas para los 2354 personajes.
    Un join mal puesto aquí no revienta: **devuelve los datos de otra
    persona**, y en una auditoría eso es peor que un error.

## [0.44.0] — 2026-10-24

### Añadido

- **Un canal de aviso por paso, no uno para todo.** En la configuración hay
  ahora cuatro: solicitud nueva, le toca a Asuntos Internos, le toca a
  Dirección y falta la invitación.
  - ⚠ **No es comodidad, es una fuga.** Avisar en `#general-reclutamiento` de
    que Asuntos Internos tiene algo que revisar le está contando a los
    reclutadores que hay una revisión en marcha — justo lo que protegen las
    notas reservadas. Cada aviso va donde solo lo ve quien debe verlo.
  - Un canal vacío significa «no avisar de ese paso». No se inventa un destino.

### Arreglado

- **Las menciones ya no salen como `<@&951128547316076614>`.** En la ficha de
  reclutamiento y en la de tickets se traducen a `@Asuntos Internos`,
  `@Fulano` y `#canal`.
  - ★ **Se traducen al MOSTRAR, no al guardar.** Lo que Discord manda son ids
    y así se archiva la transcripción. Si se tradujera al guardar, todo lo ya
    archivado seguiría enseñando ids para siempre y un rol renombrado se
    quedaría congelado con el nombre viejo. Traduciendo al leer, el histórico
    entero se arregla solo y sin tocar un dato.
  - Para las personas se mira **primero en Auth**, que es gratis y además da el
    nombre que importa: el del personaje principal, no el apodo de Discord.
    Solo si Auth no lo conoce se le pregunta a Discord, y la respuesta se
    cachea una hora — también cuando no se sabe quién es, porque volver a
    preguntarlo en cada carga no lo va a averiguar mejor.
  - Un id que ya no existe sale como `@desconocido`. Si Discord no responde,
    se ven los ids: feo, pero la ficha se abre igual.

## [0.43.0] — 2026-10-24

### Quitado

- **El cog de Discord queda desactivado.** No está registrado en `hooks.py`; el
  código se conserva documentado por si se retoma.
  - El comando se quedaba colgado sin error ni respuesta. Se probaron cuatro
    cosas y ninguna lo resolvió.
  - **La causa raíz de no poder arreglarlo es que el log del `authbot` no
    escribe nada después del arranque.** Sin rastro, cada intento es una
    hipótesis que cuesta un despliegue. Antes de retomarlo, arreglar el log.
  - Lo que el cog ahorraba era abrir el navegador: comodidad, no capacidad.
    Todo lo que hacía está en la pantalla web, verificado.

### Añadido

- **La tarea se avisa en el canal de staff, con enlace directo a la ficha.**
  Cuando alguien da su OK, en `#general-reclutamiento` aparece a quién le toca
  ahora y el enlace a la solicitud.
  - ⚠ **En el canal de staff y no en el del piloto**: un mensaje de canal lo ve
    todo el que entra, y en el canal de la solicitud está el solicitante.
    Discord solo tiene mensajes efímeros como respuesta a un botón o comando,
    que es justo lo que se ha descartado.
  - Y es **mejor** que un efímero: el efímero desaparece y solo lo ve quien
    pulsó. Esto se queda, así que subiendo un poco se ve todo lo pendiente —
    una lista de tareas en un sitio que ya miran.

### El enfoque, fijado

El trabajo se hace **en el Auth**; Discord lo **refleja** y guarda la
conversación, que luego se transcribe con sus adjuntos. Una sola pieza que
mantener, y que no se rompe sola.

## [0.42.3] — 2026-10-24

### Corregido

- **El comando se quedaba colgado en «está pensando…» para siempre**, sin error
  y sin respuesta. No fallaba: **esperaba**. `sync_to_async` ejecuta por defecto
  (`thread_sensitive=True`) el código de Django en el hilo principal — que en un
  bot es justo el que atiende el bucle de eventos. Se quedaban esperándose el
  uno al otro.
- Con `thread_sensitive=False` va a un hilo aparte. **No es opcional** en un
  cog: cualquier acceso a la base desde aquí lo necesita.

El síntoma es la pista: un error se ve, un bloqueo no. Cuando un comando ni
responde ni falla, el sospechoso es el hilo, no el código.

## [0.42.2] — 2026-10-24

### Cambiado

- **El cog cuenta sus propios fallos.** El log del bot no escribe nada después
  del arranque, así que una excepción dejaba el comando colgado en «está
  pensando…» para siempre y sin rastro en ningún sitio. Ahora el error se
  responde en Discord: un fallo invisible pasa a ser uno que se lee.
- `ctx.channel.id` en vez de `ctx.channel_id` — el primero existe en todas las
  versiones, el segundo no siempre.

## [0.42.1] — 2026-10-24

### Corregido

- **El cog no cargaba: la librería no es discord.py, es py-cord.** Comprobado en
  producción: `py-cord 2.8.1`. No existe `discord.app_commands`, así que el
  import reventaba y el bot lo registraba como extensión fallida. Reescrito con
  `SlashCommandGroup` y `ctx.respond(...)`, y `setup()` **síncrono**, que es
  como lo llama py-cord.
- **Los comandos se registran en el servidor, no globalmente.** Los globales
  tardan hasta una hora en aparecer; los de guild son inmediatos. Sale de
  `DISCORD_GUILD_ID`; sin él se cae a global, que funciona pero tarda.

Fue el único trozo de la sesión escrito sin poder ejecutarlo, y falló por donde
se avisó. El fallo fue de los buenos: ruidoso, en el log del bot, y sin tocar
nada de lo que ya funcionaba.

## [0.42.0] — 2026-10-24

### Añadido

- **Cog de Discord**: los pasos de la solicitud se pueden dar desde su propio
  canal, sin abrir el Auth.
  - `/recluta estado` — en qué punto va
  - `/recluta entrevista [nota]` — marcarla hecha
  - `/recluta ok` — dar el OK al paso que toque
  - `/recluta invitacion` — marcar la invitación enviada
- Los comandos van escritos **en el propio mensaje de la ficha**: un comando que
  nadie sabe que existe es un comando que no existe.

### Decisiones

- **Comandos y no botones.** Los botones quedan mejor, pero los persistentes se
  pierden al reiniciar el bot si no se vuelven a registrar — y ese fallo no se
  nota el día que pasa, se nota semanas después cuando alguien pulsa y no ocurre
  nada. Los botones se pueden añadir encima más adelante.
- **El cog no decide nada**: llama a las mismas funciones de `recruit.py` que la
  pantalla web. Quién puede, en qué orden y qué se escribe está en un solo sitio.
- La respuesta al que ejecuta es **efímera**; lo que se anuncia al canal es otra
  cosa. Mezclarlas llenaría el canal de ruido.
- Si quien ejecuta **no tiene Discord vinculado** en el Auth, se le dice — pasa
  de verdad, y es mejor que dejarle ejecutando sin efecto.

### ⚠ Sin probar

El cog **no se ha ejecutado nunca**. Está comprobado que el Python es válido y
que usa la misma lógica que la web, pero las interacciones de Discord solo se
ven ejecutándolas. Cuenta con una o dos vueltas de ajuste.

Corre en el proceso `myauth:authbot`, así que **hay que reiniciarlo** para que
los comandos aparezcan, y Discord puede tardar unos minutos en registrarlos.

## [0.41.1] — 2026-10-24

### Cambiado (por dentro)

- **Las acciones de la cadena pasan a vivir en `recruit.py`**: marcar la
  entrevista, aprobar un paso, marcar la invitación y cerrar. La pantalla web ya
  solo las llama.
- Es el paso previo a los botones de Discord: si el cog reimplementara la
  lógica, aprobar desde Discord y aprobar desde la web harían cosas distintas a
  la primera modificación — y nadie se daría cuenta hasta que importara.
- `recruit.usuario_de_discord(uid)` traduce quien pulsa en Discord a su usuario
  del Auth, para que el cog **no tenga que mapear roles**: la persona que pulsa
  ya es un usuario con sus grupos.

Sin cambios visibles en la pantalla.

## [0.41.0] — 2026-10-24

### Añadido

- **La entrevista, con su hora y quién la hizo**, como primer paso de la cadena.
  Y **no se puede dar el OK de reclutadores sin marcarla** (se apaga con
  `exigir_entrevista` si algún día estorba): un expediente que dice «aprobado»
  sin que conste que alguien habló con la persona no cuenta lo que pasó.
- Al marcarla se puede dejar una nota, que va **a las notas del staff** y no a
  un campo escondido: es lo que el siguiente de la cadena necesita leer.

### Para qué sirve de verdad

Para medir **cuánto se tarda desde que entra una solicitud hasta que alguien
habla con la persona**. Ese es el número que dice si reclutamiento va bien, y
hasta ahora no existía.

⚠ **Lo que NO prueba:** si se pulsa «entrevista hecha» y el OK seguido, la hora
solo demuestra que alguien pulsó dos botones. Marcarla al terminar la charla, y
no al aprobar, es un hábito — ninguna validación puede garantizarlo.

## [0.40.0] — 2026-10-24

### Cambiado

- **La invitación la puede marcar quien tiene el rol in-game**, no solo quien
  esté en un grupo de AA. A quién puede invitar a la corp lo decide el CEO
  dentro del juego: sacarlo de ahí hace que la lista se mantenga sola — el día
  que alguien deja de ser Personnel Manager, deja de poder marcar invitaciones
  sin que nadie toque nada.
- Los grupos de AA siguen valiendo como **respaldo**, por si corptools no tiene
  el dato.

### Cuidado

- ⚠ **El rol es por corp.** En la base hay 258 personnel managers, y muchos son
  alts de nuestros miembros en corps ajenas —«The Dark Techno Club», «La
  Forja»…—. Mandar en otra corp no da derecho a invitar a la nuestra, así que
  se exigen **las dos cosas**: el rol y estar en una corp rastreada.
- ⚠ **Y otra vez los ids de corptools.** `characterroles.character_id` es el PK
  del **audit**, no el de `EveCharacter` — como `skilltotals` y
  `corporationhistory`. Van ya tres tablas con la misma trampa; comprobado
  contra producción antes de escribir la consulta.

## [0.39.1] — 2026-10-24

### Corregido

- **El botón «Todas» dejaba la lista vacía.** Mandaba `?estado=todas` y la
  vista lo trataba como si «todas» fuera un valor de la columna Estado, así que
  no casaba con nada — justo el botón que promete enseñarlo todo.

## [0.39.0] — 2026-10-24

### Añadido

- **Cada OK avisa a quien le toca ahora.** Reclutadores dan el suyo → ping a
  Asuntos Internos; Asuntos Internos → ping a Dirección; Dirección → ping a
  quien manda las invitaciones. Dar un OK y que nadie se entere de que ahora le
  toca a otro es como no darlo: la solicitud se queda esperando a alguien que
  no sabe que la espera. Cada rol se elige en la configuración.
- **Paso 4: «Invitación enviada».** ⚠ No es una aprobación — no dice «me parece
  bien», dice «ya está hecho». Va en sus propios campos y con su propio grupo:
  si se mezclara con los OK, el expediente no distinguiría quién **decidió** de
  quién **ejecutó**.
- **Detección automática de la entrada** (`recruit_detectar_entradas`): cuando
  el main del solicitante aparece en una corp rastreada, la solicitud se cierra
  sola como «Pasa a Corp» —o «Pasa a Academia» si es esa corp—, se deja nota y
  se felicita al piloto en su canal.
  - **El dato lo pone el juego, no una casilla.** Marcar «ya entró» a mano se
    olvida, y entonces quedan solicitudes esperando una invitación que se
    aceptó hace tres semanas.
  - `cerrada_por` se queda **vacío a propósito**: no la cerró nadie, la cerró el
    hecho de que el piloto entrara. Poner un usuario ahí sería atribuirle una
    decisión que no tomó.
  - Solo **cierra** solicitudes abiertas. Nunca reabre ni rechaza: si alguien se
    salió de la corp, eso es cosa del Auditor.
  - Cuál es la Academia sale de la **configuración**, no de adivinar por el
    nombre — adivinarlo sería inventarse el resultado de la solicitud de una
    persona.

⚠ **Dar de alta `koru_stats.tasks.recruit_detectar_entradas`** en el programador
(cada 15–30 min). Y rellenar en la configuración los tres roles nuevos y el id
de la Academia; sin eso, ni se avisa al siguiente ni se distingue el destino.

## [0.38.0] — 2026-10-24

### Corregido

- **Nadie se enteraba de que el canal existía.** Un canal privado recién creado
  aparece en la lista de Discord y ya está: ni al piloto ni a los reclutadores
  les saltaba nada. Ahora el primer mensaje **menciona al rol de reclutamiento
  y al piloto**, y además se avisa en el canal general con un enlace al nuevo.
  El rol se elige en la configuración (`Mencionar a`); vacío = no mencionar.
- El campo `avisar_en` llevaba configurado desde el principio **sin usarse**.
  Ahora sirve para algo.

### Añadido

- **Reabrir una solicitud cerrada por error**, mientras su canal siga vivo —las
  primeras 24 h—. El cierre **no se borra en silencio**: queda una nota
  automática con quién reabrió, cómo estaba cerrada y por qué. Limpiar los
  campos sin más dejaría la ficha como si nunca se hubiera cerrado, y eso es
  falso: el error también es historia.

### Decidido

- **Reabrir solo dentro de la ventana.** Después, el canal ya no existe y crear
  uno nuevo sobrescribiría la transcripción del primero — perder justo lo que
  esto existe para guardar. Cerrar por error se detecta en minutos, así que las
  24 h cubren el caso real. Si con el uso hace falta reabrir algo archivado,
  habrá que **acumular** transcripciones en vez de reemplazarlas.

## [0.37.0] — 2026-10-24

### Cambiado

- **Cerrar una solicitud ya no borra su canal.** Son dos decisiones distintas y
  una de ellas no tiene vuelta atrás; juntarlas hacía que una reversible
  arrastrase a la otra. Al cerrar, al piloto se le dice que **tiene 24 horas**
  antes de que el canal desaparezca: si quiere copiar algo, preguntar o
  despedirse, puede. Borrarlo en el mismo segundo en que se le dice que no es
  innecesariamente brusco.
- **Al piloto se le menciona** en lo que le afecta — los OK y el cierre — para
  que le salte la notificación. Un cambio en su solicitud que solo ve quien ya
  estaba mirando el canal no es un aviso, es un apunte.
- Botón **«Guardar y borrar ya»** para no esperar las 24 h, con el mismo
  permiso que cerrar: quien decide el final decide el archivo.

### Añadido

- Tarea `recruit_archivar_vencidas`: archiva y borra los canales de las
  solicitudes cerradas hace más de 24 h. **Si el mensaje promete que el canal
  desaparece, algo tiene que borrarlo de verdad** — si no, volveríamos a
  acumular canales habiendo prometido lo contrario, que es peor que no
  prometer nada.
  - Va una a una y cada una en su `try`: que falle un canal borrado a mano no
    puede dejar sin archivar a los demás. Lo que falla se reintenta en la
    siguiente pasada, porque sin transcripción no se borra nada.

⚠ **Hay que darla de alta en el programador de tareas** (cada hora vale). Hasta
entonces el botón manual funciona, pero el plazo de 24 h no se cumple solo.

## [0.36.0] — 2026-10-24

### Añadido

- **La conversación se guarda antes de borrar el canal.** Al cerrar una
  solicitud, Koru lee todos los mensajes del canal de Discord, los guarda en la
  ficha y **sólo entonces** borra el canal. Se pinta como chat, con el mismo
  formato que las transcripciones de los tickets viejos.
- **El progreso se anota en el canal**: quién reclama la solicitud, qué paso se
  aprueba y cómo se cierra. El aviso de cierre se publica **antes** de archivar,
  así que entra en la transcripción: queda escrito cómo acabó y quién lo decidió.

### Por qué

Hasta ahora estábamos en el peor sitio posible: ni se borraban canales (se
acumulaban) ni se guardaba nada (si alguien borraba uno a mano, se perdía la
entrevista). Y el expediente existe **precisamente** para conservar qué se
habló: una solicitud cerrada sin la conversación dentro es media solicitud.

Lo del progreso es el mismo fallo que arreglamos en los tickets viejos:
reclamabas en la web y en el canal seguía figurando sin reclamar.

### Cuidado

- **El orden no es negociable**: primero guardar, después borrar. Si el guardado
  falla, el canal **no** se borra y la pantalla lo avisa — una conversación
  perdida no se recupera; un canal de más se borra a mano en diez segundos.
- De los adjuntos se guarda **solo el nombre**. El enlace de Discord caduca a
  las pocas horas: guardarlo sería guardar un enlace muerto y hacer creer que
  el fichero sigue ahí.
- ⚠ El parser de conversaciones está **duplicado** con el de `ticket_detail`, a
  sabiendas: unificarlos al final de una sesión larga arriesgaba una pantalla
  que ya funciona. Si se toca el formato, hay que tocar los dos.

## [0.35.0] — 2026-10-24

### Añadido

- **Pantalla del staff de reclutamiento**: lista con el contador de abiertas,
  ficha con el retrato del piloto, las respuestas, las notas y la cadena de
  aprobaciones. Cada paso solo lo da quien tiene su grupo, y al que no le toca
  **se le dice quién tiene que darlo** en vez de esconderle el botón.
- No se puede adelantar un paso: aprobar el tercero sin el primero dejaría un
  expediente diciendo que pasó algo que no pasó.
- **Notas reservadas a Asuntos Internos y Dirección.** Sin esto, una nota del
  tipo «tiene un alt en una corp con la que tuvimos un problema, lo estamos
  mirando» la leería el reclutador de turno — que puede ser alguien que entró
  hace dos meses, o que conoce al solicitante.
- **Ver y aprobar no son lo mismo**: Asuntos Internos y Dirección entran a la
  pantalla aunque no tengan `recruit_manage`, porque su paso está dentro.

### Cuidado

- Las notas reservadas **ni se enseñan ni se insinúan** a quien no puede
  leerlas: se filtran en la consulta, no en la plantilla. «Hay algo que no
  puedo ver» ya es información, y quien escribe no debería tener que calcular
  si el hueco delata algo.
- Solo quien puede **leer** reservadas puede **escribirlas**: si no, cualquiera
  podría esconder una nota a quien tiene que verla.
- Lo ya escrito se queda como «todo el staff»: es lo que era cuando se escribió.

## [0.34.0] — 2026-10-24

### Añadido

- **Quién aprueba cada paso, configurable desde el admin** y con varios grupos
  por paso: reclutadores, Asuntos Internos, Dirección, y quién puede rechazar o
  cerrar. Se usan **grupos de AA**, no roles de Discord: aquí manda el Auth y
  los roles de Discord salen de él. Un sitio donde decidirlo, no dos.
- Cuando a alguien no le toca un paso, no se le esconde el botón: se le dice
  **quién tiene que darlo**, para que sepa a quién avisar.

### Por qué

En W4 el permiso era **una sola comprobación para todos los botones** — los
cinco roles podían pulsar cualquier paso. La cadena existía como secuencia, no
como reparto de autoridad, y así el registro de «quién aprobó» dice quién pulsó,
no quién tenía potestad.

### Cuidado

- **Un paso con la lista vacía no es «todos»: es «sin configurar»**, y entonces
  solo un superusuario puede darlo. Nacen vacías a propósito; sembrarlas con una
  suposición sería peor que obligar a decidirlo.

## [0.33.2] — 2026-10-24

### Corregido

- **El retrato enseñaba los SP y las corps de OTRA PERSONA.** En corptools no
  todos los `character_id` significan lo mismo:
  - `corptools_characteraudit.character_id` → PK de `EveCharacter`
  - `corptools_skilltotals.character_id` → PK del **audit**
  - `corptools_corporationhistory.character_id` → PK del **audit**

  El retrato cruzaba los dos últimos contra `EveCharacter`. No fallaba: cuando
  los números coincidían devolvía los datos de otro personaje. A RoGiz7 le
  salían 16,4 M de SP y 7 corps; los suyos son 657.755 y 4. Los demás alts
  salían «sin datos de ESI» teniéndolos.
- Comprobado que el fallo **no estaba en ningún otro sitio**: las otras
  consultas de historial usan la tabla de `alumni`, que es otra cosa.

### Nota de método

La primera «verificación» de ese join comprobaba que la consulta devolviera
filas, no que devolviera las correctas — y con eso pasó por buena. Para este
tipo de cruce la comprobación válida es mirar que el número de un personaje
conocido sea **el suyo**.

## [0.33.1] — 2026-10-24

### Cambiado

- **Los roles del canal se eligen de una lista**, no se teclean. La lista se le
  pide a Discord con el token que ya tiene el Auth, así que salen los roles
  reales con su nombre. Un id de Discord son 18 dígitos: copiarlos a mano es
  una invitación a que uno salga mal, y un id mal copiado es un canal que no ve
  quien tiene que verlo.
- Si Discord no contesta, el campo se queda como estaba —texto JSON— en vez de
  impedir guardar: no poder tocar la configuración porque un servicio externo
  está caído sería peor que escribir un id a mano.
- `@everyone` y los roles de bots no se ofrecen. Dar a `@everyone` permiso de
  ver un canal privado es exactamente lo contrario de lo que se busca.
- **La categoría y el canal de aviso también se eligen de una lista.** El canal
  se muestra con su categoría delante (`Reclutamiento / #general`): en un
  Discord grande hay tres canales llamados «general» y sin el contexto no se
  sabe cuál es cuál.
- Cada lista se pide por separado: que Discord falle al listar una cosa no deja
  la otra sin su desplegable.

## [0.33.0] — 2026-10-24

### Añadido

- **«Únete a Rekium»: el asistente del solicitante.** Entrada propia en el menú,
  visible para cualquiera que haya entrado al Auth aunque no tenga ningún grupo
  — que es justo a quien va dirigida. Cuatro pasos: personaje principal, alts
  (saltables), Discord, y el formulario. Cada paso se **verifica contra la base**
  al volver, no se fía de que el piloto diga que ya lo hizo.
- El formulario va **de una pregunta en una**, con las contestadas a la vista
  arriba. Se guarda un borrador en el navegador mientras se rellena: son seis
  preguntas, pero una pide pensar, y perder lo escrito por una recarga es la
  forma más tonta de perder un solicitante.
- **El canal de Discord lo crea Koru**, no n8n (`discordapi.py`), con la ficha
  del piloto publicada dentro. Configuración en *Reclutamiento — configuración*:
  categoría, prefijo del canal y roles que lo ven.

### Por qué directo a Discord y no por n8n

El Auth ya tiene bot y token, y ya los usa. Mandar a n8n algo que podemos hacer
aquí añade un workflow que mantener, un secreto más que cruzar y un sitio más
donde mirar cuando falle. En n8n se queda lo que **nace** en Discord —botones y
modales—, porque allí está el disparador.

### Decisiones

- **El canal se crea al enviar, no al aprobar**: la entrevista es el primer
  filtro, así que el reclutador necesita hablar antes de decidir.
- **Pero en segundo plano**: si Discord tarda o falla, la solicitud ya está
  guardada y nadie pierde el formulario. Lo que falle queda en `discord_error`
  y se ve en la pantalla del reclutador, no en un limbo silencioso.
- **La configuración nace apagada y sin categoría.** Mejor que las solicitudes
  salgan «sin canal» a que una migración se invente una categoría y aparezcan
  canales sueltos en la raíz del Discord.
- **Una solicitud abierta por persona.** Si ya tiene una en marcha se le enseña
  en qué punto va, no el formulario otra vez: dos solicitudes abiertas son dos
  reclutadores haciendo el mismo trabajo sin saberlo.
- Los permisos del canal son **los mismos que usan las auditorías** creadas
  desde Discord. Si aquí pusiéramos otros, dos canales del mismo tipo se
  comportarían distinto según quién los creó.

## [0.32.1] — 2026-10-24

### Corregido

- El admin de preguntas no arrancaba (`admin.E124`): Django no admite que la
  primera columna de la lista sea editable sin decirle cuál es el enlace a la
  ficha. El enlace es la etiqueta.

## [0.32.0] — 2026-10-24

### Añadido

- **El formulario de solicitud se edita desde el admin** (`RecruitQuestion`).
  Pregunta, ayuda, tipo, opciones, orden y si es obligatoria. La migración
  `0038` lo siembra con las seis preguntas acordadas; a partir de ahí manda el
  admin y tocar el código ya no cambia nada en producción.
- **Retrato del piloto** (`recruit.retrato`): personajes, SP, antigüedad de cada
  cuenta, corp actual, historial de corps y unas pocas señales objetivas. Todo
  de la base del Auth, sin llamar al ESI, así que el reclutador no espera.

### Decisiones

- **La etiqueta de la pregunta se guarda junto a la respuesta.** Si solo se
  guardara la clave, el día que alguien reescriba o borre una pregunta las
  solicitudes viejas quedarían con respuestas huérfanas: un texto sin saber a
  qué contestaba. Se guarda `{clave: {etiqueta, valor}}`, y el lector aguanta
  también el formato plano por si acaso.
- **Las preguntas no se borran desde el admin, se desactivan.** Borrar una no
  borra las respuestas que ya dio la gente, solo las deja sin contexto.
- **Las señales son señales, no un veredicto.** Cuenta recién creada, muchos
  saltos de corp, sin datos de ESI todavía. El reclutador filtra; si algo huele,
  para eso está el botón de abrir auditoría y Asuntos Internos detrás.
- `sp` puede venir vacío y eso **no** es un cero: corptools rellena en su propio
  ciclo, así que un personaje registrado hace diez minutos aún no tiene datos.
  La ficha lo dice; un 0 se leería como «cuenta vacía», que es lo contrario.

## [0.31.0] — 2026-10-24

### Añadido

- **El reclutamiento empieza a vivir dentro del Auth.** Modelos
  `RecruitApplication` y `RecruitNote`, migración `0037`. Todavía no hay
  pantallas: esto solo crea las tablas para poder construir encima.
- Permisos nuevos: `recruit_apply` y `recruit_manage`.

### Por qué

- La solicitud vivía en Baserow y se cruzaba con el Auth **por el nombre del
  personaje**. Ese cruce es el origen de la mitad de los fallos: en **12 de los
  últimos 36 tickets** el campo `Main` llegó vacío, y con él vacío W4 reventaba
  (`Cannot read properties of undefined`) antes de crear la auditoría — el
  reclutador pulsaba «aprobar» y no pasaba nada. Aquí el solicitante **es** un
  usuario del Auth: no hay nombre que casar, hay un `user_id`.

### Decisiones que quedan fijadas

- **Los estados son los mismos que en Baserow.** No se renombran aprovechando la
  migración: el histórico de 573 solicitudes se compara con esto.
- **Cada aprobación guarda quién y cuándo en su propia columna**, en vez de un
  campo «fase» que se pisa. Es la lección de los 282 tickets de Directores que
  se quedaron sin rastro de quién los cerró.
- **Se guarda un retrato del piloto al solicitar** (SP, corps, antigüedad),
  aunque esté en corptools: corptools refleja el *ahora*, y la pregunta que se
  hace cuando algo sale mal es «¿qué vimos cuando le aceptamos?».
- **Las notas del staff no se editan ni se borran.** Es el expediente de una
  persona; si se puede reescribir, deja de explicar por qué se decidió lo que
  se decidió.
- **Borrar el usuario del Auth no borra su solicitud** (`SET_NULL`, no cascade).
  Con cascade, el expediente desaparecía justo cuando más falta hace: cuando
  alguien se marcha o se le echa y hay que explicar qué pasó. El «quién» no
  depende de esa relación — vive en `main_character_id` y `main_character_name`,
  en texto plano, así que aguanta también que se borre el personaje.
- **La tabla `Main` de Baserow NO se recrea aquí.** AA ya es esa tabla. Lo que
  se hace es dejar de crear dependencias nuevas sobre ella.

### Arreglado en n8n (fuera del repo)

- `W4 → Escapar nombre main` ya no revienta con un error de JavaScript cuando el
  ticket no tiene Main: dice qué falta y en qué ticket.

## [0.30.0] — 2026-10-22

### Cambiado

- **Quién va a cada lado del chat, decidido con datos y no con suposiciones.**
  La regla anterior era «si el Auth lo conoce, es de los nuestros», y se cayó en
  cuanto apareció un solicitante que ya estaba registrado: sus dos
  interlocutores acababan del mismo lado. Lo que de verdad distingue a un
  reclutador es que **reclama tickets, decenas**; quien abre uno, ninguno. Esa
  lista ya estaba en el espejo, así que no hay nada que mantener aparte y se
  actualiza sola cuando alguien deja el puesto.
- **La conversación se busca por formato, no por campo.** En Soporte la charla
  acaba dentro de «Notas», no en «Transcripción texto», así que esos tickets se
  quedaban con el volcado crudo. Ahora, si las líneas empiezan por
  `[fecha, hora] alguien:`, es una conversación venga del campo que venga —con
  dos mensajes como mínimo, para no pintar una nota suelta como un chat.

### Corregido

- Las menciones salían como `<@Reclutador>`: se sustituía el id pero quedaban
  los símbolos de Discord. Ahora **@Reclutador**, y los emojis propios
  (`<:nombre:861047786…>`) se quedan en `:nombre:`.

## [0.29.2] — 2026-10-22

### Corregido

- **Los tickets antiguos perdían su transcripción.** Al separar la conversación
  de los adjuntos (0.28.1) solo se aceptaron `.html` y `.txt`, pero los tickets
  de antes no tienen texto: su conversación es un **PDF** que generaba MEE6 y se
  archivaba a mano. Esos caían a «Adjuntos» y dejaban de verse en el recuadro.

## [0.29.1] — 2026-10-22

### Corregido

- **Toda la conversación salía al mismo lado.** Se comparaba el autor con el
  main del ticket, y el solicitante de un reclutamiento todavía no está en el
  Auth: su nombre de Discord no se resuelve a ningún personaje, así que nunca
  casaba. Ahora al revés — a quien el Auth conoce se le ve el nombre de
  personaje y va al lado del staff; el que sigue con su alias de Discord es el
  que viene de fuera.

## [0.29.0] — 2026-10-22

### Añadido

- **La conversación se pinta en la ficha, como un chat.** El piloto a un lado y
  el staff al otro, con la hora de cada mensaje. Sale del texto que ya guardaba
  Baserow (`[20/10/2026, 19:31:28] usuario: mensaje`), que estaba ahí sin usar
  mientras la ficha enseñaba el fichero del bot en un iframe.
- **Los adjuntos de dentro de la charla enlazan nuestra copia.** Los enlaces de
  Discord caducan a las pocas horas —ese `?ex=…` es la fecha de expiración—, así
  que en una transcripción de hace meses están todos muertos. W5 guardó una
  copia de cada adjunto en el ticket: si el nombre casa, se enlaza esa, que ni
  caduca ni se sirve sin permiso. Cuando no casa, se avisa de que puede estar
  caducado en vez de dar un enlace roto sin más.
- Debajo queda un desplegable con el texto tal cual lo guardó el bot, por si
  hace falta leerlo en crudo.

### Seguridad

- Al pintar la conversación nosotros **desaparece el HTML ajeno de la ficha**.
  Donde había un iframe con un fichero generado por un bot a partir de lo que la
  gente pegó en un canal, ahora hay texto escapado por Django.

## [0.28.1] — 2026-10-22

### Corregido

- **El recuadro «Conversación» enseñaba una foto.** El campo «Transcripción» de
  Baserow guarda el HTML de la charla y los adjuntos en la misma lista —W5
  escribe las imágenes ahí mismo—, así que coger el primer fichero y meterlo en
  el iframe mostraba cualquier cosa. Ahora la conversación es el fichero HTML y
  el resto baja a Adjuntos. Venía de antes; salió al revisar los permisos.

## [0.28.0] — 2026-10-22

### Seguridad

- **Las transcripciones y los adjuntos ya no se sirven sin permiso.** Vivían en
  la media de Baserow, y esa URL la abre cualquiera que la tenga: una
  transcripción de Asuntos Internos reenviada por error se leía entera desde un
  navegador anónimo. La ficha comprobaba el permiso; el fichero que enlazaba,
  no. Ahora pasan por `ticket_fichero`, que exige **el mismo permiso que la
  ficha**, y la URL de Baserow ya no llega a la plantilla.
- La vista acepta **un índice dentro de los ficheros de ese ticket, nunca una
  URL**. Una vista que aceptara direcciones sería un proxy abierto: cualquiera
  le pediría que trajese lo que fuera, con la IP del servidor.
- Las transcripciones son HTML, así que servirlas desde nuestro dominio
  convertiría un problema de lectura en uno de ejecución. Van con
  `Content-Security-Policy: sandbox`, `X-Content-Type-Options: nosniff` y
  `Cache-Control: private, no-store`, y el iframe de la ficha lleva `sandbox`.

### Notas

- El almacén no cambia: los ficheros siguen en Baserow. Esto es el punto 1 de la
  migración —quién los SIRVE—, que se hace primero a propósito: el día que se
  mueva el almacén solo cambia de dónde lee esta vista.

## [0.27.1] — 2026-10-22

### Corregido

- Un tipo sin ninguna fecha de cierre sacaba las dos notas a la vez, y la del
  recorte con el mes en blanco («desde ,»). Ahora esa nota solo aparece cuando
  hay una fecha desde la que medir.

## [0.27.0] — 2026-10-22

### Cambiado

- **El «% cerrados» ya no castiga a una tabla por no haber tenido dónde apuntar
  el cierre.** Directores salía al 9,6% y no es que no cierre: antes de marzo de
  2026 no existía el campo —282 de sus 353 tickets no tienen ni estado—. El
  ticket se cerraba en Discord, se borraba el canal, y la fila se quedaba igual.
  Ahora el porcentaje se calcula sobre los tickets **abiertos desde que hay
  rastro de cierre**, y la pantalla dice desde cuándo y cuántos quedan fuera.
  Los anteriores siguen contando en el total, en el volumen y en los tiempos.
- Un tipo **sin ninguna fecha de cierre** deja de salir como «0%» y pasa a decir
  «sin rastro». Un cero ahí se lee como «no cierran nunca», que es justo lo
  contrario de lo que dice el dato: es Soporte, cuyo campo se creó hoy.

## [0.26.1] — 2026-10-22

### Corregido

- **Nueve fechas de nacimiento se colaban como fecha de apertura.** En la
  columna «Fecha» de la tabla de reclutamiento hay quien escribió su año de
  nacimiento: 1976, 1987, 1994… Son 9 filas de 573, pero cada una mete cuarenta
  años en la media, y entre todas inflaban la antigüedad media del embudo unos
  cinco meses. Ahora se descarta cualquier fecha anterior a 2022 —antes no
  había tickets en Baserow— y se cae a la última modificación. Un dato
  imposible es mejor nulo que falso.

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
