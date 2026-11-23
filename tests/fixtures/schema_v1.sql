-- Certificates Archive · esquema SQLite (v1)
-- Fechas: texto ISO. Se admite AAAA, AAAA-MM o AAAA-MM-DD (cuando no se sabe el día).
-- Ninguna tabla guarda datos sensibles (salud, religión, orientación, etc.).

PRAGMA foreign_keys = ON;

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
  notas        TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_events_fecha ON events(fecha);

-- Objetos físicos o digitales asociados a un evento: lanyards, certificados, pines, fotos de equipo...
CREATE TABLE IF NOT EXISTS objects (
  id           INTEGER PRIMARY KEY,
  uid          TEXT    NOT NULL UNIQUE,                    -- id estable (mismo que archive.json)
  event_id     INTEGER NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
  tipo         TEXT    NOT NULL CHECK (tipo IN ('lanyard', 'certificado', 'pin', 'foto', 'otro')),
  rol          TEXT    NOT NULL DEFAULT '',                -- Speaker, Ponente, Participante...
  premio       TEXT    NOT NULL DEFAULT '',                -- 1st Prize, Top 10, Finalista...
  num_archivo  TEXT    NOT NULL DEFAULT '',                -- número en el Certificates Archive físico
  caja_fisica  TEXT    NOT NULL DEFAULT '',                -- caja / página
  pin_city     TEXT    NOT NULL DEFAULT '',                -- solo pines: ciudad del pin
  pin_id       TEXT    NOT NULL DEFAULT '',
  ancho_mm     REAL,
  alto_mm      REAL,
  forma        TEXT    NOT NULL DEFAULT '' CHECK (forma IN ('', 'rectangular', 'libre')),
  agujero_mm   TEXT    NOT NULL DEFAULT '',                -- diámetros separados por ;
  anclaje_x    REAL,
  anclaje_y    REAL,
  front_web    TEXT    NOT NULL DEFAULT '',
  back_web     TEXT    NOT NULL DEFAULT '',
  avisos       TEXT    NOT NULL DEFAULT '',
  created_utc  TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_objects_event ON objects(event_id);
CREATE INDEX IF NOT EXISTS ix_objects_tipo ON objects(tipo);

-- Personas que aparecen en fotos o charlas. La clave es el nombre normalizado (sin acentos, minúsculas).
CREATE TABLE IF NOT EXISTS people (
  id      INTEGER PRIMARY KEY,
  nombre  TEXT NOT NULL,                                   -- como se escribe: "Persona D"
  clave   TEXT NOT NULL UNIQUE,                            -- "persona d"
  notas   TEXT NOT NULL DEFAULT ''
);

-- Fotos (Drive o local). Una foto pertenece a un evento y muestra a varias personas.
CREATE TABLE IF NOT EXISTS photos (
  id        INTEGER PRIMARY KEY,
  event_id  INTEGER REFERENCES events(id) ON DELETE SET NULL,
  fecha     TEXT    NOT NULL CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]*'),
  archivo   TEXT    NOT NULL UNIQUE,                       -- nombre del fichero original (sirve de clave)
  fuente    TEXT    NOT NULL DEFAULT 'drive' CHECK (fuente IN ('drive', 'iphone', 'otra')),
  notas     TEXT    NOT NULL DEFAULT ''
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

PRAGMA user_version = 1;
