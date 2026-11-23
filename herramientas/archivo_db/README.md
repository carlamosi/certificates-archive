# archivo_db · base de datos del archivo

SQLite (`datos/archivo.sqlite`), **fuente de verdad** del archivo (esquema v4). Esquema en `schema.sql`; pasos v1→v2 y v2→v3 y v3→v4 en `migraciones/002.sql`, `003.sql` y `004.sql`.

- **Dos ejes:** eventos y viajes (también familiares). Un viaje tiene visitas (ciudad + fechas) a lugares con coordenadas.
- **Objetos** (lanyards, certificados, pines, sellos LEGO): cuelgan de un evento, un viaje, un lugar o solo de su título (certificado suelto).
- **Fotos:** de un evento, de un viaje o sueltas; con personas. **Charlas:** de un evento, con personas.
- **Seguimiento calculado** (vistas): `v_viajes` (días, año, pasado/futuro), `v_ciudades`, `v_paises`, `v_continentes`, `v_aeropuertos`.

## Comandos
    pip install -r requirements.txt                         # openpyxl y pymupdf (una vez)
    python archivo.py init                                  # crea la base de datos (una vez)
    python archivo.py migrar                                # a la última versión, v4 (hace copia antes)
    python archivo.py copia                                 # copia de seguridad en datos/copias/
    python archivo.py importar-viajes datos/mis_viajes.xlsx # viajes, visitas, lugares, aeropuertos y pines
    python archivo.py viaje --nombre "Premios (París)" --inicio 2026-12-03 --fin 2026-12-04 --transporte Avión --salida BCN --llegada ORY --ciudad París
    python archivo.py viaje --slug SLUG --nombre "Nombre nuevo" [--km 1200]   # cambia solo lo que pasas
    python archivo.py pin --viaje SLUG --titulo "El Principito" --ciudad París
    python archivo.py lugar --nombre "Planes de Son" --renombrar "MónNatura Pirineus" --lat 42.6181 --lng 1.0802   # coordenadas de Nominatim (OSM)
    python archivo.py pulir                                 # arreglos automáticos; se puede repetir
    python archivo.py sello --fecha 2026-08-25 --sitio "LEGO Store Tivoli" --ciudad Copenhague [--pais Dinamarca] [--viaje SLUG] [--imagen RUTA]
    python archivo.py importar-objetos ruta/archive.json    # lanyards procesados
    python archivo.py importar-catalogo ../../datos/certificates_archive_v1.csv   # columnas opcionales `evento` (slug; vacía = suelto) y `archivo` (fichero en datos/certificados_originales -> JPG en web/img/certificados)
    python archivo.py evento --nombre "..." --fecha 2026-07-12 [--organizador --lugar --ciudad] [--viaje SLUG]
    python archivo.py importar-fotos datos/entrada/fotos_personas.txt --zip datos/entrada/gente.zip
    python archivo.py importar-charlas datos/entrada/charlas.txt        # vídeos grabados con el móvil (ruta local)
    python archivo.py charla --slug <slug> --tipo keynote --titulo "..." --archivo /ruta/video.mov --personas "Nombre"
    python archivo.py resumen                               # recuento, avisos, integridad
    python archivo.py exportar ../../web/data/archivo.json  # para la web

## Propiedades importantes
- Todas las importaciones son **idempotentes**: repetirlas no duplica nada.
- Las personas se comparan por **nombre normalizado** (sin acentos, minúsculas). Si dos nombres se parecen mucho
  ("Minguela" / "Minguella"), `resumen` y la importación lo avisan; **no se fusionan solas**.
- Las claves foráneas están activas; `resumen` comprueba la integridad.
- Variables `ARCHIVO_DB`, `ARCHIVO_FOTOS` y `ARCHIVO_FOTOS_WEB` para usar otra base, otra carpeta de originales y otra de WebP (pruebas).
- `archivo.py foto --archivo F --nota T` guarda el pie de una foto (F: nombre del fichero o una parte que no se repita); `archivo.py persona --nombre N --instagram U` guarda el Instagram de una persona.
- `archivo.py fotos-web` crea en `web/img/fotos/` el WebP (1600 px) y la miniatura de cada foto; después `exportar` añade sus rutas a `archivo.json`.

## Formato de fotos con personas
Ver `datos/fotos_personas_EJEMPLO.txt`.

## Charlas (vídeos del móvil)
No tienen URL: se guarda la **ruta local** del vídeo (`archivo_local`). Formato en `datos/entrada/charlas_EJEMPLO.txt`:
`slug | tipo | título | fecha | duración_s | idioma | ruta_video | personas`.
La duración se puede dejar vacía. Repetir la línea no duplica la charla.

## Fotos desde gente.zip
- Las imágenes se extraen a `datos/fotos_originales/` (no van a git).
- Si una línea tiene `=> archivo`, se busca ese nombre en el zip; si falta, se avisa.
- Si la fecha EXIF de la foto no coincide con la del texto, se avisa (no se corrige sola).
