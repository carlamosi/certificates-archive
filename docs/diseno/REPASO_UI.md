# Repaso de coherencia UI/UX (25/11/2026)

Repaso de las 13 páginas de `web/` con `make-interfaces-feel-better` (modo completo), `frontend-design` y `emil-design-eng`.
Medido en el navegador con servidor local a 1280 px y 375 × 812, en claro y oscuro, con un script que revisa
tipografía, áreas táctiles, desbordes y contraste. Guía de referencia: `IDENTIDAD.md`.

**Prioridad:** alta = algo se rompe o no se lee; media = incoherencia visible entre páginas; baja = pulido.

## Incoherencias y arreglos

| Página | Problema | Arreglo | Prioridad | Estado |
|---|---|---|---|---|
| Fotos | La clase `.buscador` del campo de búsqueda pisaba el diálogo del buscador global (`dialog.buscador`): el diálogo cerrado quedaba con `display: flex` y su contenido aparecía en la página | Campo común `.campo` en `style.css`; `.buscador` queda solo para el diálogo | Alta | Hecho |
| Todas | El CSS del mapa vivía en `style.css` con clases genéricas (`.resumen`, `.leyenda`, `.panel`, `.zoom`…): en Premios el resumen heredaba padding y radio del mapa, y en Línea la leyenda salía con `position: absolute` | Movido a `web/mapa.css` (solo lo carga `mapa.html`) | Alta | Hecho |
| Fotos | `.matasellos` de las fotos redefinía el matasellos «AQUÍ» del índice (pasaporte) en esa página | Limitado a `.marco .matasellos` | Media | Hecho |
| Móvil (Pines, Línea, Pared, Certificados) | Fichas y diálogos quedaban debajo de la barra de pestañas (z-index 20 < 30) o la tapaban (`.detalle`, ficha de Pines) | Token `--sobre-pestanas` (alto de la barra + safe-area); hojas modales a z-index 40; fichas fijas se colocan encima de la barra | Alta | Hecho |
| Fotos, Intervenciones, Evento | A 375 px la barra escondía «Archivo / sección» (reglas del menú de chips antiguo) | Borradas; la barra es igual en todas | Media | Hecho |
| Todas | Cinco velos distintos detrás de fichas y diálogos (`.28`, `.32`, `.4`, `.45`, `.5`; desenfoque 4–8 px) | Token `--velo` (claro y oscuro) y desenfoque de 8 px en todos | Media | Hecho |
| Línea, Evento | Botón de cerrar con «✕» de texto y estilo propio (Línea) | Botón común `.btn.ghost.redondo.close` con el icono `cerrar` del sprite | Media | Hecho |
| Todas | Botón de cerrar en 4 posiciones (8, 12 y 16 px) y clases distintas (`.cfi-x`, `.cerrar`, `.ficha .redondo`, `.x`) | `.btn.close`: arriba a la derecha a 12 px en toda ficha | Media | Hecho |
| Fotos, Certificados | Dos campos de búsqueda con estilos distintos (`.buscador`, `.buscar`) y letra de 14 px: el iPhone amplía la página al escribir | `.campo` común con letra de 16 px | Media | Hecho |
| Fotos, Línea, Mapa | Tres controles segmentados duplicados (`.modo`, `.vista`, `.segmento`) | `.segmento` común (sirve con `aria-pressed` y `aria-checked`) | Media | Hecho |
| Certificados, Intervenciones, Pines | Contadores duplicados (`.contadores-c`, `.cifras`) con tamaños 44, 56 y 32 | `.contadores` común: 44/48 en escritorio y 32/36 en móvil (el mapa conserva su versión compacta) | Media | Hecho |
| Lanyards, Intervenciones | Título de página duplicado en cada CSS | `.titulo` común (32/38, 26/32 en móvil) | Media | Hecho |
| Inicio, Fotos, Certificados, Premios, Evento | Cinco estados vacíos distintos (alineación, tamaño, margen) | `.vacio` común; Premios (estante) y Evento (página) solo ajustan la posición | Media | Hecho |
| Inicio | Los años eran botones con estilo propio, no chips | Usan `.chip` (mismo tamaño, activo y área táctil que el resto) | Media | Hecho |
| Pared, Fotos, Certificados | El número pequeño de los chips (`small` con opacidad .7) no llegaba a AA (4,2:1) | Sin opacidad: tinta secundaria | Media | Hecho |
| Varias | Pesos 600 y 800 que la fuente no trae (solo 300/400/500/700): el navegador ya pintaba 700 | Escritos como 700 | Baja | Hecho |
| Lanyards, Pines, Intervenciones, Evento | Cada página repetía `text-decoration: none` y colores para los enlaces con forma de botón | `a.btn` sin subrayado en `style.css` | Baja | Hecho |
| Fichas (Fotos, Certificados, Premios, Pines, Lanyards) | Cristal de ficha con 84 %, 86 % y 88 % de superficie | Token `--glass-strong` (88 %) | Baja | Hecho |
| Premios, LEGO | Azules sueltos (`#4D7CFF`, `rgba(47,91,234,…)`) fuera de tokens | Derivados de `--accent` con `color-mix` | Baja | Hecho |
| Inicio | Hover de los accesos sin `@media (hover: hover)` (se quedaba pegado al tocar) | Envuelto en la media query | Baja | Hecho |
| Lanyards | Botón «Teclas» de 36 px de alto | 40 px (solo escritorio: en móvil no se muestra) | Baja | Hecho |
| Fotos | Matasellos de 7–8 px en las miniaturas | Se deja: es decorativo (`aria-hidden`) | Baja | Pendiente |
| Evento, Intervenciones, Pared | Colores fijos propios de la página (papel de polaroid, fondo de vídeo, portada del pasaporte) | Se dejan: son materiales, no interfaz | Baja | Aceptado |
| Pared 3D | Las piezas no se alcanzan con Tab | Fuera de este repaso (cambia la lógica); sigue en `PENDIENTES.md` | Media | Pendiente |

## Componentes comunes (en `web/style.css`)
`.bar` (barra de cristal + sello del índice), `.chip`, `.btn` (`.ghost`, `.redondo`, `.close`), `.campo`, `.segmento`,
`.contadores`, `.titulo`, `.vacio`, `.notice` (carga y avisos), `.sheet` (ficha modal), `.pegatina`, `.sello`, `.kicker`,
y los tokens `--glass-strong`, `--velo` y `--sobre-pestanas`. Una página nueva debe usar estos antes de crear los suyos.

## Comprobado
Ver el final de `docs/ESTADO.md` (sección del repaso).
