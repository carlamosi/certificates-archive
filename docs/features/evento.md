# Página de evento
Estado: Verificada · Fecha: 2026-11-25

## Para qué
Ver todo lo de un evento en una sola hoja: sus objetos, fotos, charlas (con vídeo) y el viaje, con km y ciudades.

## Alcance
- Entra: `web/evento.html?e=<slug>` + `evento.js` + `evento.css`. Versión B «Página de cuaderno» del lienzo: hoja rayada con el sello del objeto principal, collage de polaroids inclinadas con cinta, notas para las charlas y tira lateral de cristal con el viaje.
- **Variante compacta** (menos de 3 piezas entre objetos, fotos y charlas): hoja estrecha de una columna, la pieza única se ve grande y centrada. Sin viaje no hay tira. Sin imagen de objeto, una tarjeta con su pegatina («Certificado por escanear»). Sin nada, una nota «Aún no hay fotos, objetos ni charlas».
- Foto o objeto con imagen: clic o Enter abre el visor (flechas ← → pasan de una a otra, Esc cierra y devuelve el foco).
- Charla: «Ver la grabación» abre el reproductor debajo (vídeo local `video/<nombre>.mp4` o YouTube, como en intervenciones).
- Sin `?e` o con un slug que no existe: estado vacío con «Ir al inicio».
- Enlaces «Ver el evento» activados en `intervenciones.js` y `lanyards.js` (`DESTINO.evento`).
- No entra (de momento): enlace en el menú común (lo añade quien integra), buscador de eventos, edición.

## Datos
Lee `web/data/archivo.json` (eventos con `objetos`, `fotos`, `charlas`, y `viajes` por `trip_id`). **Sin cambios de esquema.**
- Imágenes: foto `web` en grande y `mini` en el collage; objeto `front_web`; si una imagen falla, se cambia por la pegatina de su tipo.
- Personas: las de las fotos del evento.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Slug válido muestra el evento; sin slug o inexistente, estado vacío con enlace | ✔ navegador |
| 2 | Evento rico (EuChemS, Women in Tech Awards, STEM Women Congress) y 3 pobres (Calçotada IP, FIRST LEGO League Junior, 1 solo certificado) se ven completos, sin huecos | ✔ navegador |
| 3 | Vídeo de una charla se reproduce; visor de fotos con flechas, Esc y foco de vuelta | ✔ navegador (script + clic) |
| 4 | 1280 y 390 px, claro y oscuro, sin scroll horizontal ni errores en consola | ✔ navegador (`scrollWidth` = 375 en el emulador móvil) |
| 5 | «Ver el evento» de intervenciones lleva a `evento.html?e=<slug>` | ✔ navegador |
| 6 | `bash tests/run_all.sh` en OK | ✔ ejecución |

## Diseño
`docs/diseno/IDENTIDAD.md`; mesa «Página de evento» del lienzo (versión B, elegida por Carla). Tokens de `style.css`; pegatinas con `IDENTIDAD.pegatina`.
