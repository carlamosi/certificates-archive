# Modelo de datos (esquema v5)

Fuente de verdad: `herramientas/archivo_db/schema.sql` (`PRAGMA user_version = 5`). Este documento explica el porqué; si no coincide con `schema.sql`, manda `schema.sql` y se corrige este.

## Dos ejes y lo que cuelga de ellos
```
viaje (trips) ──► visitas (visits: ciudad + fechas) ──► lugar (places: lat/lng)
  │                                                       ▲
  ├── evento (events.trip_id) ── events.place_id ──────────┘
  │     ├── objetos: lanyard, certificado (objects.event_id)
  │     ├── fotos (photos.event_id) ──► personas (photo_people)
  │     └── charlas (talks) ──► personas (talk_people)
  ├── fotos del viaje sin evento (photos.trip_id)
  └── pines y sellos LEGO (objects.trip_id + objects.place_id)
sueltos: certificados online (objects con solo título), fotos sin evento ni viaje
```

## Tablas
| Tabla | Qué es | Clave natural (para importar sin duplicar) |
|---|---|---|
| `events` | Algo a lo que fuiste: final, campamento, congreso, mesa redonda | `slug` = `fecha_nombre` |
| `trips` | Viaje, familiar o por un evento; fechas opcionales | `slug` |
| `places` | Ciudad con país, continente y coordenadas | `(nombre, pais)` |
| `visits` | Una ciudad en unas fechas, dentro de un viaje o suelta | `(place_id, trip_id, inicio)` (se busca con `IS` porque puede haber NULL) |
| `airports` | Aeropuertos usados | `iata` |
| `objects` | Lanyards, certificados, pines, sellos, fotos de equipo, otros | `uid` |
| `people` | Personas de fotos y charlas (`instagram`: solo el usuario) | `clave` = nombre sin acentos en minúsculas |
| `photos` | Fotos con personas | `archivo` (nombre del fichero) |
| `talks` | Charlas grabadas (ruta local del vídeo, sin URL) | evento + tipo + título + ruta del vídeo |
| `photo_people`, `talk_people` | Relaciones N:M | par de ids |
| `imports` | Control de importaciones ya hechas | `clave` |

## Reglas del dominio (las impone el código o el esquema)
- **Un objeto siempre cuelga de algo:** evento, viaje, lugar o al menos un título (`CHECK` en `objects`).
- **Certificados:** tienen evento solo si fue presencial (final, campamento, congreso, ceremonia); si no, quedan sueltos.
- **Sellos LEGO:** `tipo = 'sello'`, con fecha propia (el mes del diseño), sitio exacto (`sitio`), lugar y viaje.
- **Personas:** nunca se fusionan solas; nombres parecidos solo generan aviso.
- **Fechas:** texto ISO `AAAA`, `AAAA-MM` o `AAAA-MM-DD` (se admiten fechas incompletas).
- **Categoría:** `objects.categoria` es una de 4 (Ciencia y tecnología, Divulgación, Emprendimiento, Impacto social), sacada de `categoria_propuesta` del catálogo; la de un evento es la más común de sus objetos (`archivo.py pulir`).
- **Instagram:** `people.instagram` guarda solo el usuario (v4, sesión de fotos).
- **Nivel del premio:** se calcula al exportar desde el texto libre de `premio` (primer premio, podio, finalista, mención, ponente, participación); no se guarda. Exporta `objetos[].nivel` y `totales.premios`.
- **Lugar de un evento:** `archivo.py pulir` lo enlaza solo si la ciudad escrita coincide con un lugar con coordenadas, o si su viaje visita una única ciudad. Nunca adivina entre varias.
- **Lo futuro no cuenta** en los totales hasta que llega (como en el Excel).
- **Km de un viaje:** `trips.km_manual` si está relleno; si no, se calculan en `archivo.py` (haversine, en Python para no depender de SQLite) sobre la ruta Barcelona → salida → escala → llegada → ciudades por fecha, y vuelta por el mismo camino. Se exportan como `viajes[].km`, `viajes[].vuelos` (tramos entre aeropuertos, para los arcos del mapa) y `totales.km` (sin viajes futuros).
- **País visitado** = tiene una ciudad visitada o un aeropuerto usado (Catar cuenta por la escala en Doha).
- **Datos sensibles prohibidos:** salud, religión, orientación, opiniones políticas, datos de menores.

## Vistas (todo el seguimiento es calculado)
`v_viajes` (días, año, pasado/futuro/sin fecha) · `v_ciudades` · `v_paises` · `v_continentes` · `v_aeropuertos` (veces usado).

## Cambiar el esquema
1. Nueva migración `herramientas/archivo_db/migraciones/00N.sql` con `PRAGMA user_version = N`, y subir `ULTIMA` en `archivo.py` (`cmd_migrar` aplica en orden las que falten).
2. Actualizar `schema.sql` para que dé la misma estructura (lo comprueba `tests/test_archivo_db.py`).
3. `archivo.py migrar` hace copia previa y aplica todo en una transacción.
4. Mantener la portabilidad a Postgres (`docs/MIGRACION_SUPABASE.md`) y actualizar este documento.
