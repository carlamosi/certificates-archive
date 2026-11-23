# Lanyards en línea de tiempo
Estado: Verificada · Fecha: 2026-11-23

## Para qué
Ver todos sus lanyards colgados en orden de fecha, girarlos para ver las dos caras y abrir su ficha, sin 3D y con las medidas fuera de la vista.

## Alcance
- Entra: `web/lanyards.html` (+ `lanyards.js`, `lanyards.css`; `style.css` solo para los tokens). Carril recto y horizontal con los años marcados y las tarjetas colgadas por fecha; se desplaza con rueda, arrastre y teclado.
- **Ratón:** un clic gira (anverso/reverso, 480 ms); doble clic abre la ficha.
- **Teclado:** Tab recorre las tarjetas (también las desplaza a la vista); **Enter o Espacio gira**; **F abre la ficha**; ← → mueven el foco; Inicio/Fin van a la primera/última; Esc cierra la ficha; tras abrirla, Tab entra en ella (está antes que el carril en el DOM). Está escrito en la página («Teclas»).
- **Móvil:** un toque gira; mantener pulsado (0,5 s) abre la ficha; cada tarjeta lleva además un botón visible «Ficha».
- **Pegatina de premio** (medalla pequeña junto a la fecha) en los lanyards con premio o con rol de premio/ganadora/finalista; nunca sobre la tarjeta.
- **Ficha** (panel de cristal): las dos caras, fecha, evento, lugar y premio o rol, y los botones «Ver el evento» y «En el mapa».
- No se muestran: medidas, forma, dónde se guarda, calibración ni avisos de calidad (siguen en los datos).
- No entra (de momento): filtro por año, escala de tiempo proporcional (las tarjetas van a la misma distancia), editar nada.

## Datos
- Lee `data/archive.json` (mismo formato que `app.js`: `fecha`, `evento`, `ciudad`, `lugar`, `rol`, `front_web`, `back_web`…). Sin él, aviso en pantalla.
- Si existe `data/archivo.json`, enlaza cada lanyard con su evento: primero por `objetos[].uid` = `id` del lanyard; si no, por mismo mes y nombre del evento contenido en el del lanyard. El evento aporta ciudad, país, premio (`objetos[].premio`) y `slug`. Sin coincidencia, se usa lo del propio lanyard.
- Sin reverso: la cara de atrás se muestra en blanco con «Sin reverso». Sin anverso: tarjeta de papel con el nombre del evento.
- «En el mapa» → `mapa.html#evento=<slug>` (el mapa aún no lee el parámetro: abre el mapa). **«Ver el evento» se oculta hasta que exista una página de eventos**; el destino está en una constante (`DESTINO`) de `lanyards.js`.
- Sin cambios de esquema.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Tarjetas en orden de fecha, años marcados, desplazamiento horizontal con rueda, arrastre y teclado | ✔ navegador (carril, años, `scrollWidth`); rueda y arrastre con ratón **no probados a mano** (solo revisados en código) |
| 2 | Clic gira (480 ms; sin giro con «reducir movimiento»); doble clic abre la ficha | ✔ navegador (eventos de clic y doble clic); «reducir movimiento» **no emulado** (solo código y CSS) |
| 3 | Teclado completo y documentado en la página; Esc cierra y devuelve el foco | ✔ navegador (F, ←, Esc, foco) |
| 4 | Móvil (390 px): toque gira, pulsación larga y botón «Ficha» abren la ficha | ✔ 390 px: botón «Ficha»; la pulsación larga **no probada con un dedo real** |
| 5 | La ficha no muestra medidas, forma, ubicación ni calibración | ✔ lectura del DOM de la ficha |
| 6 | Sin reverso, sin evento coincidente o sin `archivo.json`: no se rompe | ✔ sin `archivo.json` y con un lanyard sin reverso |
| 7 | Claro y oscuro, escritorio y 390 px | ✔ navegador |
| 8 | `bash tests/run_all.sh` en OK | ✔ ejecución |

## Diseño
`docs/diseno/IDENTIDAD.md`; diseño aprobado en Claude Design (mesa «Lanyards»). Carril de acero satinado con cuerdas finas en tinta, tarjeta con sombra suave y una ligera inclinación alterna, fecha en etiqueta azul y evento debajo. Ficha en cristal a la derecha (hoja inferior en móvil). Barra copiada de `mapa.html` con «Lanyards» activo; la navegación común se cambiará después.
