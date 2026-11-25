# Pendientes (priorizados)

## Ahora (bloquean lo siguiente)
1. **Lote real de lanyards** con HEIC del iPhone, en parejas. Revisar la ventana de revisión y el CSV. (Pendiente de la persona.)
2. **Calibrar la impresora:** imprimir `plantilla_calibracion_A4_v3.pdf` al 100 %, medir la regla de 100 mm y ejecutar `--medir-regla`.
3. **Sincronizar datos reales** en la web y revisar la pared con lanyards reales (aspecto, tamaños, balanceo).

## Datos
0a. **Fotos:** quién sale en `2026_03_26 -.jpg` y `2025_11_12.jpg` (sin nombres, no importadas). Gente.zip ya está importado.
0b. **Charlas grabadas:** hechas las 2 de `datos/intervenciones/` (entrega y discurso del Aspiring Teen Award, París, 20/11/2026). Faltan los vídeos de otras charlas (HealthTech 2030, Mesa redonda TIC…) si existen: añadir una línea a `datos/entrada/charlas.txt`, `importar-charlas`, `exportar` y `preparar_vercel.py`. El vídeo de `gente.zip` es un mensaje grabado por otra persona, no una intervención de Carla: no va a charlas.
0c. **Listado de eventos completo:** comprobar que el catálogo y los objetos cubren todos los eventos (ver `archivo.py resumen`).
3b. **Escanear los certificados que faltan** (en el catálogo sin fichero): 001–006, 008, 009, 012, 013, 015, 016, 018, 020, 022, 033, 038, 044. Ponerlos en `datos/certificados_originales/`, rellenar la columna `archivo` del catálogo e importar.
4. Resolver el **025** repetido en `certificates_archive_v1.csv` (renumerar 2026 como 026–045 o mantener etiquetas impresas).
5. Confirmar la fecha del **022** (LaIA List, supuesta septiembre 2025).
6. Buscar certificado o lanyard de los viajes sin objeto: FLL Open Africa (may 2025), Girls Go STEM Meet Up (mar 2026), MBA League (may 2026), TikTok × OMS Ginebra (may 2026), MonNatura (jun–jul 2026), Changemaker Camp (ago 2026), RedeSTEAM (oct 2026).
7. **Lugar de 2 eventos:** Taula rodona Escola Horitzó (feb 2026) y Hope! (jul 2026). Cuando se sepa: `archivo.py evento --slug SLUG --ciudad X` y `archivo.py pulir`.
7b. **Categoría de 15 eventos sin certificado** (Ciencia y tecnología, Divulgación, Emprendimiento o Impacto social): `archivo.py evento --slug SLUG --categoria X`.
7d. Lugares nuevos de los pines sin país ni continente (Colonia, Filipinas, Hannover, Lituania, Malta, Polonia, Salzburgo, Seattle, Viena).
7c. Fechas que faltan: 6 eventos solo con año o mes (opcional).
8. Decidir si FLL Masterpiece (feb 2024) y la final de Alicante (mar 2024) son fases distintas.
9a. **Km por carretera (opcional):** en coche y tren los km calculados van en línea recta (se quedan cortos). Si sabes los reales de un viaje: `archivo.py viaje --slug SLUG --km 1234` (sustituyen al cálculo).
9. Decidir si el 012 (HP CodeWars Team Photo) es certificado o foto.
9b. **Caja y página física** de cada certificado y lanyard (`caja_fisica`, hoy vacía en los 101 objetos): sin esto el buscador no puede decir dónde está cada cosa.
9c. **Copia automática:** que `exportar` haga `copia` antes, si la última tiene más de un día (hoy depende de acordarse).

## Web · próximos módulos (en este orden)
Hecho: identidad (`docs/diseno/IDENTIDAD.md`), pared, mapa, fotos, certificados, premios, pines, lanyards, intervenciones con vídeo, navegación pasaporte y publicación en Vercel.

**Diseño elegido por Carla (25/11, maquetas A/B en https://claude.ai/artifact/R6kS6vXg35a6BC1qb1ELxh):**
- Evento → **B «Página de cuaderno»** (collage, polaroids, tira del viaje). Muchos eventos tienen poco (una foto o un certificado): con poco contenido debe verse completo y bonito, no vacío.
- Inicio → **B «Recorrido narrado»** (el año contado mes a mes, cifras dentro del relato).
- Línea del tiempo → **las dos**: «Río horizontal» y «Salas por año», con un conmutador de vista.
- Pasaporte LEGO → **B «Pasaporte que se hojea»**.

1. **Página de evento** (`evento.html?e=<slug>`): el centro del archivo. Reúne lanyard, certificados, premios, fotos, personas, charlas con vídeo y su viaje en el mapa. Activa el «Ver el evento» que hoy está desactivado en intervenciones, y todas las demás páginas enlazan aquí. Datos: ya están en `archivo.json`.
2. **Inicio «Tu año en cifras»** (ficha `cifras-e-hitos.md`, acordada): sustituye a la pared como primera página. La pared aún muestra 6 lanyards de demostración, y es lo primero que se ve. La pared pasa a ser un módulo más.
3. **Personas**: una ficha por persona con sus fotos, charlas y eventos en común. Después, la red (grafo) si aporta.
4. **Línea del tiempo** 2018–hoy, con los hitos de `cifras-e-hitos`. Absorbe la idea de la «sala de museo por año»: no hacer las dos.
5. **Pasaporte LEGO** (ficha `sellos-lego.md`, verificada): hecha la página y los 18 sellos. Falta: sellos en la ficha de cada viaje y la tienda como punto del mapa; enlace en el menú.
6. **Buscador** (también Ctrl+K desde cualquier página): eventos, personas, lugares y objetos. Con `caja_fisica` responde «caja 3, página 12» (modo archivo físico). Hoy ningún objeto tiene caja: primero, apuntarlas.

## Web · UI/UX (repaso transversal)
- **Coherencia entre las 9 páginas** (las hicieron sesiones distintas): cabecera, estados vacíos, modo claro y oscuro, tokens de `style.css` sin colores sueltos. Un repaso completo con `make-interfaces-feel-better` y la guía viva `identidad.html` al día.
- **Teclado en la pared 3D:** hoy los lanyards no se alcanzan con Tab. Hace falta una lista accesible o un foco que recorra las piezas.
- **Móvil real** (no solo emulado a 390 px): tacto en la pared y en el mapa, la barra inferior y la reproducción de vídeo en iPhone.
- **Rendimiento en Vercel:** caché larga para `img/` y `video/` en `vercel.json`, e imágenes con `loading="lazy"` en todas las páginas.

## Herramienta
18. Probar las ventanas de revisión con pantalla real (`cv2.imshow`).
20. Empaquetar para Windows con un instalador sencillo (opcional).

## Riesgos abiertos
- Pérdida de datos: no hay copia automática. Recomendar copia periódica de `LanyardArchive`.
- Web publicada en Vercel con datos completos (decisión de Carla, 24/11/2026). El enlace no se indexa (`noindex`), pero quien lo tenga lo ve todo. No compartirlo.
- La base solo existe en este ordenador y en `datos/copias/`: copiar `datos/copias/` fuera (nube o USB) de vez en cuando.
