# Migración futura a Supabase (Postgres)

Hoy la base es SQLite local (`datos/archivo.sqlite`) y **no hay que migrar**. Esta guía existe para que, si algún día
hace falta (web con login, sincronizar varios dispositivos), el paso sea mecánico y sin pérdidas.

## Por qué la base ya está preparada
- **Claves naturales estables** en todas las tablas: `events.slug`, `objects.uid`, `trips.slug`, `people.clave`,
  `photos.archivo`, `airports.iata`, `places (nombre, pais)`. Permiten importar con *upsert* (`ON CONFLICT DO NOTHING`)
  y repetir la carga sin duplicar, igual que hoy.
- **Fechas en texto ISO** (`AAAA`, `AAAA-MM` o `AAAA-MM-DD`): se copian tal cual a `text`.
- **Totales como vistas**, no como datos: no hay nada que recalcular al migrar.
- **Ficheros fuera de la base:** imágenes y vídeos son rutas. Las imágenes irían a un bucket privado de Storage; los originales y vídeos no se suben.

## Qué cambia al traducir el esquema (`schema.sql`)
| SQLite | Postgres / Supabase |
|---|---|
| `INTEGER PRIMARY KEY` | `bigint generated always as identity primary key` |
| `REAL` | `double precision` |
| `CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]*')` | `CHECK (fecha ~ '^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$')` |
| `julianday(fin) - julianday(inicio) + 1` | `fin::date - inicio::date + 1` (solo si la fecha es completa) |
| `date('now')` | `current_date::text` |
| `substr(inicio, 1, 4)` | `left(inicio, 4)` |
| `INSERT OR IGNORE` | `INSERT ... ON CONFLICT DO NOTHING` |
| `PRAGMA user_version` | tabla de migraciones de Supabase (`supabase/migrations/`) |
| `PRAGMA foreign_keys = ON` | siempre activo en Postgres |

## Pasos (cuando toque)
0. Instalar entonces la skill oficial `postgres-best-practices` (github.com/supabase/agent-skills) y usar el MCP de Supabase que ya está instalado.
1. `python herramientas/archivo_db/archivo.py copia`.
2. Traducir `schema.sql` con la tabla de arriba a `supabase/migrations/0001_archivo.sql`; activar **RLS en todas las tablas** con una sola política: solo la dueña (su `auth.uid()`) lee y escribe. Los datos son personales.
3. Exportar cada tabla a CSV (respetando el orden de las claves foráneas: places, airports, trips, visits, events, people, objects, photos, photo_people, talks, talk_people, imports) y cargar con `\copy`.
4. Comprobar: mismos recuentos por tabla que `archivo.py resumen`, y las vistas devuelven los mismos totales.
5. Las imágenes de `web/img/certificados/` a un bucket **privado**; `front_web` pasa a ser la ruta del bucket.

## Regla para no romper la portabilidad
No usar funciones exclusivas de SQLite nuevas (JSON1, FTS5, `WITHOUT ROWID`, triggers con `RAISE`) sin anotarlas en la tabla de arriba.
