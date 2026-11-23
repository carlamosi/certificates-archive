# Certificados
Estado: En construcción · Fecha: 2026-11-23

## Para qué
Ver de un vistazo los 56 certificados de Carla, encontrar uno por evento, organizador o nº de archivo, y saber cuáles tienen premio y cuáles faltan por escanear.

## Alcance
- Entra: contadores (certificados, con premio, por escanear); buscador sin mayúsculas ni acentos; vistas Todos / Con premio / Por escanear; rejilla de hojas giradas con miniatura, agrupada por año (reciente primero); ficha con imagen grande, fecha, título, organizador, premio (nivel + texto original), nº de archivo; Anterior / Siguiente y Esc.
- No entra (de momento): «Ver el evento» (no hay página de eventos a la que enlazar); `caja_fisica`; edición de datos.

## Datos
`web/data/archivo.json`: objetos con `tipo = certificado` en `eventos[].objetos` y `objetos_sueltos`. Campos: `titulo`, `organizador`, `fecha` (AAAA, AAAA-MM o AAAA-MM-DD), `premio`, `nivel`, `num_archivo`, `front_web` (imagen; vacío = por escanear). Sin cambios de esquema. Las imágenes (`img/certificados/`) no van a git.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Los contadores salen de los datos (56 · 24 · 18) | navegador |
| 2 | Búsqueda sin mayúsculas ni acentos por título, organizador, nº y evento | navegador |
| 3 | Las tres vistas filtran; premio = `nivel` no vacío; por escanear = sin `front_web` | navegador |
| 4 | Hojas con miniatura; medalla si hay premio; borde discontinuo y «Por escanear» si falta | navegador |
| 5 | Ficha con todos los campos; Anterior/Siguiente recorren lo visible; Esc cierra y devuelve el foco | navegador con teclado |
| 6 | Escritorio y 390 px, claro y oscuro, sin desbordes | navegador |
| 7 | Sin `archivo.json` muestra un aviso claro | navegador |

## Diseño
`docs/diseno/IDENTIDAD.md`. Lienzo aprobado: mesa «Certificados» (claude.ai/artifact/GyQxMnXwC7BuNvu7Fgci7x). Pegatina de premio: `IDENTIDAD.pegatina('premio')`.
