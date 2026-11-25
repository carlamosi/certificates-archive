# Estado del proyecto

Fecha de corte: 23/11/2026. Esto es lo que hay, lo que está comprobado y lo que no.

## 1. Herramienta de lanyards (`herramientas/lanyard_archive`)
**Versión:** v3 (simplificada). Fuente de verdad: `lanyard_archive.py` + `lanyard_core.py`.

| Parte | Estado | Cómo se comprobó |
|---|---|---|
| Calibración ArUco (plantillas v2 y A4) | Hecho | Detección de los 4 marcadores en la plantilla renderizada: error < 0,02 mm |
| Plano rectificado y medidas en mm | Hecho | 40 fotos sintéticas de medida conocida: error medio ~0,03 mm, máx. 0,12 mm |
| Segmentación con luz lateral y etiqueta blanca | Hecho | Pruebas sintéticas + una foto real (iFest) con esquinas manuales |
| Orificios: arriba, redondos, máx. 2 | Hecho | Pruebas con letras, bultos y el caso del "0" marcado como agujero |
| Formas libres (medalla) | Hecho | Prueba sintética: silueta 1868 mm² frente a 1884 reales |
| Anverso y reverso con la misma medida | Hecho | Regla en el código; la diferencia se avisa si supera 1,5 mm |
| Anclaje para cordón 3D | Hecho | Campo `anclaje_x/y` en el JSON |
| Ventanas de revisión (cv2) | **No probado** | El entorno no tiene pantalla. El modo `--sin-gui` sí está probado |
| Lote real de la persona (HEIC del iPhone) | **Pendiente** | Solo se ha probado con HEIC sintéticos y una foto real |
| Calibración de su impresora | **Pendiente** | Se usa 100 % hasta que ejecute `--medir-regla` |

**Límites conocidos**
- Objetos blancos sobre papel blanco no se detectan solos: pedir cartulina negra debajo.
- La precisión depende de que la hoja esté plana y de la escala de la impresora.
- Si una pareja falla, se repite completa en una carpeta nueva (no se empareja por nombre).

## 2. Web (`web/`)
**Versión:** prototipo 2 (pared de lanyards con la identidad «cuaderno de viaje de cristal», ver `docs/diseno/IDENTIDAD.md`).

