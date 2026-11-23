# Mapa de viajes
Estado: Verificada · Fecha: 2026-11-23

## Para qué
Ver de un vistazo, estilo Been, todo lo que Carla ha viajado: cuánto (contadores grandes) y dónde (países en tres estados, ciudades y aeropuertos con su pegatina y arcos de vuelo).

## Alcance
- Entra: página `web/mapa.html` (+ `web/mapa.js`, estilos añadidos al final de `web/style.css`). Contadores héroe: ciudades, países, continentes, aeropuertos y km (si `totales.km` existe; si no, el contador no aparece). Países en 3 estados: visitado, tránsito (solo aeropuerto) y futuro. Chinchetas-pegatina por ciudad (y por evento, cuando los eventos tengan `lat`/`lng`). Tarjeta de cristal (la cartela) al pasar o enfocar. Zoom con rueda, pellizco y botones + / −.
- Capas: fondo **Papel** (mapa propio), **Satélite** (Esri World Imagery) o **Noche** (luces de NASA Black Marble); capas que se pueden ocultar: países, vuelos, rutas por tierra, ciudades, aeropuertos y eventos (los que tienen coordenadas: 8 hoy).
- Panel lateral (abajo en móvil): botón «Viajes» con la lista por año; al tocar una chincheta, un arco o una fila, la ficha del viaje (fechas, días, km, ciudades, vuelos como billetes, recorrido en orden, eventos y objetos del archivo) y el mapa se encuadra en ese viaje. Anterior / siguiente y Esc.
- Barra superior de cristal brillante (también en la pared).
- No entra (de momento): capa de eventos con ficha completa, fotos en el mapa, % del mundo, filtro por año, recordar las capas elegidas. Ideas de capas para más adelante: pines por ciudad, fotos, calor por número de visitas.

## Datos
Lee `web/data/archivo.json` (lo deja en `window.ARCHIVO`); sin cambios de esquema.
- Ciudades: `viajes[].visitas` (`lat`, `lng`, fechas) y `viajes[].estado` (`futuro` = ciudad futura).
- Estados de país: visitado = `totales.paises` con `ciudades > 0`; tránsito = con `ciudades = 0` y aeropuertos; futuro = país de una visita de un viaje `futuro` que no está visitado.
- Contadores: ciudades = `totales.ciudades`; países y continentes = solo los **visitados** (el tránsito sale en la leyenda, como en Been); aeropuertos = `totales.aeropuertos`; km = `totales.km`.
- Arcos: si existe `viajes[].vuelos` (`origen`/`destino` con `iata`, `lat`, `lng`), se dibuja cada vuelo y sus aeropuertos llevan pegatina. Si no, **un arco de Barcelona (casa) a la ciudad más lejana de cada viaje**; dentro del viaje, las ciudades se unen con una ruta discontinua (por tierra).
- Formas de los países: `world-atlas@2.0.2` (Natural Earth 1:50m, incluye Andorra) con `topojson-client@3.1.0`, `d3@7.9.0` y `d3-tile@1.0.0`, desde CDN con versión fija y sin clave. Proyección Mercator para que encajen las teselas; sin la Antártida. Los nombres de país de la base se traducen a su código ISO numérico en `mapa.js`.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Contadores correctos (40 ciudades, 10 países, 2 continentes, 10 aeropuertos con los datos de hoy); km oculto si falta y visible si existe | ✔ navegador (52.731 km ya exportados) + `estados()` con node |
| 2 | Catar en tránsito, Chequia en futuro, los otros 10 visitados | ✔ navegador (clase de cada país) |
| 3 | Cada ciudad tiene su pegatina; al pasar, tocar o enfocar con Tab sale la tarjeta de cristal; Esc la cierra | ✔ navegador, ratón, toque y teclado |
| 4 | Arcos en `--accent` (1,5 px), rutas en tierra discontinuas; al señalar una ciudad se resaltan sus viajes | ✔ navegador (10 vuelos reales de `viajes[].vuelos`) |
| 5 | Escritorio y 390 px, claro y oscuro, `prefers-reduced-motion` (zoom sin animación) | ✔ navegador; «reducir movimiento» revisado en código (el navegador integrado no lo emula) |
| 6 | Capas: los tres fondos cargan y cada capa se oculta; créditos visibles con teselas | ✔ navegador (35 teselas Esri y NASA) |
| 7 | Panel: lista, ficha, encuadre del viaje sin quedar bajo el resumen ni el panel; Esc cierra y devuelve el foco | ✔ navegador, escritorio y 390 px |
| 8 | `bash tests/run_all.sh` en OK | ✔ ejecución |

## Diseño
`docs/diseno/IDENTIDAD.md` §9. Mapa propio en SVG fundido con el papel (el mar es el fondo): se tiñe con los tokens y el modo oscuro sale solo; satélite y noche son teselas debajo. Visitado = azul matasellos eléctrico con degradado vertical (luz arriba) y halo azul; la tierra lleva una sombra suave, los arcos van en marino (blanco en oscuro) con brillo y los bordes del mapa se funden con el papel. Pegatinas de 20 px (área táctil de 44 px); tránsito = rayado en acento; futuro = contorno discontinuo. Barra de cristal con enlaces Pared / Mapa. La tarjeta reutiliza la `.cartela` de la pared.

Por qué no Leaflet: el fondo principal es el papel propio (sin teselas) y los tres estados de país necesitan las formas igualmente; d3-tile basta para los fondos de satélite y noche sin añadir otra librería de mapas.
