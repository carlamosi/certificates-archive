-- Migración v1 -> v2: viajes, visitas, lugares, aeropuertos, sellos y objetos sin evento.
-- La ejecuta `archivo.py migrar` (copia previa, foreign_keys OFF, una transacción, foreign_key_check antes de confirmar).
-- schema.sql debe dar la misma estructura (lo comprueba tests/test_archivo_db.py).

CREATE TABLE places (
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

CREATE TABLE airports (
  iata     TEXT PRIMARY KEY CHECK (length(iata) = 3),
  nombre   TEXT NOT NULL DEFAULT '',
  place_id INTEGER REFERENCES places(id) ON DELETE SET NULL,
  lat      REAL,
  lng      REAL
);

CREATE TABLE trips (
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
  notas      TEXT NOT NULL DEFAULT ''
);

-- Una visita = una ciudad en unas fechas, dentro de un viaje o suelta (p. ej. Andorra 2021).
CREATE TABLE visits (
  id       INTEGER PRIMARY KEY,
  place_id INTEGER NOT NULL REFERENCES places(id) ON DELETE RESTRICT,
  trip_id  INTEGER REFERENCES trips(id) ON DELETE SET NULL,
  inicio   TEXT,
  fin      TEXT,
  nota     TEXT NOT NULL DEFAULT '',
  UNIQUE (place_id, trip_id, inicio)
);
CREATE INDEX ix_visits_trip ON visits(trip_id);

ALTER TABLE events ADD COLUMN place_id INTEGER REFERENCES places(id) ON DELETE SET NULL;
ALTER TABLE events ADD COLUMN trip_id  INTEGER REFERENCES trips(id) ON DELETE SET NULL;
ALTER TABLE photos ADD COLUMN trip_id  INTEGER REFERENCES trips(id) ON DELETE SET NULL;

-- pin_city pasa a ser un lugar (sin país: se completa al importar los viajes)
INSERT OR IGNORE INTO places (nombre, pais) SELECT DISTINCT pin_city, '' FROM objects WHERE pin_city <> '';

CREATE TABLE objects_new (
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
INSERT INTO objects_new (id, uid, event_id, place_id, tipo, rol, premio, num_archivo, caja_fisica, pin_id,
                         ancho_mm, alto_mm, forma, agujero_mm, anclaje_x, anclaje_y, front_web, back_web, avisos, created_utc)
  SELECT o.id, o.uid, o.event_id, (SELECT p.id FROM places p WHERE p.nombre = o.pin_city AND p.pais = ''),
         o.tipo, o.rol, o.premio, o.num_archivo, o.caja_fisica, o.pin_id,
         o.ancho_mm, o.alto_mm, o.forma, o.agujero_mm, o.anclaje_x, o.anclaje_y, o.front_web, o.back_web, o.avisos, o.created_utc
  FROM objects o;
DROP TABLE objects;
ALTER TABLE objects_new RENAME TO objects;
CREATE INDEX ix_objects_event ON objects(event_id);
CREATE INDEX ix_objects_tipo  ON objects(tipo);
CREATE INDEX ix_objects_trip  ON objects(trip_id);
CREATE INDEX ix_objects_place ON objects(place_id);

-- Seguimiento: todo calculado. Lo futuro no cuenta hasta que llega (como en el Excel).
CREATE VIEW v_viajes AS
  SELECT id, slug, nombre, inicio, fin,
         CAST(julianday(fin) - julianday(inicio) + 1 AS INTEGER) AS dias,
         substr(inicio, 1, 4) AS anio,
         CASE WHEN inicio IS NULL THEN 'sin fecha' WHEN inicio > date('now') THEN 'futuro' ELSE 'pasado' END AS estado
  FROM trips;

CREATE VIEW v_ciudades AS
  SELECT p.id, p.nombre, p.pais, p.continente, MIN(v.inicio) AS primera_visita, COUNT(v.id) AS visitas
  FROM places p JOIN visits v ON v.place_id = p.id
  WHERE v.inicio IS NULL OR v.inicio <= date('now')
  GROUP BY p.id;


CREATE VIEW v_aeropuertos AS
  SELECT a.iata, a.nombre, COUNT(t.id) AS veces
  FROM airports a JOIN trips t ON a.iata IN (t.salida, t.llegada, t.escala)
  WHERE t.inicio IS NULL OR t.inicio <= date('now')
  GROUP BY a.iata;

-- País contado si tiene ciudades visitadas o un aeropuerto usado (Catar por la escala en Doha), como el Excel.
CREATE VIEW v_paises AS
  SELECT pais, continente, SUM(ciudad) AS ciudades, SUM(aeropuerto) AS aeropuertos FROM (
    SELECT pais, continente, 1 AS ciudad, 0 AS aeropuerto FROM v_ciudades
    UNION ALL
    SELECT p.pais, p.continente, 0, 1 FROM v_aeropuertos va JOIN airports a ON a.iata = va.iata JOIN places p ON p.id = a.place_id
  ) GROUP BY pais;

CREATE VIEW v_continentes AS
  SELECT continente, COUNT(*) AS paises, SUM(ciudades) AS ciudades FROM v_paises GROUP BY continente;

PRAGMA user_version = 2;
