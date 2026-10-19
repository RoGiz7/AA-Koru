# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado semántico, con el `0.x` indicando que la API interna puede moverse.

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
