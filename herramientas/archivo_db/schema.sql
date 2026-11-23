-- Certificates Archive · esquema SQLite (v4). Pasos: v1 -> v2 migraciones/002.sql, v2 -> v3 003.sql, v3 -> v4 004.sql
-- Fechas: texto ISO. Se admite AAAA, AAAA-MM o AAAA-MM-DD (cuando no se sabe el día).
-- Ninguna tabla guarda datos sensibles (salud, religión, orientación, etc.).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS places (
  id              INTEGER PRIMARY KEY,
  nombre          TEXT NOT NULL,
  region          TEXT NOT NULL DEFAULT '',
  pais            TEXT NOT NULL DEFAULT '',
  continente      TEXT NOT NULL DEFAULT '',
  lat             REAL,
  lng             REAL,
  coord_confianza TEXT NOT NULL DEFAULT '',
  UNIQUE (nombre, pais)
);

CREATE TABLE IF NOT EXISTS airports (
  iata     TEXT PRIMARY KEY CHECK (length(iata) = 3),
  nombre   TEXT NOT NULL DEFAULT '',
  place_id INTEGER REFERENCES places(id) ON DELETE SET NULL,
  lat      REAL,
  lng      REAL
);

CREATE TABLE IF NOT EXISTS trips (
  id         INTEGER PRIMARY KEY,
  slug       TEXT NOT NULL UNIQUE,
  nombre     TEXT NOT NULL,
  inicio     TEXT,                                      -- NULL si no se sabe
  fin        TEXT,
  transporte TEXT NOT NULL DEFAULT '',
  salida     TEXT REFERENCES airports(iata),
  llegada    TEXT REFERENCES airports(iata),
  escala     TEXT REFERENCES airports(iata),
  motivo     TEXT NOT NULL DEFAULT '',
  notas      TEXT NOT NULL DEFAULT '',
  km_manual  REAL CHECK (km_manual IS NULL OR km_manual >= 0)  -- si es NULL, los km se calculan (archivo.py)
);

-- Una visita = una ciudad en unas fechas, dentro de un viaje o suelta (p. ej. Andorra 2021).
CREATE TABLE IF NOT EXISTS visits (
  id       INTEGER PRIMARY KEY,
  place_id INTEGER NOT NULL REFERENCES places(id) ON DELETE RESTRICT,
  trip_id  INTEGER REFERENCES trips(id) ON DELETE SET NULL,
  inicio   TEXT,
  fin      TEXT,
  nota     TEXT NOT NULL DEFAULT '',
  UNIQUE (place_id, trip_id, inicio)
);
CREATE INDEX IF NOT EXISTS ix_visits_trip ON visits(trip_id);


