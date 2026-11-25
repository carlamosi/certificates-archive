# PWA instalable (iPhone) y splash
Estado: Verificada (escritorio, Chrome) · pendiente probar en el iPhone · Fecha: 2026-11-25

## Para qué
Abrir la web desde un icono en el iPhone 12 mini, a pantalla completa, con una bienvenida (el sello que se estampa) y funcionando sin red tras una visita.

## Alcance
- Entra: manifest, iconos, imagen de arranque iOS (claro/oscuro), service worker, splash.
- No entra: notificaciones, sincronización en segundo plano, caché de vídeos y de los mapas/librerías de CDN (mapa sin red no carga d3 ni teselas).

## Piezas
- `herramientas/generar_iconos_pwa.py` → `web/img/app/` (dibuja el sello con Pillow; se relanza si cambia el logo).
- `web/manifest.webmanifest`, bloque PWA en el `<head>` de cada `web/*.html`.
- `web/sw.js`: precachea html/css/js/`data/archivo.json`; red primero (cae a caché sin red); imágenes cache-primero; vídeos y CDN directos. Subir `VERSION` para invalidar.
- `web/splash.js` + `splash.css`: splash una vez por sesión y registro del SW (único sitio). Con `prefers-reduced-motion`, solo opacidad.
- `preparar_vercel.py`: cabeceras (`sw.js` sin caché, manifest, `img/` y `video/` caché larga).

## Instalar en el iPhone
Safari → abrir la web publicada → Compartir → «Añadir a pantalla de inicio» → Añadir. Se abre desde el icono «Archivo».

## Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Splash una vez por sesión, sin errores de consola | Chrome: sí |
| 2 | SW activo y páginas + datos sin red tras una visita | Chrome: sí |
| 3 | Barra superior bajo el notch en modo app | `env(safe-area-inset-top)` ya en `.bar`; **sin probar en iPhone** |
| 4 | Imagen de arranque iOS | **sin probar en iPhone** (iOS exige 1125×2436 para 375×812 @3x) |
