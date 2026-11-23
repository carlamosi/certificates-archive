# Pines por ciudad
Estado: Verificada · Fecha: 2026-11-23

## Para qué
Ver todos los pines de Carla de un vistazo, agrupados por país, y saltar de un pin a su viaje en el mapa.

## Alcance
- Entra: contadores (pines, ciudades, países); grupos por país con más de un pin; «Otros países» con el país bajo la ciudad; chapa redonda por pin (foto si hay, si no el código); panel con foto grande en marco de sello, fecha, ciudad, país y viaje; botones «Ver en el mapa» y «Su viaje».
- No entra: medidas y lugar físico (se guardan, no se muestran); edición; buscador.

## Datos
`web/data/archivo.json`: objetos `tipo = pin` de `viajes[].objetos` (`pin_id`, `place_id` → `totales.ciudades`, `front_web`). Fecha: la visita de esa ciudad en el viaje; si no hay, el inicio del viaje. Sin cambios de esquema.
Código de la chapa: `pin_id` antes del primer guion si es corto; si no, las 3 primeras letras de la ciudad.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Contadores y grupos salen de `archivo.json` | navegador |
| 2 | Pin sin foto muestra su código; con foto, la foto | navegador |
| 3 | Pin elegido: panel con fecha, ciudad, país y viaje, sin medidas ni caja | navegador |
| 4 | «Ver en el mapa» abre `mapa.html?viaje=<id>` con ese viaje abierto | navegador |
| 5 | «Su viaje» resalta los pines del mismo viaje | navegador |
| 6 | Escritorio y 390 px, claro y oscuro, todo con teclado | navegador |

## Diseño
Mesa «Pines» del lienzo de Claude Design; identidad en `docs/diseno/IDENTIDAD.md`. Barra de cristal como `mapa.html`.