| Parte | Estado | Cómo se comprobó |
|---|---|---|
| Carga de `archivo.json` (base real) en `window.ARCHIVO` | Hecho | Navegador a 1280 px y 375 px: 27 eventos, 18 viajes, 11 países; pared intacta (aún no se pinta) |
| Carga de datos y pared 3D | Hecho | Chromium headless con Three r128 local |
| Balanceo, cartela y clic para girar | Hecho | Pruebas de cursor y clic (tras corregir un `[hidden]` que lo bloqueaba) |
| Ficha: anverso, reverso, medidas, navegación | Hecho | Pruebas de teclado (Enter, flechas, Esc) y botón |
| Filtro por año | Hecho | Prueba: "3 de 7 objetos · 2025" |
| Identidad visual: tokens claro/oscuro, Open Sauce One, logo sello, iconos SVG, pegatinas Fluent Emoji 3D | Hecho (23/11/2026) | Navegador a escritorio y 390 px, claro y oscuro; contraste AA calculado |
| Guía visual viva `web/identidad.html` | Hecho | Navegador: colores, pegatinas, iconos, botones, sello, cartela |
| Publicar en Vercel (`herramientas/preparar_vercel.py` → repo privado `carlamosi/certificates-archive-web`) | Hecho (24/11/2026) | Publicada en https://certificates-archive-web.vercel.app (cada subida se despliega sola); fotos, mapa y las 127 imágenes comprobadas en la web publicada; `noindex` activo |
| Cartela: margen para llegar a los botones, botón «Girar», se abre al tocar en móvil | Hecho | Hover y clic en escritorio; toque a 390 px |
| Pared 3D: colores desde tokens, sombra de contacto, 3 por fila en móvil, péndulo quieto con «reducir movimiento» | Hecho | Navegador; «reducir movimiento» **no probado** en el navegador |
| Móvil | Hecho a 390 px | Emulación en el navegador; **pendiente en un móvil real** |
| Datos reales | **Pendiente** | Hay 6 objetos de demostración inventados |
| Mapa de viajes `web/mapa.html` (ficha `docs/features/mapa.md`): contadores con km, países visitado/tránsito/futuro, pegatinas por ciudad y aeropuerto, vuelos reales, capas (fondo papel/satélite/noche y capas que se ocultan), panel lateral con la lista de viajes y la ficha de cada uno, barra de cristal brillante | Hecho (23/11/2026) | Navegador a 1280 px y 390 px, claro y oscuro; ratón, toque, Tab y Esc (devuelve el foco); zoom y encuadre por viaje; teselas de Esri y NASA cargadas; `estados()` comprobado con node (40 · 10 · 2 · 10 · 52.731). «Reducir movimiento» **no emulado** (solo revisado en código) |
| Página de evento `web/evento.html?e=<slug>` (ficha `docs/features/evento.md`): hoja de cuaderno con sello, polaroids, notas con vídeo y tira de viaje; variante compacta para eventos pobres; «Ver el evento» activado en intervenciones y lanyards | Hecho (25/11/2026) | Navegador a 1280 y 390 px, claro y oscuro; 3 eventos ricos y 3 pobres; visor con teclado; enlace del menú común pendiente de integrar |
| Enlaces a `evento.html?e=<slug>` desde fotos, certificados, premios, mapa (ficha de viaje) y pared 3D (ficha); lanyards ya lo tenía y pines solo si el pin tiene evento (hoy ninguno: enlazan al viaje) | Hecho (25/11/2026) | `tests/run_all.sh` OK; navegador a escritorio y 375 px: el enlace sale solo con evento, href correcto, Tab/Enter, consola sin errores. Sin probar con lanyards reales (la pared usa `archive.json` de demostración; cruza por uid o mes+nombre como `lanyards.js`). En móvil, las pestañas fijas tapan el pie de las fichas de certificados y pared (ya ocurría); premios sube su ficha 76 px |
| Intervenciones en público `web/intervenciones.html` (ficha `docs/features/intervenciones.md`): resumen por tipo, lista por mes y año, reproductor con «Sin grabación todavía»; vídeos MP4 H.264 en `web/video/` (fuera de git, los crea `preparar_vercel.py`) | Hecho (23/11/2026; vídeos 24/11) | Navegador a 1280 y 390 px, claro y oscuro, Tab + Enter; salen 4, las 2 de París con vídeo; reproducción comprobada (vertical sin recorte) |
| Lanyards en línea de tiempo `web/lanyards.html` (ficha `docs/features/lanyards.md`): carril con años, clic gira, doble clic / F / pulsación larga abren la ficha, evento enlazado con `archivo.json` | Hecho (23/11/2026) | Navegador a 1280 px y 390 px, claro y oscuro; clic, doble clic, F, flechas y Esc; sin `archivo.json` y sin reverso. **No probados:** rueda y arrastre a mano, pulsación larga con dedo real, «reducir movimiento». «Ver el evento» oculto hasta que haya página de eventos |
| Pines por ciudad `web/pines.html` (ficha `docs/features/pines.md`): contadores, grupos por país con «Otros países», chapa por pin (código si no hay foto), ficha con sello, «Ver en el mapa» (`mapa.html?viaje=`) y «Su viaje» (resalta los del viaje); sin medidas ni caja | Hecho (23/11/2026) | Navegador a 1280 px y 390 px (hoja inferior), oscuro y claro (claro solo a 390 px); ratón, Tab, Enter y Esc; `?viaje=` abre el viaje en el mapa. Datos hoy: 17 pines, 16 ciudades, 8 países, sin fotos (**ruta de `front_web` y el camino con foto, no probados**) |
| Certificados `web/certificados.html` (ficha `docs/features/certificados.md`): contadores, buscador sin acentos, vistas Todos/Con premio/Por escanear, hojas por año con miniatura y ficha con teclado | **En construcción** | Escrita; `node --check` y `tests/run_all.sh` OK. **Sin probar aún en navegador** (escritorio, 390 px, claro/oscuro, teclado) |
| Premios `web/premios.html` (ficha `docs/features/premios.md`): vitrina de cristal con 23 medallas en 4 estantes, resumen por nivel y año, ficha con «Ver el certificado» / «Por escanear» | Hecho (23/11/2026) | Navegador a escritorio y 390 px, claro y oscuro, teclado (Tab, flechas, Esc); `contar()` con node = 23 (7/2/8/6). «Reducir movimiento» revisado en CSS, no emulado |
| Buscador global `web/buscador.js` (ficha `docs/features/buscador.md`): Ctrl/⌘+K, `/` o lupa de la barra, en todas las páginas vía `pasaporte.js`; eventos, viajes, lugares, personas, certificados, premios, pines, sellos y charlas | Hecho (25/11/2026) | `tests/test_buscador.js`; navegador a escritorio y 375 px, claro y oscuro, teclado, foco y consola sin errores propios |
| Línea del tiempo `web/linea.html` (ficha `docs/features/linea-del-tiempo.md`): vistas «Río» y «Salas» con conmutador (`#rio`/`#salas`), filtros por tipo, salto a año y detalle que enlaza a `evento.html?e=` | Hecho (25/11/2026) | `tests/test_linea.js`; navegador a escritorio y 375 px, claro y oscuro, Esc y foco, consola limpia. Sin `hitos` en los datos todavía; `evento.html` y el menú los pone la integración |
| Inicio «Tu año en cifras» `web/inicio.html` (+ `inicio.js`, `inicio.css`; ficha `docs/features/cifras-e-hitos.md`, parte web): selector 2018…año actual y «Todo», frase de apertura con las cifras, recorrido mes a mes (viajes con sus eventos, premios, primeras veces, km acumulados, foto en marco de sello) y accesos a los módulos; cada evento enlaza a `evento.html?e=<slug>`. Lee `anual`, `hitos` y `totales.km_perspectiva`, que genera `archivo.py exportar` (`bloques_cifras`; viajes sin fecha en el bloque `sin_fecha`); el JS solo los agrupa por mes. Los viajes enlazan a `mapa.html?viaje=<id>` y los km del arranque se cuentan animados (sin animación con reduced-motion). «País nuevo» no cuenta España. Es la portada (`index.html`); la pared pasó a `pared.html` (25/11) | Hecho (25/11/2026) | `tests/test_archivo_db.py::test_anual/test_hitos` (km por año = `totales.km`, hitos ordenados, únicos y sin futuros) y `tests/test_inicio.js` (agrupación; km por año = `totales.km` = 56.110; pines solo en «Todo»; sin futuros). Navegador a escritorio y 390 px, claro y oscuro, teclado, consola sin errores. «Reducir movimiento» revisado en CSS, no emulado. Falta: `evento.html` (otra sesión) |
| Personas, buscador físico | **Pendiente** | No empezado |

