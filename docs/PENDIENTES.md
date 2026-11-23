# Pendientes (priorizados)

## Ahora (bloquean lo siguiente)
1. **Lote real de lanyards** con HEIC del iPhone, en parejas. Revisar la ventana de revisión y el CSV. (Pendiente de la persona.)
2. **Calibrar la impresora:** imprimir `plantilla_calibracion_A4_v3.pdf` al 100 %, medir la regla de 100 mm y ejecutar `--medir-regla`.
3. **Sincronizar datos reales** en la web y revisar la pared con lanyards reales (aspecto, tamaños, balanceo).

## Datos
0a. **Fotos:** quién sale en `2026_03_26 -.jpg` y `2025_11_12.jpg` (sin nombres, no importadas). Gente.zip ya está importado.
0b. **Charlas grabadas (vídeos del móvil, sin URL):** la persona indica en `datos/entrada/charlas.txt` la ruta de cada vídeo (keynote, mesa redonda, pitches) e importamos con `importar-charlas`. Primero: el vídeo de Rocío Vidal (de gente.zip) y los de `intervenciones/`.
0c. **Listado de eventos completo:** comprobar que el catálogo y los objetos cubren todos los eventos (ver `archivo.py resumen`).
3b. **Escanear los certificados que faltan** (en el catálogo sin fichero): 001–006, 008, 009, 012, 013, 015, 016, 018, 020, 022, 033, 038, 044. Ponerlos en `datos/certificados_originales/`, rellenar la columna `archivo` del catálogo e importar.
4. Resolver el **025** repetido en `certificates_archive_v1.csv` (renumerar 2026 como 026–045 o mantener etiquetas impresas).
5. Confirmar la fecha del **022** (LaIA List, supuesta septiembre 2025).
6. Buscar certificado o lanyard de los viajes sin objeto: FLL Open Africa (may 2025), Girls Go STEM Meet Up (mar 2026), MBA League (may 2026), TikTok × OMS Ginebra (may 2026), MonNatura (jun–jul 2026), Changemaker Camp (ago 2026), RedeSTEAM (oct 2026).
7. **Lugar de 19 eventos** (sin ciudad, el mapa no los pinta): FLL Junior 2019, FLL Masterpiece 2024, HP CodeWars, entrevista RN4, Tecnocamp, encuentro Persona E, Future Makers, Women Startup Challenge, Diada GrausTIC, STEM Women Congress, Calçotada IP, Escola Horitzó, MWC, Nit de les Telecos, taller Openchip, concurso Apolo (¿Torrejón?), HOPE, campamento Gran Canaria (¿qué pueblo?), Women in Tech Barcelona. Cuando se sepa: ciudad en el evento y `archivo.py pulir`.
7b. **Categoría de los eventos** (bloque 2): el catálogo ya trae `categoria_propuesta` en los 60 certificados, pero con nombres sin unificar (`emprendimiento/tecnología`, `tecnología`…). Unificar en 5–6 temas y cargarla.
7c. Fechas que faltan: viaje por el sur de Francia (sin año) y 6 eventos solo con año o mes.
8. Decidir si FLL Masterpiece (feb 2024) y la final de Alicante (mar 2024) son fases distintas.
9a. **Km por carretera (opcional):** en coche y tren los km calculados van en línea recta (se quedan cortos). Si sabes los reales de un viaje: `archivo.py viaje --slug SLUG --km 1234` (sustituyen al cálculo).
9. Decidir si el 012 (HP CodeWars Team Photo) es certificado o foto.

## Web
0g. **Aplicar la guía de diseño** (`docs/diseno/WEB_DISENO.md`): sustituir el logo cónico, la tipografía serif por Open Sauce One y el tema oscuro con amarillo.
0h. **Generar la identidad** con `docs/diseno/PROMPT_IMAGENES_IDENTIDAD.md` y rehacer el símbolo en vector.
0d. ~~Exportar la base a `web/data/archivo.json` y que `web/app.js` la lea~~ (hecho: `docs/features/datos-web.md`; falta pintar los datos en cada página).
0e. **Página de personas:** ficha por persona con sus fotos y charlas (relaciones de la base de datos).
0f. **Página de charlas:** reproductor o enlace junto al lanyard del mismo evento.
10. **Probar en móvil** (viewport 390 px, tacto).
11. **Mapa con dos capas** (viajes y eventos) con Leaflet + OpenStreetMap. Eventos virtuales ("Desde casa") fuera del mapa.
12. Línea del tiempo horizontal 2018–hoy.
13. Sala de museo (una sala por año, cartelas).
14. Pines como colección enlazada al mapa.
15. Red de personas (fotos de mesas redondas).
16. Modo archivo físico (caja / página).
17. Grabaciones junto al lanyard del evento (cuando existan).

## Herramienta
18. Probar las ventanas de revisión con pantalla real (`cv2.imshow`).
20. Empaquetar para Windows con un instalador sencillo (opcional).

## Riesgos abiertos
- Pérdida de datos: no hay copia automática. Recomendar copia periódica de `LanyardArchive`.
- Publicación futura: difuminar datos personales antes de cualquier publicación.
