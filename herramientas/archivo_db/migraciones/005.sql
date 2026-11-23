-- Migración v4 -> v5: categoría común de cada objeto (Ciencia y tecnología, Divulgación, Emprendimiento, Impacto social).
-- La rellena `archivo.py importar-catalogo` desde la columna categoria_propuesta. schema.sql debe dar la misma estructura.

ALTER TABLE objects ADD COLUMN categoria TEXT NOT NULL DEFAULT '';

PRAGMA user_version = 5;
