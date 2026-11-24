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
| Intervenciones en público `web/intervenciones.html` (ficha `docs/features/intervenciones.md`): resumen por tipo, lista por mes y año, reproductor con «Sin grabación todavía»; vídeos en `web/video/` (fuera de git) | Hecho (23/11/2026) | Navegador a 1280 y 390 px, claro y oscuro, Tab + Enter; hoy salen 2 de 4 (faltan `charlas.txt`); reproducción real sin probar |
| Lanyards en línea de tiempo `web/lanyards.html` (ficha `docs/features/lanyards.md`): carril con años, clic gira, doble clic / F / pulsación larga abren la ficha, evento enlazado con `archivo.json` | Hecho (23/11/2026) | Navegador a 1280 px y 390 px, claro y oscuro; clic, doble clic, F, flechas y Esc; sin `archivo.json` y sin reverso. **No probados:** rueda y arrastre a mano, pulsación larga con dedo real, «reducir movimiento». «Ver el evento» oculto hasta que haya página de eventos |
| Pines por ciudad `web/pines.html` (ficha `docs/features/pines.md`): contadores, grupos por país con «Otros países», chapa por pin (código si no hay foto), ficha con sello, «Ver en el mapa» (`mapa.html?viaje=`) y «Su viaje» (resalta los del viaje); sin medidas ni caja | Hecho (23/11/2026) | Navegador a 1280 px y 390 px (hoja inferior), oscuro y claro (claro solo a 390 px); ratón, Tab, Enter y Esc; `?viaje=` abre el viaje en el mapa. Datos hoy: 17 pines, 16 ciudades, 8 países, sin fotos (**ruta de `front_web` y el camino con foto, no probados**) |
| Certificados `web/certificados.html` (ficha `docs/features/certificados.md`): contadores, buscador sin acentos, vistas Todos/Con premio/Por escanear, hojas por año con miniatura y ficha con teclado | **En construcción** | Escrita; `node --check` y `tests/run_all.sh` OK. **Sin probar aún en navegador** (escritorio, 390 px, claro/oscuro, teclado) |
| Premios `web/premios.html` (ficha `docs/features/premios.md`): vitrina de cristal con 23 medallas en 4 estantes, resumen por nivel y año, ficha con «Ver el certificado» / «Por escanear» | Hecho (23/11/2026) | Navegador a escritorio y 390 px, claro y oscuro, teclado (Tab, flechas, Esc); `contar()` con node = 23 (7/2/8/6). «Reducir movimiento» revisado en CSS, no emulado |
| Línea del tiempo, personas, buscador físico | **Pendiente** | No empezado |

## 3. Datos
- `certificates_archive_v1.csv`: 60 filas (56 certificados, 1 lanyard, 1 foto, 2 otros), columnas `evento` y `archivo`. **Pendiente:** 025 repetido; fecha del 022 supuesta; 18 certificados sin escanear.
- `ciudades_geo.csv`: 41 ciudades únicas, 16 con pin, estados visitada/futura/sin fecha. **Coordenadas aproximadas:** revisar Planes de Son ("revisar") y Christiania ("media").
- `aeropuertos_geo.csv`: 11 aeropuertos.
- `mis_viajes.xlsx`: histórico. Desde el esquema v2 (06/11/2026) los viajes viven en la base de datos (`importar-viajes`).

## 3b. Base de datos (`herramientas/archivo_db`)
| Parte | Estado | Cómo se comprobó |
|---|---|---|
| Fotos con personas `web/fotos.html` (ficha `docs/features/fotos.md`): sellos agrupados por mes, filtro por año, buscador sin mayúsculas ni acentos, visor con personas, anterior/siguiente y Esc. Datos: `archivo.py fotos-web` (WebP 1600 px + miniatura, HEIF incluido) y `exportar` con `web`/`mini` | Hecho (23/11/2026) | `test_fotos_web`; navegador a 1280 px y 390 px, claro y oscuro: 26 fotos reales, búsqueda («nuria», «KARINA gibért»), visor con flechas y Esc (foco vuelve al sello), aviso si falta `archivo.json`. Visor sin recortar fotos verticales, con zoom (doble toque, pellizco, rueda, teclas), deslizar, «Ver las N fotos del evento», «En el mapa» (sin enlace profundo), Descargar y vista Mesa; nombres con Instagram (`persona`, esquema v4, base real migrada con copia el 23/11/2026) abren su perfil. Filtro «Todas», sugerencias de nombres (combobox con teclado), pies de foto (`archivo.py foto`, `test_nota_de_foto`), búsqueda por principio de palabra y visor inerte al fondo. **No emulado:** «reducir movimiento» (solo revisado en código); Tab dentro del visor solo revisado en código |
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
