# Arquitectura

Tres piezas locales, sin servidor ni nube. Los datos entran por la izquierda y la web solo lee ficheros estáticos.

```
 FOTOS / ESCANEOS                 HERRAMIENTAS (Python)                       WEB (estática)
 ─────────────────                ─────────────────────                       ──────────────
 lanyards y pines   ──►  lanyard_archive.py  ──►  Lanyards_procesados/
 (plantilla ArUco)       (calibra, recorta, mide)   archive.json + WebP
                                         │                 │
                                         │                 └──► web/sync.py ──► web/data/archive.json ──► pared 3D (app.js)
                                         ▼                                       web/img/web/*.webp
 gente.zip + texto  ──►  archivo.py importar-objetos / -fotos / -catalogo / -viajes / -charlas
 catálogo CSV                    │
 mis_viajes.xlsx                 ▼
 certificados PDF        datos/archivo.sqlite  (FUENTE DE VERDAD, esquema v2)
                                 │   └─ datos/copias/ (archivo.py copia)
                                 ▼
                         archivo.py exportar ──► web/data/archivo.json ──► (pendiente) mapa, personas, línea del tiempo
                         importar-catalogo   ──► web/img/certificados/*.jpg
```

## Piezas
| Pieza | Responsabilidad | Entrada | Salida |
|---|---|---|---|
| `herramientas/lanyard_archive/` | Digitalizar lanyards y pines con medidas reales | Fotos sobre la plantilla A4 v3 | `Lanyards_procesados/` (`archive.json`, `web/`, `master/`, `originals/`) |
| `herramientas/archivo_db/` | Base de datos única del archivo; importadores idempotentes; exportación | `archive.json`, CSV, Excel, zips, textos | `datos/archivo.sqlite`, `web/data/archivo.json`, imágenes de certificados |
| `web/` | Museo personal (privado) | `data/archive.json` hoy; `data/archivo.json` cuando se conecte | Páginas estáticas servidas con `python -m http.server` |

## Contratos entre piezas
- **`archive.json`** (herramienta → web y base): formato descrito en `docs/DECISIONES.md`. Si cambia, se actualizan `sync.py`, `web/app.js` y `archivo.py importar-objetos` en el mismo cambio.
- **`archivo.json`** (base → web): lo genera `archivo.py exportar`. Es la única puerta de la base hacia la web: la web nunca lee SQLite.
- **Rutas de imágenes**: relativas a `web/` (`img/web/…`, `img/certificados/…`).

## Principios
- **Local y privado**: originales, base, copias, certificados y vídeos fuera de git (`.gitignore`).
- **Idempotencia**: repetir cualquier importación no duplica nada (claves naturales: `uid`, `slug`, `clave`, `archivo`, `iata`).
- **Calculado, no guardado**: totales y estados (días, países, pasado/futuro) son vistas SQL.
- **Portabilidad**: la base puede migrar a Supabase/Postgres (`docs/MIGRACION_SUPABASE.md`).