CREATE TABLE IF NOT EXISTS events (
  id           INTEGER PRIMARY KEY,
  slug         TEXT    NOT NULL UNIQUE,                  -- ej. 2025-09-09_mesa-redonda-estudiantes-tic
  nombre       TEXT    NOT NULL,
  fecha        TEXT    NOT NULL CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]*'),
  organizador  TEXT    NOT NULL DEFAULT '',
  lugar        TEXT    NOT NULL DEFAULT '',                -- recinto: "UPC · Sala Ágora"
  ciudad       TEXT    NOT NULL DEFAULT '',
  pais         TEXT    NOT NULL DEFAULT '',
  modalidad    TEXT    NOT NULL DEFAULT '' CHECK (modalidad IN ('', 'presencial', 'virtual')),
  categoria    TEXT    NOT NULL DEFAULT '',                -- robótica, IA, neurociencia...
  notas        TEXT    NOT NULL DEFAULT '',
  place_id     INTEGER REFERENCES places(id) ON DELETE SET NULL,
  trip_id      INTEGER REFERENCES trips(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_events_fecha ON events(fecha);

-- Objetos físicos o digitales asociados a un evento: lanyards, certificados, pines, fotos de equipo...
CREATE TABLE IF NOT EXISTS objects (
  id           INTEGER PRIMARY KEY,
  uid          TEXT    NOT NULL UNIQUE,
  event_id     INTEGER REFERENCES events(id) ON DELETE RESTRICT,
  trip_id      INTEGER REFERENCES trips(id) ON DELETE RESTRICT,
  place_id     INTEGER REFERENCES places(id) ON DELETE RESTRICT,
  tipo         TEXT    NOT NULL CHECK (tipo IN ('lanyard', 'certificado', 'pin', 'sello', 'foto', 'otro')),
  titulo       TEXT    NOT NULL DEFAULT '',                -- si hay evento y está vacío, se usa el del evento
  organizador  TEXT    NOT NULL DEFAULT '',
  fecha        TEXT    NOT NULL DEFAULT '',                -- sellos: día en que se estampó
  sitio        TEXT    NOT NULL DEFAULT '',                -- "LEGO Store Tivoli", "Aeropuerto de Barcelona"
  rol          TEXT    NOT NULL DEFAULT '',
  premio       TEXT    NOT NULL DEFAULT '',
  num_archivo  TEXT    NOT NULL DEFAULT '',
  caja_fisica  TEXT    NOT NULL DEFAULT '',
  pin_id       TEXT    NOT NULL DEFAULT '',
  ancho_mm     REAL,
  alto_mm      REAL,
  forma        TEXT    NOT NULL DEFAULT '' CHECK (forma IN ('', 'rectangular', 'libre')),
  agujero_mm   TEXT    NOT NULL DEFAULT '',
  anclaje_x    REAL,
  anclaje_y    REAL,
  front_web    TEXT    NOT NULL DEFAULT '',
  back_web     TEXT    NOT NULL DEFAULT '',
  avisos       TEXT    NOT NULL DEFAULT '',
  created_utc  TEXT    NOT NULL DEFAULT '',
  CHECK (event_id IS NOT NULL OR trip_id IS NOT NULL OR place_id IS NOT NULL OR titulo <> '')
);
CREATE INDEX IF NOT EXISTS ix_objects_event ON objects(event_id);
CREATE INDEX IF NOT EXISTS ix_objects_tipo  ON objects(tipo);
CREATE INDEX IF NOT EXISTS ix_objects_trip  ON objects(trip_id);
CREATE INDEX IF NOT EXISTS ix_objects_place ON objects(place_id);

-- Personas que aparecen en fotos o charlas. La clave es el nombre normalizado (sin acentos, minúsculas).
CREATE TABLE IF NOT EXISTS people (
  id      INTEGER PRIMARY KEY,
  nombre  TEXT NOT NULL,                                   -- como se escribe: "Persona D"
  clave   TEXT NOT NULL UNIQUE,                            -- "persona d"
  notas   TEXT NOT NULL DEFAULT '',
  instagram TEXT NOT NULL DEFAULT ''                       -- solo el usuario: "personaf"
);

-- Fotos (Drive o local). Una foto pertenece a un evento y muestra a varias personas.
CREATE TABLE IF NOT EXISTS photos (
  id        INTEGER PRIMARY KEY,
  event_id  INTEGER REFERENCES events(id) ON DELETE SET NULL,
  fecha     TEXT    NOT NULL CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]*'),
  archivo   TEXT    NOT NULL UNIQUE,                       -- nombre del fichero original (sirve de clave)
  fuente    TEXT    NOT NULL DEFAULT 'drive' CHECK (fuente IN ('drive', 'iphone', 'otra')),
  notas     TEXT    NOT NULL DEFAULT '',
  trip_id   INTEGER REFERENCES trips(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_photos_event ON photos(event_id);

CREATE TABLE IF NOT EXISTS photo_people (
  photo_id  INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
  PRIMARY KEY (photo_id, person_id)
);
CREATE INDEX IF NOT EXISTS ix_pp_person ON photo_people(person_id);

-- Charlas grabadas: keynote, mesa redonda, pitch... Se enlazan con su evento y, opcionalmente, con su lanyard.
CREATE TABLE IF NOT EXISTS talks (
  id            INTEGER PRIMARY KEY,
  event_id      INTEGER NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  tipo          TEXT    NOT NULL CHECK (tipo IN ('keynote', 'mesa_redonda', 'pitch', 'otro')),
  titulo        TEXT    NOT NULL DEFAULT '',
  fecha         TEXT    NOT NULL DEFAULT '',
  duracion_s    INTEGER CHECK (duracion_s IS NULL OR duracion_s >= 0),
  idioma        TEXT    NOT NULL DEFAULT '',
  url           TEXT    NOT NULL DEFAULT '',               -- YouTube no listado o Drive (no se guarda el vídeo)
  archivo_local TEXT    NOT NULL DEFAULT '',               -- ruta en el ordenador, si existe
  transcripcion TEXT    NOT NULL DEFAULT '',               -- ruta a .txt o .srt (opcional)
  notas         TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_talks_event ON talks(event_id);

-- Personas que participan en una charla (moderadora, panelistas...)
CREATE TABLE IF NOT EXISTS talk_people (
  talk_id   INTEGER NOT NULL REFERENCES talks(id) ON DELETE CASCADE,
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
  papel     TEXT    NOT NULL DEFAULT 'panelista',
  PRIMARY KEY (talk_id, person_id)
);

-- Control de importaciones: evita duplicar al repetir una importación.
CREATE TABLE IF NOT EXISTS imports (
  clave        TEXT PRIMARY KEY,                           -- hash o identificador de la fuente
  origen       TEXT NOT NULL,
  importado_utc TEXT NOT NULL
);

-- Seguimiento: todo calculado. Lo futuro no cuenta hasta que llega (como en el Excel).
CREATE VIEW IF NOT EXISTS v_viajes AS
  SELECT id, slug, nombre, inicio, fin,
         CAST(julianday(fin) - julianday(inicio) + 1 AS INTEGER) AS dias,
         substr(inicio, 1, 4) AS anio,
         CASE WHEN inicio IS NULL THEN 'sin fecha' WHEN inicio > date('now') THEN 'futuro' ELSE 'pasado' END AS estado
  FROM trips;

CREATE VIEW IF NOT EXISTS v_ciudades AS
  SELECT p.id, p.nombre, p.pais, p.continente, MIN(v.inicio) AS primera_visita, COUNT(v.id) AS visitas
  FROM places p JOIN visits v ON v.place_id = p.id
  WHERE v.inicio IS NULL OR v.inicio <= date('now')
  GROUP BY p.id;


CREATE VIEW IF NOT EXISTS v_aeropuertos AS
  SELECT a.iata, a.nombre, COUNT(t.id) AS veces
  FROM airports a JOIN trips t ON a.iata IN (t.salida, t.llegada, t.escala)
  WHERE t.inicio IS NULL OR t.inicio <= date('now')
  GROUP BY a.iata;

-- País contado si tiene ciudades visitadas o un aeropuerto usado (Catar por la escala en Doha), como el Excel.
CREATE VIEW IF NOT EXISTS v_paises AS
  SELECT pais, continente, SUM(ciudad) AS ciudades, SUM(aeropuerto) AS aeropuertos FROM (
    SELECT pais, continente, 1 AS ciudad, 0 AS aeropuerto FROM v_ciudades
    UNION ALL
    SELECT p.pais, p.continente, 0, 1 FROM v_aeropuertos va JOIN airports a ON a.iata = va.iata JOIN places p ON p.id = a.place_id
  ) GROUP BY pais;

CREATE VIEW IF NOT EXISTS v_continentes AS
  SELECT continente, COUNT(*) AS paises, SUM(ciudades) AS ciudades FROM v_paises GROUP BY continente;

PRAGMA user_version = 4;
