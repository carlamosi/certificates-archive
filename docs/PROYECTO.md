# Certificates Archive — Especificación del proyecto

> Archivo personal, digital y físico, de todo lo que ha dejado huella en mi trayectoria: certificados, lanyards, pines, fotos, grabaciones y viajes. Primero un archivo ordenado; después una web interactiva tipo museo, solo para mí.

---

## 1. Idea general

Quiero conservar y poder **explorar** mis eventos, premios y viajes de forma organizada. El proyecto tiene dos caras que se alimentan entre sí:

| Cara | Qué es | Estado |
|---|---|---|
| **Archivo físico** | Certificados impresos y ordenados cronológicamente en el *Certificates Archive*; lanyards y pines guardados | En marcha |
| **Archivo digital** | Todo digitalizado y catalogado en datos limpios, con imágenes recortadas y medidas reales | En marcha |
| **Web interactiva** | Museo personal con pared de lanyards 3D, línea del tiempo, mapa, personas y buscador del archivo físico | Pendiente |

**Principio rector:** *lo más simple que funcione.* Pocas preguntas, pocos pasos, datos limpios que sirvan para la web futura. No sobrediseñar.

**Audiencia de la web:** solo yo. (Esto simplifica la privacidad; si algún día se publica, hay que difuminar nombres completos, QR y códigos de los certificados.)

---

## 2. Qué se archiva

| Tipo | Descripción | Origen | Caras / piezas |
|---|---|---|---|
| **Certificado** | Diplomas y reconocimientos de concursos y cursos | Escáner HP Smart Tank 7010 | 1 |
| **Lanyard / acreditación** | Tarjeta del evento. Normalmente de eventos; los concursos dan certificado | Fotografía sobre plantilla ArUco | **Siempre 2** (anverso y reverso) |
| **Pin** | Colección de pines, uno por ciudad | Fotografía sobre plantilla ArUco | 1 |
| **Foto** | Fotos de eventos y mesas redondas, con las personas que salen | Carpeta de Drive (26 fotos importadas, JPG y HEIF) | 1 |
| **Grabación** | Mis charlas: keynote, mesa redonda, pitches de concursos | Por recopilar | Vídeo / audio |
| **Viaje** | Viajes con países, ciudades, aeropuertos, fechas y pins | Excel `mis_viajes.xlsx` | — |

Los lanyards no se repiten: no hay dos iguales. Hay unos 10 por ahora.

---

## 3. Modelo de datos

> Diagrama conceptual de la idea original (v1). El modelo vigente está en `docs/data-model.md`.

> Implementado en SQLite: `herramientas/archivo_db/schema.sql`. Las secciones 3.1–3.4 describen el modelo conceptual.

Un **evento** es el centro. Todo lo demás cuelga de él.

```
Viaje ── 1:N ── Ciudad visitada
  │
  └── 0..1 ── N  Evento ── 1:N ── Objeto (certificado | lanyard | pin | foto | grabación)
                                      │
                                      ├── N:M ── Persona (solo fotos)
                                      └── 1:N ── Archivo (imagen / vídeo, por cara)
```

El vínculo viaje–evento es **opcional**: los eventos en Barcelona (HealthTech 2030, Smart City Congress, mesas redondas) no son viajes.

### 3.1 Evento

| Campo | Ejemplo |
|---|---|
| `id` | `2026-10-23_healthtech-2030-innovation-challenge` |
| `evento` | HealthTech 2030 Innovation Challenge |
| `fecha` | `2026-10-23` (ISO; se admite `AAAA-MM` si no se sabe el día) |
| `organizador` | Xartec Salut |
| `lugar` / `ciudad` | UPC · Sala Ágora / Barcelona |
| `modalidad` | presencial / virtual |
| `viaje_id` | vacío si no fue un viaje |

### 3.2 Objeto

| Campo | Notas |
|---|---|
| `tipo` | certificado, lanyard, pin, foto, grabación |
| `rol` / `premio` | Speaker, ganadora, finalista, 1st Prize, Top 10… |
| `categoria` | robótica, IA, neurociencia, divulgación… (propuesta mía, editable) |
| `caja_fisica` | Dónde está en el archivo físico (caja / página) |
| `ancho_mm`, `alto_mm` | Medidas reales (lanyards y pines) |
| `forma` | `rectangular` o `libre` (p. ej. la medalla de África) |
| `agujero_mm`, `anclaje_x`, `anclaje_y` | Diámetro y centro del orificio, para colgar el cordón en 3D |

### 3.3 Personas (solo fotos)

Cada foto guarda la fecha, el evento y la lista de personas que salen además de mí. Formato de entrada: `AAAA/MM/DD - Nombre | Nombre | Nombre`. Esto permite fichas por persona y un grafo de coincidencias.

Ejemplo ya definido: mesa redonda de estudiantes TIC en el Ateneu Barcelonès, organizada por Dona Digital, 2025-09-09, con Persona A, Persona B, Persona C y Persona D.

