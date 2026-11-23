-- Migración v3 -> v4: usuario de Instagram de cada persona (solo el usuario, sin URL; vacío si no se sabe).
-- La ejecuta `archivo.py migrar`. schema.sql debe dar la misma estructura (lo comprueba tests/test_archivo_db.py).

ALTER TABLE people ADD COLUMN instagram TEXT NOT NULL DEFAULT '';

PRAGMA user_version = 4;
