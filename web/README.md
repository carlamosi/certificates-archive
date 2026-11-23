# Certificates Archive · web

Web estática (HTML + CSS + JS) con la pared de lanyards en 3D (Three.js).

## Ver la web
Hay que servir la carpeta (el navegador bloquea las imágenes y el JSON si abres el HTML directamente):

    python -m http.server 8000

y abre http://localhost:8000

## Actualizar con lanyards nuevos
1. Procesa las fotos con Lanyard Archive → carpeta `Lanyards_procesados`.
2. Sincroniza:

       python sync.py "ruta/a/Lanyards_procesados"

   Copia `archive.json` a `data/` y las WebP a `img/web/` (borra antes las imágenes de la sincronización anterior).

## Controles
- Pasar el cursor sobre un lanyard: se balancea y aparece su cartela.
- Clic: gira la tarjeta para ver el reverso.
- Enter (con el cursor encima) o "Ver ficha": ficha con anverso, reverso y datos.
- En la ficha: ← → para navegar, Esc para cerrar.
- Filtro por año arriba a la derecha.

## Estructura
    index.html        estructura y marcado
    style.css         estética (cristal iOS + serif de museo, modo oscuro automático)
    app.js            escena 3D, balanceo, filtro, ficha
    sync.py           copia datos e imágenes desde Lanyard Archive
    data/archive.json datos que lee la web
    img/web/          imágenes WebP con transparencia

Los datos de demostración (6 lanyards inventados) están en `data/` y `img/web/`.
Para empezar de cero, borra `data/archive.json` y `img/web/` antes de sincronizar.