### 3.4 Viajes (el Excel que ya existe)

Hojas: **Resumen, Viajes, Ciudades, Países, Continentes, Aeropuertos**. Es la fuente de verdad de los viajes; no se rehace, se **conecta**.

Ficheros derivados ya generados: `ciudades_geo.csv` (41 ciudades únicas con latitud y longitud aproximadas, estado visitada/futura/sin fecha y pin sí/no) y `aeropuertos_geo.csv` (11 aeropuertos).

---

## 4. Reglas y convenciones

- **Fechas** siempre ISO (`2025-03-29`). Sin "March" bajo encabezados de año.
- **IDs inmutables y únicos.** Nunca se reutilizan. El número del archivo físico es una columna aparte (`num_archivo`).
- **Nombres de fichero:** `AAAA-MM-DD_evento-en-minusculas_cara.webp` (ordenan solos).
- **Unidades:** milímetros reales, medidos con la plantilla de calibración.
- **Orden físico:** cronológico.
- **Eventos virtuales** (hechos desde casa): **sin chincheta** en el mapa; van a una vista aparte, "Desde casa".
- **Los pines pesan:** son un tipo de objeto de primera clase, ligado a una ciudad, con su ID del álbum y la fecha del viaje.

---

## 5. Digitalización

### 5.1 Certificados

1. Imprimir y ordenar físicamente en el *Certificates Archive*.
2. Escanear con la HP Smart Tank 7010 (300 ppp, color).
3. Guardar el original (PDF/TIFF) y una versión ligera WebP para la web.
4. Registrar evento, fecha, organizador y rol en el catálogo.

Estado actual del catálogo: ver `docs/ESTADO.md`.

### 5.2 Lanyards y pines — herramienta *Lanyard Archive*

**Flujo:** se fotografían **en orden: anverso, reverso, anverso, reverso…**; cada pareja es un lanyard. El programa calibra, recorta, enseña el resultado una vez y pregunta evento, fecha y lugar una sola vez por pareja.

**Plantilla de calibración:** hoja A4 con 4 marcadores ArUco (`plantilla_calibracion_A4_v3.pdf`), impresa al 100 %. Da medidas en mm reales y corrige la perspectiva.

**Qué hace automáticamente**
- Recorte enderezado con **transparencia**, también en el orificio.
- Orificios: solo **arriba**, redondos o con rotura al borde, **máximo 2**.
- **Rectangulares:** anverso y reverso reciben la **misma medida**. **Formas libres** (medallas): se recorta la silueta real y la medida es la del anverso.
- Avisos de calidad: luz desigual, desenfoque, reflejo, hoja inclinada.
- **Punto de anclaje** del orificio para colgar cordón o mosquetón en 3D.

**Salida** (carpeta `Lanyards_procesados` junto a las fotos, se abre sola):

```
web/        WebP con transparencia  → para la web
master/     PNG con transparencia   → máxima calidad
originals/  copia de las fotos originales
archive.json  archive.csv          → una fila por lanyard
```

**Cómo fotografiar bien:** hoja plana (pegada a un cartón), los 4 marcadores visibles, luz difusa de frente (ventana con cortina), móvil paralelo a la mesa a 30–40 cm, cámara 1x, agujero hacia arriba. Objetos blancos: cartulina negra debajo.

**Límites conocidos:** la exactitud depende de la escala real de la impresora (se corrige una vez con `--medir-regla`); objetos blancos sobre papel blanco no se detectan solos.

**Comandos:** `py lanyard_archive.py` · `--pin` (una foto = un pin) · `--rapido` · `--medir-regla 99.6` · `--input fotos.zip`.

### 5.3 Fotos de mesas redondas

- Convertir HEIF → WebP conservando la fecha EXIF.
- Línea por foto con fecha, evento y personas; el script crea la tabla de personas.
- Decidir antes de publicar si alguna persona necesita permiso.

### 5.4 Grabaciones

- Cada grabación cuelga de un evento y se muestra **junto a su lanyard**.
- Campos: tipo (keynote / mesa redonda / pitch), duración, idioma y **ruta local** del vídeo (`archivo_local`); sin URL.
- Opcional: transcripción automática para buscar dentro de las charlas.

---

## 6. La web interactiva

Diseño **creativo**, con UX cuidado, inspirado en la app *Been* para la parte de viajes.