### Repaso de coherencia UI/UX (2026-11-25)
Tabla completa en `docs/diseno/REPASO_UI.md`. Componentes comunes en `web/style.css` (`.campo`, `.segmento`, `.contadores`, `.titulo`, `.vacio`, `.btn.close`, tokens `--velo`, `--glass-strong`, `--sobre-pestanas`); el CSS del mapa pasó a `web/mapa.css`; `sw.js` en `v2`. Arreglado: el diálogo del buscador se veía en Fotos (choque de clases), estilos del mapa que se colaban en Premios y Línea, fichas tapadas por la barra de pestañas en móvil, nombre de sección oculto en la barra de 3 páginas, velos y botones de cerrar distintos, campos de búsqueda que hacían zoom en iPhone. `IDENTIDAD.md` e `identidad.html` al día.
**Comprobado:** las 13 páginas en el navegador con servidor local a 1280 px y 375 × 812, claro y oscuro, con un script que mide áreas táctiles (≥ 40/44 px), desbordes, contraste AA y la barra; abrir, cerrar con Esc y foco en Línea, Pines, Certificados y Fotos; consola sin errores de JS; `bash tests/run_all.sh` OK. **No comprobado:** revisión visual con capturas (el panel del navegador estaba oculto: todo se midió por script), «reducir movimiento» emulado y el iPhone real en modo PWA.

