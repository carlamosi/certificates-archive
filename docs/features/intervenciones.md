# Intervenciones en público
Estado: Verificada (falta probar la reproducción con un vídeo real) · Fecha: 2026-11-23

## Para qué
Ver de un vistazo todo lo que Carla ha dicho en público (charlas como speaker, mesas redondas, entrevistas) y poder reproducir la grabación si la hay.

## Alcance
- Entra: `web/intervenciones.html` + `intervenciones.js` + `intervenciones.css` (los tokens salen de `style.css`, sin editarlo). Barra igual que la del mapa con «Intervenciones» activo.
- Resumen arriba, solo de intervenciones: total y cuántas son mesa redonda, charla como speaker o entrevista. Sin premios.
- Lista (la más reciente arriba) donde mandan **mes y año** («Octubre · 2026») y el día queda pequeño debajo; evento, lugar y tipo en una pastilla.
- Al elegir una: reproductor, fecha (mes y año), evento, lugar y tipo, y los botones «Abrir el vídeo» y «Ver el evento».
- Sin vídeo: el reproductor dice «Sin grabación todavía» (sin error) y «Abrir el vídeo» queda desactivado.
- No entra (de momento): página propia de evento (por eso «Ver el evento» está desactivado hasta que exista), transcripciones, subir vídeos a ningún sitio, ordenar o filtrar.

## Datos
Lee `web/data/archivo.json`; **sin cambios de esquema ni de exportación**.
- Una intervención por charla (`eventos[].charlas`). Además, cada evento **sin charlas** que tenga un objeto con `rol` o `premio` = Ponente o Speaker.
- Tipo (se deduce, no se pregunta): charla `keynote` → «Speaker»; `mesa_redonda` → «Mesa redonda»; `pitch` → «Pitch»; si el título o el evento dicen «entrevista» → «Entrevista»; si dicen «mesa redonda» o «taula rodona» → «Mesa redonda»; Speaker → «Speaker»; cualquier otro caso → «Intervención».
- Fecha: la de la charla; si falta, la del evento. Lugar: lugar y ciudad del evento.
- **Hoy salen 2** (HealthTech 2030, Mesa redonda TIC): «Taula rodona Escola Horitzó» y «Entrevista RN4» son eventos sin charla ni objeto. Aparecerán al importar `datos/entrada/charlas.txt` (formato en `datos/entrada/charlas_EJEMPLO.txt`).
- Vídeo: la base guarda la ruta local (`archivo_local`). El navegador no abre rutas de Windows, así que la web usa **`web/video/<nombre del fichero>`** (solo el nombre, sacado de `archivo_local`). Esa carpeta no va a git. Si hay `archivo_local` pero el fichero no está en `web/video/`, el reproductor lo dice. Si hay `url` de YouTube (también no listado) se incrusta; otro enlace solo se abre con «Abrir el vídeo».

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Resumen con total y recuento por tipo, sin premios | ✔ navegador con datos reales (2) y con 2 charlas de prueba (4) |
| 2 | Lista por mes y año, más reciente arriba; día pequeño; evento, lugar, tipo | ✔ navegador (1280 y 390 px) |
| 3 | Elegir una intervención cambia reproductor, fecha, evento, lugar y botones; funciona con teclado | ✔ navegador, clic y Tab + Enter |
| 4 | Sin `archivo_local` → «Sin grabación todavía» sin errores en consola; con vídeo en `web/video/` se reproduce | ✔ sin grabación y vídeo ausente (aviso con el nombre a copiar); ⏳ reproducción real sin probar (aún no hay vídeo) |
| 5 | Claro y oscuro, 390 px sin scroll horizontal | ✔ navegador (scrollWidth = 390) |
| 6 | `bash tests/run_all.sh` en OK | ✔ ejecución |

## Diseño
`docs/diseno/IDENTIDAD.md`; mesa «Intervenciones» del lienzo de Claude Design (aprobada por Carla). Pegatina `charla` (micrófono) junto al resumen.
