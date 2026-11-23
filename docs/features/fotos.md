# Fotos con personas
Estado: Verificada · Fecha: 2026-11-23

## Para qué
Ver las fotos con personas como un álbum de sellos, encontrar a alguien por su nombre y abrir cada foto en grande con quién sale.

## Alcance
- Entra: `web/fotos.html` (+ `fotos.js`, `fotos.css`). Fotos en marcos de sello, algo giradas, agrupadas por mes (las más recientes primero); filtro por año a la izquierda (con «Todas»); buscador con lupa por nombre de persona (sin distinguir mayúsculas ni acentos, por principio de palabra, con sugerencias de nombres mientras escribes); al tocar un sello, la foto se abre en grande con las personas, evento, fecha, anterior/siguiente; Esc cierra. Tocar un nombre en la foto busca a esa persona; si tiene Instagram guardado, el nombre abre su perfil en otra pestaña. La foto grande conserva su proporción (vertical u horizontal).
- Entra (datos): `archivo.py fotos-web` crea las versiones web; `archivo.py exportar` añade `web` y `mini` a cada foto.
- Entra (visor): «Ver las N fotos del evento» (filtra la página al evento; «Ver todas» lo quita), «En el mapa» (abre `mapa.html`; el mapa aún no sabe enfocar un evento), «Descargar» (el WebP de 1600 px con nombre `fecha_evento.webp`, sin nombres de personas), zoom (doble toque/clic, pellizco, rueda, teclas + − 0; arrastrar al acercar) y deslizar para cambiar de foto.
- Entra (pies de foto): `archivo.py foto --archivo F --nota T` guarda un pie (columna `photos.notas`, sin cambio de esquema); `exportar` lo lleva como `nota` y el visor lo muestra en cursiva si existe.
- Entra (vista): conmutador Álbum / Mesa (fotos más giradas y solapadas; la que tocas o enfocas sube al frente). Se recuerda en el navegador.
- No entra (de momento): descargar el original HEIF (no está en la web); panel lateral con vista previa fija del diseño (la ampliación ya cubre ese uso); edición de nombres desde la web (se corrige en la base).

## Datos
Esquema v4: `people.instagram` (solo el usuario; `archivo.py persona --nombre N --instagram U`, acepta URL). `exportar` lo lleva a `personas[]`; la web solo lo usa si cumple `[A-Za-z0-9._]{1,30}`.
- `archivo.py fotos-web`: lee los originales (`datos/fotos_originales`, JPG y HEIF/HEIC con `pillow-heif`, ya en `requirements.txt`) y deja en `web/img/fotos/` un WebP de lado largo 1600 px y una miniatura de 480 px. Respeta la orientación del móvil. Nombre = hash del original (la ruta no lleva nombres de personas). Repetible: salta lo ya hecho y avisa de los originales que faltan.
- `archivo.json`: cada foto lleva `{archivo, fecha, personas, web, mini}`; `web` y `mini` son `null` si no hay WebP. La web solo muestra las que tienen `web`.
- La página junta `eventos[].fotos`, `viajes[].fotos` y `fotos_sueltas`.
- **Privacidad:** `web/img/fotos/` y `web/data/archivo.json` están en `.gitignore`; ninguna foto ni nombre va a git. Página con `noindex`.

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | `fotos-web` crea WebP 1600 px y miniatura 480 px, es repetible y avisa de los originales que faltan | `tests/test_archivo_db.py::test_fotos_web` |
| 2 | `exportar` enlaza `web`/`mini` solo si el WebP existe y la ruta no lleva el nombre del original | mismo test |
| 3 | `web/img/fotos/` y `web/data/archivo.json` no van a git | `git check-ignore` |
| 4 | Fotos en sellos, agrupadas por mes, más recientes primero; chips de año con su contador | navegador, escritorio y 390 px, claro y oscuro |
| 5 | La búsqueda ignora mayúsculas y acentos («nuria» encuentra «Núria») y dice cuántas fotos hay | navegador |
| 6 | Tocar un sello abre la foto grande con sus personas; ← → navegan; Esc cierra y devuelve el foco al sello | navegador con teclado |
| 7 | Sin `archivo.json` o sin fotos web, la página lo dice en vez de quedar en blanco | navegador |
| 8 | Foto vertical en grande sin recortar; nombre con Instagram abre su perfil | navegador (ratio 0,75 = el de la foto; enlace `https://www.instagram.com/personaf/`) · `test_instagram_de_persona` |
| 9 | Ver las fotos del evento y quitar el filtro; Descargar; zoom y reinicio al cambiar de foto; deslizar cambia de foto; Mesa se recuerda | navegador a 1280 px (JS: filtro 4 fotos, zoom 2,5, teclas) y 390 px (deslizar 2→3, mesa) |
| 10 | «Todas» muestra todo; las sugerencias salen al escribir (flechas, Enter, Esc, toque) y no repiten el nombre ya escrito; el pie de foto aparece solo si existe; en el matasellos las ciudades largas se abrevian | `test_nota_de_foto`; navegador a 1280 y 390 px |
| 11 | `bash tests/run_all.sh` termina en OK | ejecución |

## Diseño
`docs/diseno/IDENTIDAD.md`; mesa «Fotos» del lienzo de Claude Design (aprobada). Marcos con `.sello`, pegatinas de `iconos.js` (foto, persona, evento), chips de `style.css`. Movimiento: giro que se endereza al pasar (solo con puntero fino), press `scale(.96)`, foco visible, `prefers-reduced-motion` respetado.
