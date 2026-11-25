# Línea del tiempo
Estado: Verificada · Fecha: 2026-11-25

## Para qué
Ver de un vistazo todo lo que ha pasado año a año (eventos, viajes, certificados, premios, fotos), en dos formas a elegir: un río horizontal o salas por año.

## Alcance
- Entra: `web/linea.html` + `linea.js` + `linea.css` con dos vistas y un conmutador (`#rio` / `#salas`, recordado en localStorage); filtros por tipo (eventos, viajes, certificados, premios, fotos), salto a año y panel de detalle compartidos; el detalle enlaza a `evento.html?e=<slug>` (eventos), `mapa.html#viaje=<slug>` (viajes) y `certificados.html`.
- No entra (de momento): hitos de `cifras-e-hitos` (no existe `hitos` en `archivo.json`; cuando exista, se marcan en la línea); objetos sin fecha (pines y 21 sueltos: se avisa del número); enlace en el menú común (lo añade la integración).

## Datos
Solo lee `data/archivo.json`: `eventos` (con `objetos`, `fotos`, `charlas`), `viajes` y `objetos_sueltos`. Sin cambios de esquema.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Unir y ordenar eventos, viajes y sueltos con fecha; ignorar los que no la tienen | `tests/test_linea.js` (en `run_all.sh`) |
| 2 | Las dos vistas, el conmutador, `#salas` y localStorage funcionan | navegador, escritorio y 390 px |
| 3 | Filtros y salto a año valen para las dos vistas | navegador |
| 4 | Detalle: Enter lo abre, Esc lo cierra y devuelve el foco; enlaza a `evento.html?e=` | navegador (comprobado por script) |
| 5 | Sin scroll horizontal de la página a 390 px; objetivos ≥ 44 px; claro y oscuro; consola sin errores | navegador |

## Diseño
`docs/diseno/IDENTIDAD.md` (cristal, pegatinas Fluent). Maqueta A/B elegida por Carla: «Río horizontal» y «Salas por año». `prefers-reduced-motion` respetado.