### PWA y splash (2026-11-25)
Instalable en iPhone (manifest, iconos, imagen de arranque, `sw.js`, splash). Probado en Chrome de escritorio: SW activo, sin red funciona, splash una vez por sesión. **Pendiente:** probar en el iPhone real. Ficha: `docs/features/pwa.md`.

## 3. Datos
- `certificates_archive_v1.csv`: 60 filas (56 certificados, 1 lanyard, 1 foto, 2 otros), columnas `evento` y `archivo`. **Pendiente:** 025 repetido; fecha del 022 supuesta; 18 certificados sin escanear.
- `ciudades_geo.csv`: 41 ciudades únicas, 16 con pin, estados visitada/futura/sin fecha. **Coordenadas aproximadas:** revisar Planes de Son ("revisar") y Christiania ("media").
- `aeropuertos_geo.csv`: 11 aeropuertos.
- `mis_viajes.xlsx`: histórico. Desde el esquema v2 (06/11/2026) los viajes viven en la base de datos (`importar-viajes`).

## 3b. Base de datos (`herramientas/archivo_db`)
| Parte | Estado | Cómo se comprobó |
|---|---|---|
| Fotos con personas `web/fotos.html` (ficha `docs/features/fotos.md`): sellos agrupados por mes, filtro por año, buscador sin mayúsculas ni acentos, visor con personas, anterior/siguiente y Esc. Datos: `archivo.py fotos-web` (WebP 1600 px + miniatura, HEIF incluido) y `exportar` con `web`/`mini` | Hecho (23/11/2026) | `test_fotos_web`; navegador a 1280 px y 390 px, claro y oscuro: 26 fotos reales, búsqueda («nuria», «KARINA gibért»), visor con flechas y Esc (foco vuelve al sello), aviso si falta `archivo.json`. Visor sin recortar fotos verticales, con zoom (doble toque, pellizco, rueda, teclas), deslizar, «Ver las N fotos del evento», «En el mapa» (sin enlace profundo), Descargar y vista Mesa; nombres con Instagram (`persona`, esquema v4, base real migrada con copia el 23/11/2026) abren su perfil. Filtro «Todas», sugerencias de nombres (combobox con teclado), pies de foto (`archivo.py foto`, `test_nota_de_foto`), búsqueda por principio de palabra y visor inerte al fondo. **No emulado:** «reducir movimiento» (solo revisado en código); Tab dentro del visor solo revisado en código |
| Pasaporte LEGO `web/pasaporte-lego.html` (ficha `docs/features/sellos-lego.md`): portada + una página por tienda, que se pasan con botones, ← →, y deslizando; sellos torcidos con tinta irregular; ficha al tocar (tienda, ciudad, viaje con fechas y km); tinta invertida en oscuro. Datos: `archivo.py sello --diseno --imagen` (varios por tienda y día, sin cambio de esquema) y `totales.sellos` en `exportar`; 18 sellos recortados de los escaneos (WebP con transparencia en `web/img/sellos/`, fuera de git) | Hecho (25/11/2026) | `test_sello_varios_por_tienda`; base real: copia previa, `resumen` con sellos: 18; navegador a escritorio y 390 px, claro y oscuro, teclado (Espacio abre, Esc cierra, foco vuelve al sello), consola sin errores. Recortes de tinta débil (flor, minifigura del trofeo) legibles pero tenues. **No emulado:** «reducir movimiento» y deslizar con el dedo (solo revisados en código); el enlace del menú lo añade la integración |
| Esquema: eventos, objetos, personas, fotos, charlas, importaciones | Hecho | Creación y validación de claves foráneas y restricciones |
| Importación de lanyards (archive.json) | Hecho | Repetida dos veces: no duplica |
| Importación del catálogo (CSV) | Hecho | 60 filas, 40 con imagen en `web/img/certificados/`; repetida: 0 nuevas |
| Fotos con personas (formato `AAAA/MM/DD - Nombre \| Nombre`) | Hecho | Repetida: 0 nuevas. Aviso de "Minguela"/"Minguella" |
| Charlas (keynote, mesa redonda, pitch) | Hecho | Repetida: no duplica |
| Exportación a JSON para la web | Hecho | Probado; la web todavía no la lee |
| Importación desde `gente.zip` con control de EXIF y ficheros que faltan | Hecho | Prueba con zip sintético: repetir no duplica; avisos correctos |
| Charlas con ruta local (sin URL) desde fichero | Hecho | Repetir no duplica |
| Esquema v2: viajes, visitas, lugares, aeropuertos, sellos, objetos y fotos sin evento | Hecho | `tests/test_archivo_db.py`: migración v1→v2 sin pérdida, estructura igual a `schema.sql`, totales del Excel (39 ciudades, 16 viajes, 11 países, 3 continentes, 9 aeropuertos) |
| Fotos reales de gente.zip | Hecho | 26 fotos, 17 eventos, 42 personas (06/11/2026). 2 fotos sin nombres y 1 vídeo pendientes |
| Esquema v3: km por viaje (`trips.km_manual`; si está vacío se calculan por círculo máximo, ida y vuelta desde Barcelona) | Hecho | `test_km_viajes` (Barcelona–Madrid ≈ 1.010 km ida y vuelta, escala BCN–DOH–CPT, manual, futuro fuera del total). Base real migrada el 23/11/2026 con copia previa: 52.731 km (sin Praga, futuro); `archivo.json` con `totales.km`, `viajes[].km` y `viajes[].vuelos` |
| Comando `viaje` (alta y edición; `--km` para km reales) | Hecho | `test_viaje_alta_y_edicion` (no duplica, edita solo lo pasado, rechaza aeropuertos que no existen). 23/11/2026: añadido Women in Tech Global Awards (París, 3–4 dic) y renombrado el de noviembre a Global Europe Awards |
| Pulido de datos: `pulir` (lugar de eventos, fechas de visitas, notas caducadas), `lugar` (coordenadas), `pin`, nivel de premio en `exportar` | Hecho | `test_pulir`, `test_lugar_y_pin`, `test_nivel_premio`. 23/11/2026 en la base real (copia previa): coordenadas confirmadas con Nominatim (MónNatura Pirineus, antes «Planes de Son»; Christiania, Doha, A Coruña, Figueres), 2 pines de París (El Principito, Ciudad de París). Con los datos de Carla: 25 de 27 eventos con lugar (`evento --slug`), Bruselas en ago 2024, sur de Francia en Semana Santa 2023 (7–10 abr), viaje de noviembre con vuelta por CDG (km a mano: 1.747). `totales.km` = 53.344, `totales.premios` por nivel |
| Esquema v5: categoría común en objetos (4 categorías desde el catálogo); `pulir` completa continente/región, modalidad, país y categoría de eventos; `viaje --nota` | Hecho | `test_categorias`, `test_pulir_coherencia`, `test_base_antigua_pide_migrar`, `test_viaje_nota_de_visita` (este destapó un fallo: `viaje --ciudad` duplicaba la visita sin fecha). 23/11/2026 en la base real (copia previa, v4→v5): 59 objetos y 12 eventos con categoría, 12 lugares completados |
| Vídeos de charlas | **Pendiente** | — |

## 4. Documentación y organización
- **Git** local (rama `main`); `.gitignore` deja fuera base, copias, fotos, vídeos y certificados.
- `AGENTS.md` es la fuente única para agentes; `CLAUDE.md` lo importa. Mapa de documentos y definición de «hecho» en `AGENTS.md`.
- `docs/architecture.md`, `docs/data-model.md`, `docs/features/` (fichas), `docs/MIGRACION_SUPABASE.md`.
- `.claude/settings.json`: permisos del proyecto. `.editorconfig` y salida UTF-8 en `archivo.py`.
- `docs/PROYECTO.md`: especificación general (idea, modelo de datos, digitalización, web, fases, riesgos).
- `docs/DECISIONES.md`: por qué se eligió cada cosa.
- `docs/PENDIENTES.md`: lista de tareas priorizada.
- `docs/FOTOGRAFIA.md`: guía para la persona.
