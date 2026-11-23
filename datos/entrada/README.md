# Entrada para importar

Pon aquí los ficheros que vas a importar. Esta carpeta NO va a git.

- `gente.zip`: las fotos con personas (JPG o HEIC) del Drive, en un único zip.
- `fotos_personas.txt`: el texto con el formato de `datos/fotos_personas_EJEMPLO.txt`.
  Cada línea de foto puede terminar en `=> nombre_del_fichero.heic` para enlazar la imagen del zip.
- `certificates.zip`: los certificados escaneados (ya extraídos en `datos/certificados_originales/`).
- `charlas.txt`: una línea por vídeo grabado (formato en `charlas_EJEMPLO.txt`).

Comandos:

    python herramientas/archivo_db/archivo.py importar-fotos datos/entrada/fotos_personas.txt --zip datos/entrada/gente.zip
    python herramientas/archivo_db/archivo.py importar-charlas datos/entrada/charlas.txt
    python herramientas/archivo_db/archivo.py resumen