| Módulo | Qué hace |
|---|---|
| **Pared de lanyards 3D** | Cuelgan de su anilla; se balancean al pasar el cursor y giran al clic para mostrar el reverso |
| **Línea del tiempo** | Horizontal, de 2018 a hoy, con densidad por años |
| **Mapa con capas** | Capa de **viajes** (países, ciudades, arcos de vuelo) y capa de **eventos** (pin con ficha, lanyard y foto) |
| **Estilo Been** | Contadores héroe (ciudades, países, continentes, aeropuertos, % del mundo); países en 3 estados: visitado, tránsito (solo aeropuerto) y futuro |
| **Sala de museo** | Cada año es una sala con cartelas (título, fecha, lugar, rol) junto a cada pieza |
| **Pines** | Colección visible, por ciudad, enlazada al mapa |
| **Red de personas** | Grafo de las personas de las fotos conectadas por eventos compartidos |
| **Contadores y filtros** | Premios por año, rol (Speaker / ganadora / participante), categoría |
| **Modo archivo físico** | Buscador que responde "caja 3, página 12"; la web es también el índice del *Certificates Archive* |
| **Grabaciones** | Vídeo/audio junto al lanyard del evento |
| **Desde casa** | Eventos virtuales, fuera del mapa |

**Visualización 3D del lanyard:** tarjeta con textura de anverso y reverso, anclada en el punto del orificio; la cuerda se dibuja como curva, **no hace falta escanear el hilo**. Opción ligera primero (Three.js con balanceo simple); simulación física completa solo si merece la pena.

**Idea opcional (no confirmada):** integrarlo como una ventana más dentro de CarlOS, el portfolio con interfaz estilo Mac.

---

## 7. Hojas de ruta

| Fase | Contenido | Estado |
|---|---|---|
| **0. Datos limpios** | Catálogo de certificados con fechas ISO e IDs; geocodificar ciudades y aeropuertos | Hecho (v1) |
| **1. Herramienta de lanyards** | Plantilla ArUco, recorte, medidas, JSON/CSV | Hecho; falta probarla con fotos reales y calibrar la impresora |
| **2. Unir todo** | Vincular eventos con viajes; un único JSON con certificados, lanyards, pines, fotos | Hecho (base SQLite v2, `archivo.py exportar`) |
| **3. Prototipo del mapa** | Capa de viajes + capa de eventos, con pines destacados | Pendiente (siguiente paso propuesto) |
| **4. Pared de lanyards 3D** | Con los primeros 2–3 lanyards recortados | Prototipo hecho con datos de demostración |
| **5. Museo, línea del tiempo, personas** | Resto de módulos | Pendiente |
| **6. Grabaciones y fotos** | Recopilar y enlazar | Pendiente |

**Siguiente paso concreto:** imprimir la plantilla A4 al 100 %, medir la regla impresa y ejecutar `--medir-regla`; fotografiar el lanyard de iFest y comprobar el resultado.

---

## 8. Pendientes y decisiones abiertas

- [ ] Resolver la numeración repetida **025** y confirmar la fecha del **022** (LaIA List, supuesta septiembre 2025).
- [ ] Revisar **`categoria`** de cada certificado (propuesta automática).
- [ ] Buscar certificado o lanyard de **viajes sin objeto en el archivo**: FLL Open Africa (mayo 2025), Girls Go STEM Meet Up (mar. 2026), MBA League (mayo 2026), TikTok × OMS en Ginebra (mayo 2026), MonNatura (jun.–jul. 2026), Changemaker Camp (ago. 2026), RedeSTEAM (oct. 2026).
- [ ] Futuros: París (nov. 2026) y Praga (nov. 2026) ya tienen sitio en el mapa.
- [ ] Revisar las coordenadas marcadas como **"revisar"** (Planes de Son) o **"media"** (Christiania).
- [ ] Decidir si FLL Masterpiece (feb. 2024) y la Final Nacional de Alicante (mar. 2024) son fases distintas del mismo evento.
- [ ] Decidir si el **012 (HP CodeWars · Team Photo)** es un certificado o una foto.
- [ ] Calibrar la escala de la impresora y probar la herramienta con fotos reales.
- [ ] Recopilar las **grabaciones**.
- [ ] Decidir cuándo (si alguna vez) se publica la web y qué se difumina.
- [ ] Hacer **copia de seguridad** periódica de toda la carpeta.

---

## 9. Ficheros del proyecto

| Fichero | Para qué |
|---|---|
| `certificates_archive_v1.csv` | Catálogo de certificados limpio |
| `ciudades_geo.csv`, `aeropuertos_geo.csv` | Datos geográficos para el mapa |
| `mis_viajes.xlsx` | Histórico de viajes (la fuente de verdad es `datos/archivo.sqlite`) |
| `plantilla_calibracion_A4_v3.pdf` | Plantilla de calibración para las fotos |
| `docs/PROYECTO.md` | Este documento |

---

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| Medidas erróneas por escala de impresora | `--medir-regla` una vez; comprobar con regla física |
| Fotos con mala luz o hoja curvada | Seguir la guía de fotografía; los avisos del programa |
| Emparejado de caras roto si falla una foto | Repetir la foto mala y procesar esas dos en una carpeta nueva |
| Pérdida de datos | Originales conservados; copia de seguridad periódica |
| Datos personales en certificados al publicar | Web solo para mí; difuminar si se publica |
| Complejidad excesiva | Mantener las fases pequeñas; no añadir funciones sin necesidad |
