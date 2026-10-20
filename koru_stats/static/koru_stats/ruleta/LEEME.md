# Fondo de la ruleta

Si existe un fichero **`fondo.jpg`** en esta ruta, la pantalla de proyección de
la ruleta lo usa como fondo y las auroras y las estrellas se quedan por debajo.
Si no existe, no pasa nada: el `onerror` lo quita y se ve el ambiente pintado.

## Dónde ponerlo

En el servidor, **directamente en la carpeta de estáticos ya recogidos**:

```
/var/www/myauth/static/koru_stats/ruleta/fondo.jpg
```

⚠ Ese es el sitio bueno, y no la carpeta del paquete dentro del `venv`. Un
fichero metido ahí lo borra el siguiente `pip install --upgrade`, y nadie se
acuerda de por qué un día dejó de verse el fondo. En cambio un `collectstatic`
normal respeta lo que no conoce (sin `--clear`), así que ahí aguanta.

## Por qué no viene ninguna imagen de serie

El arte del Festival de Yoiul es de CCP y no se distribuye con el plugin. Lo que
sí viene de serie es el ambiente generado por código —nieve, auroras, estrellas—
más los retratos y los renders que sirve el propio CDN de EVE.

## Una trampa, por si alguien toca la plantilla

`gift_ruleta.html` pega la ruta a mano (`{{ STATIC_URL }}…`) en vez de usar el
tag `static`. Es a propósito: con el almacenamiento por manifiesto del Auth,
pedirle por ese tag un fichero que no está **no devuelve un 404, revienta la
plantilla entera con `ValueError`** — y lo normal es que no esté.
