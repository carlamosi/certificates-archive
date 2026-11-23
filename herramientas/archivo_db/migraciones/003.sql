-- Migración v2 -> v3: km manuales por viaje (si está vacío, archivo.py los calcula por círculo máximo).
-- La ejecuta `archivo.py migrar`. schema.sql debe dar la misma estructura (lo comprueba tests/test_archivo_db.py).

ALTER TABLE trips ADD COLUMN km_manual REAL CHECK (km_manual IS NULL OR km_manual >= 0);

PRAGMA user_version = 3;
